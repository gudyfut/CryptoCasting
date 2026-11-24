"""Redes escalares com mesma informação e dimensão configurável explícita."""
import torch
from torch import nn

class RedeMamba(nn.Module):
    def __init__(self,p):
        super().__init__()
        from mamba_ssm import Mamba
        d=p['largura']
        self.projecao=nn.Linear(1,d)
        self.blocos=nn.ModuleList([Mamba(d_model=d,d_state=p['estado'],d_conv=p['convolucao'],expand=p['expansao']) for _ in range(p['camadas'])])
        self.normas=nn.ModuleList([nn.LayerNorm(d) for _ in self.blocos])
        self.dropout=nn.Dropout(p['dropout'])
        self.norma_final=nn.LayerNorm(d)
        self.saida=nn.Linear(d,1)

    def forward(self,x):
        x=self.projecao(x)
        for bloco,norma in zip(self.blocos,self.normas):
            x=norma(x+bloco(x))
        return self.saida(self.norma_final(self.dropout(x))[:,-1,:]).squeeze(-1)

class RedeLSTM(nn.Module):
    def __init__(self,p):
        super().__init__()
        self.recorrente=nn.LSTM(1,p['largura'],num_layers=p['camadas'],batch_first=True,
                                dropout=p['dropout'] if p['camadas']>1 else 0,bidirectional=False)
        self.saida=nn.Linear(p['largura'],1)

    def forward(self,x):
        sequencia,_=self.recorrente(x)
        return self.saida(sequencia[:,-1,:]).squeeze(-1)

def criar(nome,c):
    if nome=='mamba':
        if c['backend']!='oficial':
            raise ValueError('Mamba exige backend oficial.')
        return RedeMamba(c['mamba'])
    if nome=='lstm':
        return RedeLSTM(c['lstm'])
    raise ValueError('Modelo desconhecido.')
