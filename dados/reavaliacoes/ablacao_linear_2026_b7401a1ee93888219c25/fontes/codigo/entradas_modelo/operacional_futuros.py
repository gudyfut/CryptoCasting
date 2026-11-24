"""Canais e janelas causais da linha operacional; sem modelos ou simuladores."""
from dataclasses import dataclass
import numpy as np
import pandas as pd

BASE = ('open','high','low','close','volume')


def conferir_candles(q):
    obrigatorias = {'open_time','close_time',*BASE}
    if not obrigatorias.issubset(q.columns) or len(q) < 400:
        raise ValueError('Candles horários completos insuficientes.')
    tempos = q.open_time.to_numpy(dtype=np.int64)
    if not np.equal(np.diff(tempos),3600000).all() or (tempos % 3600000).any():
        raise ValueError('Grade horária incompleta/desalinhada; não interpolar.')
    if not np.equal(q.close_time.to_numpy(),tempos+3599999).all():
        raise ValueError('Candle incompleto.')
    x=q[list(BASE)].to_numpy(float)
    if not np.isfinite(x).all() or (x[:,:4]<=0).any() or (x[:,4]<0).any():
        raise ValueError('OHLCV inválido.')
    if ((q.low>q[['open','close']].min(axis=1)) | (q.high<q[['open','close']].max(axis=1))).any():
        raise ValueError('Máxima/mínima inválidas.')


def montar_canais(q, receita):
    conferir_candles(q)
    rep=receita['representacao'];c=q.close.astype(float);v=np.log1p(q.volume.astype(float))
    if rep=='crua':
        a=q[list(BASE)].astype(float).copy();padronizar=[False]*5
    elif rep in ['relativa','log_niveis']:
        a=np.log(q[list(BASE[:4])].astype(float))
        if rep=='relativa':a=a.sub(np.log(c.shift(1)),axis=0)
        a['volume']=v;padronizar=[True]*5
    else:raise ValueError('Representação fora do espaço proposto.')
    if receita.get('momentum',False):
        for h in [24,72,168]:a[f'momentum_{h}']=np.log(c/c.shift(h));padronizar.append(True)
    if receita.get('volatilidade',False):
        ret=np.log(c/c.shift(1))
        for h in [24,168]:a[f'volatilidade_{h}']=ret.rolling(h,min_periods=h).std(ddof=1);padronizar.append(True)
    if receita.get('volume_relativo',False):
        for h in [24,168]:a[f'volume_relativo_{h}']=v-v.rolling(h,min_periods=h).mean();padronizar.append(True)
    return a.to_numpy(float),tuple(a.columns),np.array(padronizar,dtype=bool)


def indices_temporais(q, calendario, contexto, purga_minutos=1442):
    if contexto not in [24,72,168] or purga_minutos<1442:
        raise ValueError('Contexto/purga incompatíveis.')
    origens=q.close_time.to_numpy(dtype=np.int64)+1
    indices=np.arange(len(q));resultado={}
    nomes={'treino':'treino','validacao':'validacao','calibracao':'calibracao',
           'comparacao':'comparacao' if 'comparacao' in calendario else 'avaliacao'}
    for nome, chave in nomes.items():
        inicio,fim=[int(pd.Timestamp(t,tz='UTC').timestamp()*1000) for t in calendario[chave]]
        # 336 primeiras horas reservadas para o suporte composto comum.
        mask=(indices>=336)&(origens>=inicio)&(origens+purga_minutos*60000<fim)
        ids=indices[mask]
        if not len(ids):raise ValueError(f'Partição vazia: {nome}')
        resultado[nome]=ids
    for a,b in zip(nomes,list(nomes)[1:]):
        if origens[resultado[a][-1]]+purga_minutos*60000>=origens[resultado[b][0]]:
            raise ValueError('Sobreposição de realizações entre partições.')
    return origens,resultado


