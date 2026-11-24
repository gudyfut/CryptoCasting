"""Fronteira consumida por modelos: arrays e metadados, sem rede/otimizador/API."""
from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass
class ConjuntoEntradas:
    matriz: np.ndarray
    origens: pd.DataFrame
    partes: dict
    escalas: dict
    contrato: dict

    @property
    def dimensao_entrada(self):
        return len(self.contrato['canais'])

    def janelas(self,indices):
        indices=np.asarray(indices)
        w=self.contrato['contexto_passos']
        if indices.ndim!=1 or not np.issubdtype(indices.dtype,np.integer) or (indices<w-1).any() or (indices>=len(self.matriz)).any():
            raise ValueError('Índices inválidos para construir janelas.')
        j=self.matriz[indices[:,None]+np.arange(1-w,1)[None,:]]
        if not np.isfinite(j).all():
            raise ValueError('Janela contém entrada indisponível.')
        return j

    def inverter_alvo(self,previsto_padronizado):
        return np.asarray(previsto_padronizado)*self.escalas['escala_alvo']+self.escalas['media_alvo']

    def adaptar_ohlcv24(self):
        """Compatibilidade de dados com o executor congelado; não executa nem altera esse executor."""
        from .receitas import CANAIS
        if self.contrato['intervalo_minutos']!=60 or self.contrato['canais']!=CANAIS or self.contrato['horizonte_minutos']!=1440:
            raise ValueError('Executor OHLCV24 antigo exige cinco canais, 1h e horizonte24h.')
        renomear=lambda q:q.rename(columns={'indice_candle':'indice_hora'})
        e=dict(self.escalas)
        e['horas_unicas_ajuste']=e.pop('candles_unicos_ajuste')
        e['regra']='união de horas únicas dos contextos de treino; ddof=0; constante recebe escala 1'
        return renomear(self.origens),self.matriz,{k:renomear(q) for k,q in self.partes.items()},e
