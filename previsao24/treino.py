"""Treino causal por MSE de validação, preservando épocas e recarga exata."""
import os
import random
import time
import numpy as np
import torch
from .arquivos import agora,salvar_json
from .metricas import calcular
from .redes import criar

def fixar_seed(seed):
    os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark=False
    torch.backends.cudnn.deterministic=True
    torch.backends.cuda.matmul.allow_tf32=False
    torch.backends.cudnn.allow_tf32=False
    torch.use_deterministic_algorithms(True,warn_only=True)
    torch.set_num_threads(2)

def janelas(matriz,indices,w):
    deslocamentos=torch.arange(1-w,1,device=matriz.device)
    return matriz[indices[:,None]+deslocamentos[None,:]].unsqueeze(-1)

def prever(rede,matriz,indices,w,escalas,batch=64):
    rede.eval()
    valores=[]
    with torch.inference_mode():
        for a in range(0,len(indices),batch):
            y=rede(janelas(matriz,indices[a:a+batch],w))
            if not torch.isfinite(y).all():
                raise ValueError('Previsão não finita.')
            valores.append(y.cpu().numpy().astype(np.float64)*escalas['escala_alvo']+escalas['media_alvo'])
    return np.concatenate(valores) if valores else np.empty(0)

def treinar(c,celula,matriz,blocos,escalas,destino):
    nome=celula['modelo']
    fixar_seed(celula['seed'])
    if not torch.cuda.is_available() or c['dispositivo']!='cuda':
        raise RuntimeError('CUDA obrigatório; sem fallback.')
    dispositivo=torch.device('cuda')
    destino.mkdir(parents=True,exist_ok=True)
    inicio=time.perf_counter()
    matriz_gpu=torch.as_tensor(matriz,device=dispositivo)
    indices={b:torch.as_tensor(q['indice_hora'].to_numpy(np.int64),device=dispositivo) for b,q in blocos.items()}
    # Verificação explícita de todas as janelas, incluindo origens operacionais.
    for b,q in blocos.items():
        for i in q['indice_hora'].to_numpy(np.int64):
            if i<celula['contexto']-1 or not np.isfinite(matriz[i-celula['contexto']+1:i+1]).all():
                raise ValueError(f'Janela inválida: {b}/{i}')
    alvos=torch.as_tensor(((blocos['treino']['alvo'].to_numpy()-escalas['media_alvo'])/escalas['escala_alvo']).astype(np.float32),device=dispositivo)
    rede=criar(nome,c).to(dispositivo)
    t=c['treino']
    otimizador=torch.optim.AdamW(rede.parameters(),lr=t['taxa_aprendizado'],weight_decay=t['weight_decay'],betas=(.9,.999),eps=1e-8)
    gerador=torch.Generator().manual_seed(celula['seed'])
    melhor=float('inf')
    espera=0
    historico=[]
    torch.cuda.reset_peak_memory_stats()
    for epoca in range(1,t['epocas']+1):
        rede.train()
        permutacao=torch.randperm(len(alvos),generator=gerador).to(dispositivo)
        soma=0.0
        for a in range(0,len(alvos),t['batch']):
            lote=permutacao[a:a+t['batch']]
            otimizador.zero_grad(set_to_none=True)
            for j in range(0,len(lote),t['microbatch']):
                sub=lote[j:j+t['microbatch']]
                y=rede(janelas(matriz_gpu,indices['treino'][sub],celula['contexto']))
                perda=torch.nn.functional.mse_loss(y,alvos[sub],reduction='sum')
                if not torch.isfinite(perda):
                    raise ValueError('Perda não finita.')
                (perda/len(lote)).backward()
                soma+=float(perda.detach().cpu())
            torch.nn.utils.clip_grad_norm_(rede.parameters(),t['clipping'],error_if_nonfinite=True)
            otimizador.step()
        p=prever(rede,matriz_gpu,indices['validacao'],celula['contexto'],escalas,t['batch'])
        mse=float(np.mean((p-blocos['validacao']['alvo'].to_numpy())**2))
        melhorou=mse<melhor
        if melhorou:
            melhor=mse
            espera=0
            parcial=destino/'checkpoint.parcial'
            torch.save({'pesos':rede.state_dict(),'epoca':epoca,'mse_validacao':mse,'configuracao':c,'celula':celula,'escalas':escalas},parcial)
            parcial.replace(destino/'checkpoint.pt')
        else:
            espera+=1
        historico.append({'epoca':epoca,'mse_treino_padronizado':soma/len(alvos),'mse_validacao':mse,'melhorou':melhorou,'utc':agora(),'segundos':time.perf_counter()-inicio})
        salvar_json(destino/'epocas.json',historico)
        print(f"{nome} {celula} época={epoca} mse_val={mse:.9f} espera={espera}",flush=True)
        if espera>=t['paciencia']:
            break
    checkpoint=torch.load(destino/'checkpoint.pt',map_location=dispositivo,weights_only=True)
    rede.load_state_dict(checkpoint['pesos'])
    metricas={}
    previsoes={}
    for b in ('validacao','teste','operacional'):
        q=blocos[b][['origem_utc','destino_utc','indice_hora','close','preco_destino','alvo']].copy()
        q['previsao']=prever(rede,matriz_gpu,indices[b],celula['contexto'],escalas,t['batch'])
        q.to_parquet(destino/f'previsoes_{b}.parquet',index=False)
        previsoes[b]=q['previsao'].to_numpy()
        if b!='operacional':
            metricas[b]=calcular(q['alvo'],q['previsao'])
    recarga=criar(nome,c).to(dispositivo)
    recarga.load_state_dict(torch.load(destino/'checkpoint.pt',map_location=dispositivo,weights_only=True)['pesos'])
    for b in ('validacao','teste','operacional'):
        refeito=prever(recarga,matriz_gpu,indices[b],celula['contexto'],escalas,t['batch'])
        if not np.array_equal(refeito,previsoes[b]):
            raise ValueError(f'Recarga não exata em {b}.')
    resultado={'modelo':nome,'epoca_selecionada':checkpoint['epoca'],'epocas_executadas':len(historico),'metricas':metricas,
               'parametros':sum(p.numel() for p in rede.parameters()),'segundos':time.perf_counter()-inicio,
               'memoria_cuda_maxima_bytes':torch.cuda.max_memory_allocated(),'recarga_exata':True}
    salvar_json(destino/'resultado.json',resultado)
    del rede,recarga,otimizador,matriz_gpu,indices,alvos
    torch.cuda.empty_cache()
    return resultado
