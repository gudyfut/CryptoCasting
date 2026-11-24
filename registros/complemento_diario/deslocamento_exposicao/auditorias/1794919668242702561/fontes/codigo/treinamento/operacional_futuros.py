"""Ajuste CUDA de um contrato operacional, seleção exclusivamente em V."""
import math
import time
from pathlib import Path
import numpy as np
import torch
from infraestrutura.artefatos import salvar_json, sha256, agora, identidade
from modelos.mamba_operacional import EspecificacaoOperacional, RedeMambaOperacional
from treinamento.otimizacao import fixar_seed, criar_otimizador


def construir(dados,receita):
    saidas=('log_retorno_24h',) if receita['familia_alvo']=='terminal' else ('payoff_compra','payoff_venda')
    esp=EspecificacaoOperacional(identidade(receita),dados.canais,dados.contexto,saidas)
    return RedeMambaOperacional(esp,{'largura':32,'estado':receita['d_state'],'camadas':2,
                                   'convolucao':4,'expansao':2,'dropout':.1}).cuda()


def metricas(y,p):
    y,p=np.asarray(y,float),np.asarray(p,float)
    if y.ndim!=2 or y.shape!=p.shape or not np.isfinite(y).all() or not np.isfinite(p).all():
        raise ValueError('Métricas exigem alvos e previsões [N,K] idênticos e finitos.')
    erro=p-y; mse=float(np.mean(erro**2))
    return {'n':len(y),'canais':y.shape[1],'mse':mse,'rmse':math.sqrt(mse),
        'mae':float(np.abs(erro).mean()),'mse_zero':float(np.mean(y**2)),
        'vies_por_canal':erro.mean(axis=0).tolist(),'mse_por_canal':np.mean(erro**2,axis=0).tolist(),
        'acerto_sinal_por_canal':np.mean(np.sign(y)==np.sign(p),axis=0).tolist()}


def atualizar(rede,opt,x,y,perda,microbatch=32):
    if y.ndim!=2 or len(x)!=len(y) or not len(x):
        raise ValueError('Lote inválido.')
    if perda not in ['mse','huber']: raise ValueError('Perda inválida.')
    opt.zero_grad(set_to_none=True); total=0.
    for i in range(0,len(x),microbatch):
        p=rede(x[i:i+microbatch]);real=y[i:i+microbatch]
        if p.shape!=real.shape: raise ValueError('Broadcasting proibido.')
        v=(torch.nn.functional.mse_loss(p,real,reduction='sum') if perda=='mse'
           else 2*torch.nn.functional.huber_loss(p,real,reduction='sum',delta=1.))
        if not torch.isfinite(v): raise ValueError('Perda não finita.')
        # Média de elementos, não apenas batch: P0 tem duas saídas.
        (v/y.numel()).backward(); total+=float(v.detach())
    norma=float(torch.nn.utils.clip_grad_norm_(rede.parameters(),1.,error_if_nonfinite=True))
    opt.step()
    return total/y.numel(),norma


def prever(rede,dados,ids):
    rede.eval(); partes=[]
    with torch.inference_mode():
        for i in range(0,len(ids),64):
            x=torch.as_tensor(dados.janelas(ids[i:i+64]),device='cuda')
            partes.append(rede(x).cpu().numpy())
    return dados.decodificar(np.concatenate(partes))


