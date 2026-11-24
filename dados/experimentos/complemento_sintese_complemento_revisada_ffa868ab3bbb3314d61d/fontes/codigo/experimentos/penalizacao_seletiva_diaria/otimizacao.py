"""Grupos explícitos de Adam; não troca por AdamW nem muda inicialização."""
import torch
from torch import nn
from infraestrutura.artefatos import salvar_json
from experimentos.sem_penalizacao_diaria.observacao import grupo


def separar(rede, politica, penalizacao):
    if politica not in ('uniforme','seletiva'):
        raise ValueError('Política desconhecida.')
    normalizacao = {id(p) for m in rede.modules() if isinstance(m,nn.LayerNorm)
                    for p in m.parameters(recurse=False)}
    grupos = {True:[], False:[]}; registro=[]; vistos=set()
    for nome,p in rede.named_parameters():
        assert p.requires_grad and id(p) not in vistos
        vistos.add(id(p));motivos=[]
        if getattr(p,'_no_weight_decay',False):motivos.append('marcador_no_weight_decay')
        if id(p) in normalizacao:motivos.append('parametros_LayerNorm')
        if nome.rsplit('.',1)[-1]=='bias':motivos.append('bias')
        isento = politica=='seletiva' and bool(motivos)
        grupos[isento].append(p)
        registro.append({'nome':nome,'forma':list(p.shape),'elementos':p.numel(),
                         'motivos_elegibilidade':motivos,'weight_decay':0. if isento else penalizacao})
    assert vistos == {id(p) for p in rede.parameters()}
    efetivos=[{'params':grupos[k], 'weight_decay':0. if k else penalizacao}
              for k in (False,True) if grupos[k]]
    return efetivos, registro


def construir_otimizador(rede,cfg,destino):
    grupos,registro=separar(rede,cfg['politica_penalizacao'],cfg['weight_decay'])
    salvar_json(destino/'grupos_penalizacao.json',{
        'politica':cfg['politica_penalizacao'],'parametros':registro,
        'elementos_totais':sum(p.numel() for p in rede.parameters()),
        'elementos_isentos':sum(r['elementos'] for r in registro if r['weight_decay']==0),
        'elementos_penalizados':sum(r['elementos'] for r in registro if r['weight_decay']!=0)})
    return torch.optim.Adam(grupos,lr=cfg['taxa'],weight_decay=cfg['weight_decay'])


def gradientes(rede,otimizador):
    coeficientes={id(p):g['weight_decay'] for g in otimizador.param_groups for p in g['params']}
    somas={}
    for n,p in rede.named_parameters():
        g=somas.setdefault(grupo(n),{'grad2':0.,'l2_2':0.})
        assert p.grad is not None and torch.isfinite(p.grad).all(),n
        g['grad2']+=float(p.grad.detach().double().square().sum())
        g['l2_2']+=float((coeficientes[id(p)]*p.detach().double()).square().sum())
    return {k:{'norma_gradiente_tarefa':v['grad2']**.5,'norma_l2':v['l2_2']**.5} for k,v in somas.items()}
