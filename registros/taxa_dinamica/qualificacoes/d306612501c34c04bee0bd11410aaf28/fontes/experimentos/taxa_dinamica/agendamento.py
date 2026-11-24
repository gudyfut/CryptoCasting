"""Política única e explícita, baseada apenas na validação; não reinicia parada."""
POLITICA={'nome':'ReduceLROnPlateau','mode':'min','factor':.5,'patience':2,
          'threshold':0.,'threshold_mode':'abs','cooldown':0,'min_lr':.000025,'eps':1e-8}


def criar_agendador(otimizador,configuracao):
    import torch
    if configuracao!=POLITICA:raise ValueError('Política diferente do ciclo delimitado.')
    return torch.optim.lr_scheduler.ReduceLROnPlateau(otimizador,**{k:v for k,v in configuracao.items() if k!='nome'})