def ajustar(dados,receita,seed,destino,vinculo,limite_segundos=2700,epocas=100,paciencia=10):
    destino=Path(destino);destino.mkdir(parents=True,exist_ok=False)
    (destino/'checkpoints').mkdir()
    salvar_json(destino/'inicio.json',{'utc':agora(),'seed':seed,'receita':receita,'vinculo':vinculo,
        'limite_segundos':limite_segundos,'epocas':epocas,'paciencia':paciencia})
    salvar_json(destino/'escalas.json',dados.escalas)
    fixar_seed(seed);rede=construir(dados,receita)
    opt,grupos=criar_otimizador(rede,{'weight_decay':.001,'taxa_aprendizado':receita['taxa']})
    salvar_json(destino/'otimizador.json',{'classe':'AdamW','grupos':grupos,'taxa':receita['taxa'],
        'betas':[.9,.999],'eps':1e-8,'scheduler':'constante'})
    ids=dados.indices['treino']; val=dados.indices['validacao']
    # Materialização só do treino: C/S não entram no forward/backward/seleção.
    x=torch.as_tensor(dados.janelas(ids),device='cuda')
    y=torch.as_tensor(dados.alvo_normalizado(ids),device='cuda')
    gen=torch.Generator().manual_seed(seed)
    inicio=time.monotonic();melhor=math.inf;espera=0;historico=[];escolhido=None
    torch.cuda.reset_peak_memory_stats()
    perda='huber' if receita['familia_alvo']=='terminal' else 'mse'
    try:
        for epoca in range(1,epocas+1):
            if time.monotonic()-inicio>=limite_segundos:
                raise TimeoutError('Ajuste parcial: limite de tempo, sem publicar como concluído.')
            rede.train();ordem=torch.randperm(len(ids),generator=gen).numpy();soma=0.;normas=[]
            for j in range(0,len(ordem),64):
                if time.monotonic()-inicio>=limite_segundos:
                    raise TimeoutError('Prazo durante época; preservar checkpoints parciais.')
                ix=ordem[j:j+64];v,norma=atualizar(rede,opt,x[ix],y[ix],perda)
                soma+=v*len(ix);normas.append(norma)
            p=prever(rede,dados,val);m=metricas(dados.alvo[val],p)
            linha={'epoca':epoca,'perda_treino':soma/len(ids),'mse_validacao':m['mse'],
                'segundos':time.monotonic()-inicio,'norma_gradiente_maxima':max(normas)}
            if m['mse']<melhor:
                melhor=m['mse'];espera=0;escolhido=epoca
                caminho=destino/'checkpoints'/f'epoca_{epoca:03d}.pt'
                if caminho.exists(): raise FileExistsError(caminho)
                torch.save({'vinculo':vinculo,'epoca':epoca,'pesos':{k:v.detach().cpu().clone() for k,v in rede.state_dict().items()}},caminho)
                linha['checkpoint_sha256']=sha256(caminho)
                h=linha['checkpoint_sha256'];arquivo=caminho
                pred_melhor=p.copy()
            else: espera+=1
            historico.append(linha)
            salvar_json(destino/'progresso.json',{'utc':agora(),'status':'treinando','historico':historico,
                'epoca_escolhida':escolhido,'melhor_mse_validacao':melhor})
            if espera>=paciencia: break
        if escolhido is None: raise RuntimeError('Nenhum checkpoint válido.')
        del opt,x,y,rede;torch.cuda.empty_cache()
        rede=construir(dados,receita)
        if sha256(arquivo)!=h: raise ValueError('Checkpoint alterado.')
        ck=torch.load(arquivo,map_location='cpu',weights_only=True)
        if ck['vinculo']!=vinculo: raise ValueError('Vínculo checkpoint inválido.')
        rede.load_state_dict(ck['pesos'],strict=True)
        p=prever(rede,dados,val)
        if not np.array_equal(p,pred_melhor): raise ValueError('Recarga não reproduziu previsão exata.')
        conclusao={'status':'concluido','utc':agora(),'seed':seed,'vinculo':vinculo,
            'epoca':escolhido,'epocas_executadas':len(historico),'checkpoint':str(arquivo.relative_to(destino)),
            'checkpoint_sha256':h,'recarga_exata':True,'segundos':time.monotonic()-inicio,
            'gpu_pico_bytes':torch.cuda.max_memory_allocated(),'metricas':{}}
        for nome in ('validacao','calibracao','comparacao'):
            ix=dados.indices[nome];p=prever(rede,dados,ix)
            path=destino/(nome+'.npz')
            np.savez_compressed(path,indices=ix,origens_ms=dados.origens_ms[ix],previsoes=p,alvos=dados.alvo[ix])
            conclusao['metricas'][nome]=metricas(dados.alvo[ix],p)
            conclusao[nome+'_sha256']=sha256(path)
        salvar_json(destino/'conclusao.json',conclusao)
        salvar_json(destino/'progresso.json',{'status':'concluido','utc':agora(),'historico':historico,'epoca_escolhida':escolhido})
        return conclusao
    except BaseException:
        import traceback
        salvar_json(destino/'incidente.json',{'utc':agora(),'erro':traceback.format_exc(),'historico':historico})
        raise
    finally:
        torch.cuda.empty_cache()
