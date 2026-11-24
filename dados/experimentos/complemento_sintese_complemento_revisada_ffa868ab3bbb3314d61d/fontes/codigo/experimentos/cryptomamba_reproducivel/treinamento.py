"""Adam/RMSE sem clipping/early-stop; seleção global em V, teste fora do treino."""
import math
import time
from pathlib import Path
import numpy as np
import torch
from infraestrutura.artefatos import salvar_json,sha256,agora,ler_json
from .modelo import construir
from treinamento.otimizacao import fixar_seed


def metricas(y,p,ultimo):
    y,p,ultimo=[np.asarray(v,dtype=np.float64) for v in (y,p,ultimo)]
    if y.shape!=p.shape or y.shape!=ultimo.shape or y.ndim!=1 or not np.isfinite(p).all():
        raise ValueError('Previsões inválidas ou broadcasting.')
    erro=p-y;real=y/ultimo-1;prev=p/ultimo-1
    mse=float(np.mean(erro**2));naive=float(np.mean((ultimo-y)**2))
    return {'n':len(y),'mse_usdt2':mse,'rmse_usdt':math.sqrt(mse),'mae_usdt':float(abs(erro).mean()),
            'mape_pct':float((abs(erro)/y).mean()*100),'mse_naive_usdt2':naive,
            'habilidade_mse_naive':1-mse/naive if naive else None,'mae_retorno':float(abs(prev-real).mean()),
            'acerto_sinal':float(np.mean(np.sign(prev)==np.sign(real))),
            'vies_retorno':float(np.mean(prev-real)),'precos_previstos_nao_positivos':int((p<=0).sum())}


def inferir(rede,x,lote=32):
    rede.eval()
    with torch.inference_mode():
        return np.concatenate([rede(torch.as_tensor(x[i:i+lote],device='cuda')).cpu().numpy() for i in range(0,len(x),lote)]).astype(np.float64)


def ajustar(dados,c,seed,destino,vinculo,epocas=None):
    d=Path(destino);d.mkdir(parents=True,exist_ok=False);(d/'checkpoints').mkdir()
    cfg=c['treinamento'];total=cfg['epocas'] if epocas is None else epocas
    salvar_json(d/'inicio.json',{'utc':agora(),'seed':seed,'vinculo':vinculo,'configuracao':cfg,'epocas':total})
    fixar_seed(seed);rede=construir(c)
    opt=torch.optim.Adam(rede.parameters(),lr=cfg['taxa'],weight_decay=cfg['weight_decay'])
    scheduler=torch.optim.lr_scheduler.StepLR(opt,step_size=cfg['scheduler_passo'],gamma=cfg['scheduler_gamma'])
    x=torch.as_tensor(dados['treino']['x'],device='cuda');y=torch.as_tensor(dados['treino']['y'],dtype=torch.float32,device='cuda')
    gen=torch.Generator().manual_seed(seed);inicio=time.monotonic();melhor=math.inf;historico=[];melhor_p=None
    try:
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
                opt.step();soma+=float(perda.detach())*len(ix)
            val=inferir(rede,dados['validacao']['x']);m=metricas(dados['validacao']['y'],val,dados['validacao']['ultimo_close'])
            if m['rmse_usdt']<melhor:
                melhor=m['rmse_usdt'];escolhida=epoca;melhor_p=val.copy();arquivo=d/'checkpoints'/f'epoca_{epoca:04d}.pt'
                torch.save({'pesos':{k:v.detach().cpu() for k,v in rede.state_dict().items()},'vinculo':vinculo,'epoca':epoca},arquivo)
                salvar_json(d/'selecao.json',{'epoca':epoca,'rmse_validacao':melhor,'checkpoint':arquivo.relative_to(d).as_posix(),'sha256':sha256(arquivo)})
            scheduler.step()
            linha={'epoca':epoca,'perda_treino_rmse_lotes':soma/len(x),'rmse_global_validacao':m['rmse_usdt'],'taxa':taxa,'segundos':time.monotonic()-inicio}
            historico.append(linha)
            with (d/'epocas.jsonl').open('a',encoding='utf-8') as f:
                import json
                f.write(json.dumps(linha)+'\n')
            salvar_json(d/'progresso.json',{'utc':agora(),'situacao':'treinando','epoca':epoca,'total':total,'epoca_escolhida':escolhida,'segundos':time.monotonic()-inicio})
            if epoca==1 or epoca%25==0:print('EPOCA',seed,epoca,'/',total,'RMSE_V',m['rmse_usdt'],flush=True)
        del rede,opt,x,y;torch.cuda.empty_cache();rede=construir(c)
        sel=ler_json(d/'selecao.json');assert sha256(d/sel['checkpoint'])==sel['sha256']
        ck=torch.load(d/sel['checkpoint'],map_location='cpu',weights_only=True);assert ck['vinculo']==vinculo
        rede.load_state_dict(ck['pesos'],strict=True);val=inferir(rede,dados['validacao']['x'])
        np.testing.assert_array_equal(val,melhor_p)
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
