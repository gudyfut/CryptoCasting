"""Integração com séries sintéticas; não representa resultado de mercado."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
import numpy as np
import pandas as pd
from previsao24.arquivos import salvar_json, ler_json
from previsao24.baselines import ajustar
from previsao24.metricas import calcular
from estudo_ohlcv.ciclo import configuracao, grade, publicar_tentativa, verificar_tentativa
from estudo_ohlcv.avaliacao import concluir


class Publicacao(unittest.TestCase):
    def test_arima_sintetico_e_publicacao_completa(self):
        c=configuracao()
        c['divisao']['teste']=['2025-01-01','2025-01-04']
        c['bootstrap']['replicas']=10
        c['arima']['ordens']=[[0,1,0],[1,1,0]]
        n=900
        rng=np.random.default_rng(17)
        close=100*np.exp(np.cumsum(rng.normal(0,.001,n)))
        h=pd.DataFrame({'indice_hora':np.arange(n),'origem_utc':pd.date_range('2024-12-01',periods=n,freq='h',tz='UTC'),'close':close})
        h['destino_utc']=h.origem_utc+pd.Timedelta(hours=24)
        h['preco_destino']=h.close.shift(-24)
        h['alvo']=np.log(h.preco_destino/h.close)
        b={'treino':h.iloc[168:400], 'validacao':h.iloc[424:600], 'teste':h.iloc[744:792], 'operacional':h.iloc[744:816]}
        with tempfile.TemporaryDirectory(prefix='cc_ohlcv_sintetico_') as temp:
            raiz=Path(temp)
            arima=raiz/'arima'
            with contextlib.redirect_stdout(io.StringIO()):
                resultado=ajustar(h,b,c,arima)
            self.assertGreaterEqual(resultado['candidatos_validos'],1)
            t={}
            for celula in grade(c):
                chave=celula['chave'];p=raiz/chave;p.mkdir(exist_ok=True)
                if chave!='arima':
                    r={'modelo':celula['modelo'],'metricas':{}}
                    for nome in ('validacao','teste','operacional'):
                        q=b[nome].copy();q['previsao']=0.
                        q.to_parquet(p/f'previsoes_{nome}.parquet',index=False)
                        if nome!='operacional':r['metricas'][nome]=calcular(q.alvo,q.previsao)
                    salvar_json(p/'resultado.json',r)
                publicar_tentativa(p);verificar_tentativa(p);t[chave]=p
            minutos=np.ones((5000,6))*100
            np.save(raiz/'minutos.npy',minutos)
            m={'minutos':str(raiz/'minutos.npy'),'primeiro_minuto':int(pd.Timestamp('2025-01-01',tz='UTC').timestamp()//60)}
            concluir(raiz,c,m,b,t)
            ponteiro=ler_json(raiz/'publicacao.json')
            r=ler_json(raiz/ponteiro['pasta']/'resultados.json')
            self.assertEqual(len(r['por_ajuste']),8)
            self.assertEqual(r['medias']['teste']['naive']['habilidade_mse'],0.)
            self.assertEqual(r['por_ajuste']['naive']['spot']['base']['entradas_planejadas'],0)
            self.assertLess(r['referencias_economicas']['compra_diaria_base']['retorno_liquido'],0.)
            self.assertEqual(len(r['contrastes']['teste']),4)
            # Corrupção deve falhar, nunca regenerar manifesto para aceitar novos bytes.
            (t['naive']/'resultado.json').write_text('{}',encoding='utf-8')
            with self.assertRaises(ValueError):verificar_tentativa(t['naive'])


if __name__=='__main__':unittest.main()
