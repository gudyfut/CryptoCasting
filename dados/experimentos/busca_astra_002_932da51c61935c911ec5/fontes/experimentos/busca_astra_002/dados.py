"""Somente candles auditados; alvo e escalas separados das janelas causais."""
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, ler_json, sha256
from .contrato import FINAIS, validar_receita, configuracao, ancoras

CANDLES = 'dados/mercado/candles/93509a1b06b19103ac1c'
INICIO_COMUM = 336  # maior contexto + maior atraso dos indicadores; mesmo suporte para todos

def carregar_candles(desenvolvimento=False):
    p = RAIZ / CANDLES
    m = ler_json(p/'manifesto.json')
    assert sha256(p/'BTCUSDT.parquet') == m['arquivos']['BTCUSDT.parquet']
    q = pd.read_parquet(p/'BTCUSDT.parquet')
    if desenvolvimento:
        q = q.loc[q.fim_utc <= pd.Timestamp('2024-01-01', tz='UTC')].copy()
    assert (pd.DatetimeIndex(q.fim_utc).to_series().diff().dropna() == pd.Timedelta(hours=1)).all()
    campos=['open','high','low','close','volume']
    assert np.isfinite(q.loc[q.completo,campos]).all().all()
    q.loc[~q.completo,campos]=np.nan  # Lacunas preservadas, nunca interpoladas.
    return q.reset_index(drop=True)

def representar(q, r):
    anterior = q.close.shift(1)
    if r['representacao'] == 'relativa':
        x = np.column_stack([np.log(q[c]/anterior) for c in ['open','high','low','close']] + [np.log1p(q.volume)])
    elif r['representacao'] == 'log_niveis':
        x = np.column_stack([np.log(q[c]) for c in ['open','high','low','close']] + [np.log1p(q.volume)])
    else:
        x = q[['open','high','low','close','volume']].to_numpy(float).copy()
    extras=[]
    logc=np.log(q.close);ret=logc.diff();lv=np.log1p(q.volume)
    if r['momentum']:extras += [logc.diff(24),logc.diff(168)]
    if r['volatilidade']:extras += [ret.rolling(24).std(ddof=0),ret.rolling(168).std(ddof=0)]
    if r['volume_relativo']:extras += [lv-lv.rolling(168).mean()]
    if extras:x=np.column_stack([x,*extras])
    return x

class Dados:
    def __init__(self, candles, receita, bloco):
        self.r = validar_receita(receita, ancora=receita in ancoras().values())
        self.bloco = bloco
        self.candles = candles
        self.raw = representar(candles, receita)
        t = pd.DatetimeIndex(candles.fim_utc)
        if bloco in configuracao()['recortes']:
            div=dict(configuracao()['recortes'][bloco]);div['validacao']=div.pop('parada')
            div={k:div[k] for k in ['treino','validacao','comparacao']}
            assert t.max() <= pd.Timestamp('2024-01-01',tz='UTC')
        else:
            a,b,c=FINAIS[bloco]
            div={'treino':('2021-01-01',a),'validacao':(a,b),'teste':(b,c)}
        close = candles.close.to_numpy(float)
        futuro = candles.close.shift(-24).to_numpy(float)
        self.tabela = pd.DataFrame(dict(indice_candle=np.arange(len(t)), origem_utc=t,
            destino_utc=t+pd.Timedelta(hours=24), close=close, preco_destino=futuro, alvo=np.log(futuro/close)))
        self.indices = {}
        observados=np.isfinite(candles[['open','high','low','close','volume']].to_numpy(float)).all(1)
        comum=pd.Series(observados).rolling(336,min_periods=336).sum().eq(336).to_numpy()
        valido = (np.arange(len(t)) >= INICIO_COMUM) & comum
        for parte, (a, b) in div.items():
            a, b = pd.Timestamp(a, tz='UTC'), pd.Timestamp(b, tz='UTC')
            self.indices[parte] = np.flatnonzero(valido & (t >= a) & (t+pd.Timedelta(hours=24) < b) & np.isfinite(futuro))
            assert len(self.indices[parte]) > 0
        ix = self.indices['treino']
        usados = np.zeros(len(t), bool)
        for i in ix:
            usados[i-receita['contexto']+1:i+1] = True
        assert np.isfinite(self.raw[usados]).all()
        self.mu = self.raw[usados].mean(0)
        self.sd = self.raw[usados].std(0)
        self.sd[self.sd == 0] = 1.
        if receita['representacao'] in ('crua', 'janela_relativa'):
            self.mu[:5] = 0.; self.sd[:5] = 1.
        self.matriz = ((self.raw-self.mu)/self.sd).astype(np.float32)
        self.y = self.tabela.alvo.to_numpy(float)
        self.ym = float(self.y[ix].mean()); self.ys = float(self.y[ix].std())
        assert self.ys > 0
        self.escalas = {'media_entrada': self.mu.tolist(), 'escala_entrada': self.sd.tolist(),
            'media_alvo': self.ym, 'escala_alvo': self.ys, 'horas_unicas_treino': int(usados.sum()),
            'inicio_comum_indice': INICIO_COMUM, 'contagens': {k: len(v) for k,v in self.indices.items()},
            'regra': 'Estatisticas somente da uniao de contextos de treino; alvo somente treino.'}

    def janelas(self, indices):
        c = self.r['contexto']
        x = np.stack([self.matriz[i-c+1:i+1] for i in indices])
        if self.r['representacao'] == 'janela_relativa':
            # Referencia de cada janela conhecida na sua origem, nunca depois dela.
            ancora = x[:, -1, 3].astype(float)
            x[:, :, :4] = np.log(x[:, :, :4].astype(float)/ancora[:, None, None])
            lv = np.log1p(x[:, :, 4].astype(float))
            sd = lv.std(1); sd[sd == 0] = 1.
            x[:, :, 4] = (lv-lv.mean(1)[:, None])/sd[:, None]
        assert x.shape == (len(indices), c, self.matriz.shape[1]) and np.isfinite(x).all()
        return np.ascontiguousarray(x, dtype=np.float32)

def diagnostico(d):
    out = {'escalas': d.escalas, 'partes': {}}
    for parte in ['treino', 'validacao']:
        ix = d.indices[parte]
        xs = d.raw[ix]
        y = d.y[ix]
        out['partes'][parte] = {'n': len(ix), 'alvo_media': float(y.mean()), 'alvo_sd': float(y.std()),
            'mse_naive': float(np.mean(y*y)), 'quantis_canais': np.quantile(xs, [.01,.5,.99], axis=0).tolist(),
            'correlacao_canais_alvo': [float(np.corrcoef(xs[:,j],y)[0,1]) if xs[:,j].std()>0 else 0.
                                     for j in range(xs.shape[1])]}
    return out