def suporte_treino(ids, contexto, tamanho):
    diferencas=np.zeros(tamanho+1,dtype=np.int64)
    np.add.at(diferencas,ids-contexto+1,1);np.add.at(diferencas,ids+1,-1)
    return np.cumsum(diferencas[:-1])>0


@dataclass
class DadosOperacionais:
    matriz: np.ndarray
    alvo: np.ndarray
    origens_ms: np.ndarray
    indices: dict
    canais: tuple
    contexto: int
    escalas: dict

    def janelas(self, ids):
        ids=np.asarray(ids,dtype=np.int64)
        if ids.ndim!=1 or (ids<self.contexto-1).any() or (ids>=len(self.matriz)).any():
            raise ValueError('Índices de janela inválidos.')
        x=self.matriz[ids[:,None]-np.arange(self.contexto-1,-1,-1)]
        if not np.isfinite(x).all():raise ValueError('Janela contém dados ausentes.')
        return x

    def alvo_normalizado(self,ids):
        return ((self.alvo[ids]-np.array(self.escalas['media_alvo']))/np.array(self.escalas['escala_alvo'])).astype(np.float32)

    def decodificar(self,z):
        z=np.asarray(z)
        if z.ndim!=2 or z.shape[1]!=self.alvo.shape[1] or not np.isfinite(z).all():
            raise ValueError('Saída normalizada incompatível.')
        return z*np.array(self.escalas['escala_alvo'])+np.array(self.escalas['media_alvo'])


def preparar(q,receita,calendario,alvos_payoff=None):
    q=q.reset_index(drop=True)
    bruto,canais,pad=montar_canais(q,receita)
    contexto=receita['contexto_horas']
    origens,indices=indices_temporais(q,calendario,contexto)
    if receita['familia_alvo']=='terminal':
        if alvos_payoff is not None:raise ValueError('Alvo payoff não pertence à tarefa terminal.')
        y=np.log(q.close.shift(-24).to_numpy()/q.close.to_numpy())[:,None]
    elif receita['familia_alvo']=='payoff':
        if alvos_payoff is None:raise ValueError('Payoffs precisam vir do contrato de alvos auditado.')
        y=np.asarray(alvos_payoff,dtype=float)
        if y.shape!=(len(q),2):raise ValueError('Dois alvos de payoff por origem são obrigatórios.')
    else:raise ValueError('Família de alvo desconhecida.')
    suporte=suporte_treino(indices['treino'],contexto,len(q))
    if not np.isfinite(bruto[suporte]).all():raise ValueError('Suporte de treino incompleto.')
    media=np.zeros(len(canais));escala=np.ones(len(canais))
    media[pad]=bruto[suporte][:,pad].mean(axis=0)
    escala[pad]=bruto[suporte][:,pad].std(axis=0,ddof=0)
    escala[escala==0]=1.
    yt=y[indices['treino']]
    if not np.isfinite(yt).all():raise ValueError('Alvo de treino ausente.')
    ym=yt.mean(axis=0);ys=yt.std(axis=0,ddof=0);ys[ys==0]=1.
    x=((bruto-media)/escala).astype(np.float32)
    for nome,ids in indices.items():
        if not np.isfinite(y[ids]).all():raise ValueError(f'Alvo ausente em {nome}; não descartar origem.')
        mascara=suporte_treino(ids,contexto,len(q))
        if not np.isfinite(x[mascara]).all():raise ValueError(f'Janela ausente em {nome}.')
    escalas={'media_entrada':media.tolist(),'escala_entrada':escala.tolist(),'padronizar':pad.tolist(),
        'media_alvo':ym.tolist(),'escala_alvo':ys.tolist(),'linhas_suporte_treino':int(suporte.sum()),
        'ultimo_candle_suporte_ms':int(q.close_time.iloc[np.flatnonzero(suporte)[-1]])}
    return DadosOperacionais(x,y,origens,indices,canais,contexto,escalas)
