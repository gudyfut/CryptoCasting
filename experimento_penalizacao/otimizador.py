"""Exceção explícita de weight decay, sem modificar arquitetura ou inicialização."""
import torch


def grupos_parametros(rede,penalizacao):
    grupos=[]
    # Grupos contíguos mantêm a ordem original dos parâmetros. Não usar sets.
    for nome,parametro in rede.named_parameters():
        valor=0.0 if getattr(parametro,'_no_weight_decay',False) else penalizacao
        if not grupos or grupos[-1]['weight_decay']!=valor:
            grupos.append({'params':[],'weight_decay':valor,'nomes':[]})
        grupos[-1]['params'].append(parametro)
        grupos[-1]['nomes'].append(nome)
    if not grupos or sum(len(g['params']) for g in grupos)!=len(list(rede.parameters())):
        raise ValueError('Cobertura inválida dos parâmetros.')
    return grupos


def descrever_grupos(rede,t):
    return [{'nomes':g['nomes'],'weight_decay':g['weight_decay'],
             'elementos':sum(p.numel() for p in g['params'])} for g in grupos_parametros(rede,t['weight_decay'])]


def criar_otimizador(rede,t):
    grupos=[{'params':g['params'],'weight_decay':g['weight_decay']} for g in grupos_parametros(rede,t['weight_decay'])]
    return torch.optim.AdamW(grupos,lr=t['taxa_aprendizado'],weight_decay=t['weight_decay'],betas=(.9,.999),eps=1e-8)
