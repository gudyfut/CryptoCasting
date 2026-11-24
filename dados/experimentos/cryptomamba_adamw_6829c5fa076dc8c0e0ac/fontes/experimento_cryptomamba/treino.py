"""Treino Adam/RMSE e avaliação; checkpoint/contratos de dados preservados."""
import time
import numpy as np
from infraestrutura.artefatos import RAIZ,salvar_json,agora
from treinamento.otimizacao import fixar_seed
from treinamento.selecao import SelecaoEpoca
from treinamento import checkpoints
from modelos.neurais import prever_neural
from avaliacao.metricas import calcular
from avaliacao.publicacao import conferir_previsoes
from .modelo import criar_rede


def otimizador(rede,cfg):
    import torch
    por_decay={};recibo=[]
    for nome,p in rede.named_parameters():
        decay=0. if getattr(p,'_no_weight_decay',False) else cfg['treino']['weight_decay']
        por_decay.setdefault(decay,[]).append(p);recibo.append({'nome':nome,'weight_decay':decay,'elementos':p.numel()})
    o=cfg['otimizador']
    grupos=[{'params':ps,'weight_decay':d} for d,ps in por_decay.items()]
    return torch.optim.Adam(grupos,lr=cfg['treino']['taxa_aprendizado'],betas=tuple(o['betas']),eps=o['eps']),recibo


def ajustar(consumo,seed,cfg,destino,vinculo):
    import torch
    fixar_seed(seed);rede=criar_rede(consumo.especificacao,cfg);opt,grupos=otimizador(rede,cfg)
    scheduler=torch.optim.lr_scheduler.StepLR(opt,step_size=cfg['scheduler']['passo_epocas'],gamma=cfg['scheduler']['gamma'])
    salvar_json(destino/'grupos_otimizador.json',grupos)
    pedido=consumo.solicitar('treino');lotes=[]
    for i in range(0,len(pedido.origens),256):
        sub=consumo.solicitar('treino',np.arange(i,min(i+256,len(pedido.origens))));lotes.append(consumo.lote_neural(sub).entradas)
    x=torch.as_tensor(np.concatenate(lotes),device='cuda');y=torch.as_tensor(consumo.alvos_supervisionados(pedido),device='cuda');del lotes
    val=consumo.solicitar('validacao');yval=consumo.alvos_supervisionados(val,padronizados=False)
    selecao=SelecaoEpoca(cfg['treino']['paciencia']);gerador=torch.Generator().manual_seed(seed);inicio=time.perf_counter();historico=[]
    torch.cuda.reset_peak_memory_stats()
    for epoca in range(1,cfg['treino']['epocas']+1):
        rede.train();ordem=torch.randperm(len(y),generator=gerador).to('cuda');soma=0.;taxa=opt.param_groups[0]['lr']
        for i in range(0,len(y),cfg['treino']['batch']):
            idx=ordem[i:i+cfg['treino']['batch']];opt.zero_grad(set_to_none=True);prev=rede(x[idx]);real=y[idx]
            if prev.shape!=real.shape:raise ValueError('Broadcasting proibido.')
            mse=torch.nn.functional.mse_loss(prev,real);perda=torch.sqrt(mse+cfg['perda']['epsilon'])
            if not torch.isfinite(perda):raise ValueError('RMSE não finito.')
            perda.backward();torch.nn.utils.clip_grad_norm_(rede.parameters(),cfg['treino']['clipping'],error_if_nonfinite=True);opt.step();soma+=float(mse.detach().cpu())*len(idx)
        rede.eval();previsao=prever_neural(rede,consumo,val,cfg['treino']['batch']).previsao.to_numpy();mse=float(np.mean((previsao-yval)**2))
        melhorou=selecao.observar(epoca,mse)
        if melhorou:checkpoints.guardar(destino,rede,vinculo,epoca,mse)
        historico.append({'epoca':epoca,'mse_treino_padronizado':soma/len(y),'mse_validacao':mse,'melhorou':melhorou,'taxa_aprendizado':taxa,'utc':agora(),'segundos':time.perf_counter()-inicio})
        salvar_json(destino/'epocas.json',historico);print(f'cryptomamba seed={seed} época={epoca} lr={taxa:.8g} mse_val={mse:.9g} espera={selecao.espera}',flush=True)
        scheduler.step()
        if selecao.parar:break
    checkpoints.carregar(destino,rede,vinculo)
    refeito=prever_neural(rede,consumo,val,cfg['treino']['batch']).previsao.to_numpy()
    if float(np.mean((refeito-yval)**2))!=selecao.melhor:raise ValueError('Recarga diverge da seleção.')
    r={'modelo':'cryptomamba_adaptado','seed':seed,'epoca_selecionada':selecao.epoca,'epocas_executadas':len(historico),'parametros':sum(p.numel() for p in rede.parameters()),'segundos':time.perf_counter()-inicio,'memoria_cuda_maxima_bytes':torch.cuda.max_memory_allocated()}
    salvar_json(destino/'ajuste.json',r);return rede,r


def avaliar(consumo,partes,cfg,destino,vinculo,rede,ajuste):
    r=dict(ajuste,metricas={});checkpoints.carregar(destino,rede,vinculo);recarga=criar_rede(consumo.especificacao,cfg);checkpoints.carregar(destino,recarga,vinculo)
    for b in ('validacao','teste','operacional'):
        pedido=consumo.solicitar(b);q=prever_neural(rede,consumo,pedido,cfg['treino']['batch']);z=prever_neural(recarga,consumo,pedido,cfg['treino']['batch'])
        if not np.array_equal(q.previsao.to_numpy(),z.previsao.to_numpy()):raise ValueError('Recarga preditiva não exata.')
        esperado=partes[b];q=esperado.merge(q[['indice_candle','previsao']],on='indice_candle',how='left',validate='one_to_one')
        if b!='operacional':r['metricas'][b]=calcular(q.alvo,q.previsao)
        conferir_previsoes(q,esperado,r['metricas'].get(b));q.to_parquet(destino/f'previsoes_{b}.parquet',index=False)
    r['recarga_exata']=True;salvar_json(destino/'resultado.json',r);return r
