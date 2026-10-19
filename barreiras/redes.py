"""Redes com configuração explícita, cinco features e uma distância auxiliar."""
from __future__ import annotations

import torch
from torch import nn


class RedeMamba(nn.Module):
    def __init__(self, parametros, backend='oficial'):
        super().__init__()
        if backend == 'oficial':
            from mamba_ssm import Mamba
        elif backend == 'pytorch':
            from modelo.mamba_minimal import Mamba
        else:
            raise ValueError('Backend desconhecido.')
        d=parametros['largura']
        self.projecao=nn.Linear(5,d)
        self.blocos=nn.ModuleList([Mamba(d_model=d,d_state=parametros['estado'],
             d_conv=parametros['convolucao'],expand=parametros['expansao']) for _ in range(parametros['camadas'])])
        self.normas=nn.ModuleList([nn.LayerNorm(d) for _ in self.blocos])
        self.dropout=nn.Dropout(parametros['dropout'])
        self.norma_final=nn.LayerNorm(d)
        self.classificador=nn.Linear(d+1,3)

    def forward(self, entradas, auxiliar):
        x=self.projecao(entradas)
        for bloco,norma in zip(self.blocos,self.normas):
            x=norma(x+bloco(x))
        x=self.norma_final(self.dropout(x))[:,-1,:]
        return self.classificador(torch.cat([x,auxiliar],dim=1))


class RedeLSTM(nn.Module):
    def __init__(self,parametros):
        super().__init__()
        d=parametros['largura']
        self.recorrente=nn.LSTM(5,d,num_layers=parametros['camadas'],batch_first=True,
             bidirectional=False,dropout=parametros['dropout'] if parametros['camadas']>1 else 0)
        self.classificador=nn.Linear(d+1,3)

    def forward(self,entradas,auxiliar):
        sequencia,_=self.recorrente(entradas)
        return self.classificador(torch.cat([sequencia[:,-1,:],auxiliar],dim=1))


def criar(nome,c):
    if nome=='mamba':
        return RedeMamba(c['mamba'],c['backend'])
    if nome=='lstm':
        return RedeLSTM(c['lstm'])
    raise ValueError('Rede desconhecida.')
