"""Adam/RMSE sem clipping/early-stop; seleção global em V, teste fora do treino."""
import math
import time
from pathlib import Path
import numpy as np
import torch
from infraestrutura.artefatos import salvar_json,sha256,agora,ler_json
from experimentos.cryptomamba_reproducivel.modelo import construir
from treinamento.otimizacao import fixar_seed


from experimentos.alvo_retorno_diario.metricas import metricas_retorno as metricas
from .observacao import observar, gradientes, EPOCAS


def inferir(rede,x,lote=32):
    rede.eval()
    with torch.inference_mode():
        return np.concatenate([rede(torch.as_tensor(x[i:i+lote],device='cuda')).cpu().numpy() for i in range(0,len(x),lote)]).astype(np.float64)


def ajustar(dados,c,seed,destino,vinculo,epocas=None):
    d=Path(destino);d.mkdir(parents=True,exist_ok=False);(d/'checkpoints').mkdir()
    cfg=c['treinamento'];total=cfg['epocas'] if epocas is None else epocas
    salvar_json(d/'inicio.json',{'utc':agora(),'seed':seed,'vinculo':vinculo,'configuracao':cfg,'epocas':total,'unidade_saida':'retorno_simples_decimal'})
    fixar_seed(seed);rede=construir(c)
    opt=torch.optim.Adam(rede.parameters(),lr=cfg['taxa'],weight_decay=cfg['weight_decay'])
    scheduler=torch.optim.lr_scheduler.StepLR(opt,step_size=cfg['scheduler_passo'],gamma=cfg['scheduler_gamma'])
    x=torch.as_tensor(dados['treino']['x'],device='cuda');y=torch.as_tensor(dados['treino']['y'],dtype=torch.float32,device='cuda')
    gen=torch.Generator().manual_seed(seed);inicio=time.monotonic();melhor=math.inf;historico=[];melhor_p=None
    try:
        observar(rede,dados['treino']['x'],d/'observacoes/inicial.json',0)
        for epoca in range(1,total+1):
            if time.monotonic()-inicio>cfg['limite_segundos_por_ajuste']:raise TimeoutError('Limite do ajuste; preservar sem publicar como concluído.')
            rede.train();ordem=torch.randperm(len(x),generator=gen).numpy();soma=0.;taxa=opt.param_groups[0]['lr']
            for i in range(0,len(ordem),cfg['lote']):
                ix=ordem[i:i+cfg['lote']];opt.zero_grad(set_to_none=True)
                pred=rede(x[ix]);mse=torch.mean((pred-y[ix])**2);perda=torch.sqrt(mse+cfg['epsilon_raiz'])
                if not torch.isfinite(perda):raise ValueError('Perda não finita.')
                perda.backward()
                finitos=torch.stack([torch.isfinite(p.grad).all() for p in rede.parameters() if p.grad is not None]).all()
                if not finitos:raise ValueError('Gradiente não finito.')
                if epoca in EPOCAS and i+cfg['lote']>=len(ordem):
                    grad=gradientes(rede,cfg['weight_decay'])
                opt.step();soma+=float(perda.detach())*len(ix)
            val=inferir(rede,dados['validacao']['x']);m=metricas(dados['validacao']['y'],val,dados['validacao']['ultimo_close'])
            if m['rmse_retorno']<melhor:
                melhor=m['rmse_retorno'];escolhida=epoca;melhor_p=val.copy();arquivo=d/'checkpoints'/f'epoca_{epoca:04d}.pt'
                torch.save({'pesos':{k:v.detach().cpu() for k,v in rede.state_dict().items()},'vinculo':vinculo,'epoca':epoca},arquivo)
                salvar_json(d/'selecao.json',{'epoca':epoca,'rmse_validacao':melhor,'checkpoint':arquivo.relative_to(d).as_posix(),'sha256':sha256(arquivo)})
            scheduler.step()
            if epoca in EPOCAS:observar(rede,dados['treino']['x'],d/'observacoes'/f'epoca_{epoca:04d}.json',epoca,grad)
            linha={'epoca':epoca,'perda_treino_rmse_lotes':soma/len(x),'rmse_global_validacao_retorno':m['rmse_retorno'],'taxa':taxa,'segundos':time.monotonic()-inicio}
            historico.append(linha)
            with (d/'epocas.jsonl').open('a',encoding='utf-8') as f:
                import json
                f.write(json.dumps(linha)+'\n')
            salvar_json(d/'progresso.json',{'utc':agora(),'situacao':'treinando','epoca':epoca,'total':total,'epoca_escolhida':escolhida,'segundos':time.monotonic()-inicio})
            if epoca==1 or epoca%25==0:print('EPOCA',seed,epoca,'/',total,'RMSE_V',m['rmse_retorno'],flush=True)
        del rede,opt,x,y;torch.cuda.empty_cache();rede=construir(c)
        sel=ler_json(d/'selecao.json');assert sha256(d/sel['checkpoint'])==sel['sha256']
        ck=torch.load(d/sel['checkpoint'],map_location='cpu',weights_only=True);assert ck['vinculo']==vinculo
        rede.load_state_dict(ck['pesos'],strict=True);val=inferir(rede,dados['validacao']['x'])
        np.testing.assert_array_equal(val,melhor_p)
        observar(rede,dados['treino']['x'],d/'observacoes/selecionado.json',sel['epoca'])
        np.savez_compressed(d/'validacao.npz',previsoes=val,**{k:v for k,v in dados['validacao'].items() if k!='x'})
        conclusao={'utc':agora(),'situacao':'concluido','seed':seed,'epocas':total,'epoca_escolhida':escolhida,'recarga_exata':True,
                   'segundos':time.monotonic()-inicio,'metricas_validacao':metricas(dados['validacao']['y'],val,dados['validacao']['ultimo_close']),
                   'checkpoint':sel,'vinculo':vinculo}
        salvar_json(d/'conclusao.json',conclusao);salvar_json(d/'progresso.json',dict(conclusao,situacao='concluido'))
        return conclusao
    except BaseException:
        import traceback
        salvar_json(d/'incidente.json',{'utc':agora(),'erro':traceback.format_exc()});raise


def carregar_rede(d,c):
    d=Path(d);sel=ler_json(d/'selecao.json');assert sha256(d/sel['checkpoint'])==sel['sha256']
    ck=torch.load(d/sel['checkpoint'],map_location='cpu',weights_only=True)
    rede=construir(c);rede.load_state_dict(ck['pesos'],strict=True);return rede.eval()
