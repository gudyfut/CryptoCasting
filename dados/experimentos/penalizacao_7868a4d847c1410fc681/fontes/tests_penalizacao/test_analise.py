import copy
import unittest
import numpy as np
import pandas as pd
from previsao24.arquivos import RAIZ,ler_json
from previsao24.financeiro import simular
from experimento_penalizacao.analise import auditar_financeiro
from manutencao.consolidar_resultados import diario,intervalo_blocos


class AnaliseTeste(unittest.TestCase):
    def test_contraste_constante_e_zero(self):
        t=pd.date_range('2023-01-01',periods=100,freq='h',tz='UTC').to_series().reset_index(drop=True)
        for valor in (-.00001,0.,.00001):
            d=diario(t,np.full(len(t),valor),'DB1')
            # Usar somente calendário observado neste teste de identidade.
            validos=d[1]>0
            r=intervalo_blocos([(d[0][validos],d[1][validos])],2,50,17)
            self.assertAlmostEqual(r['inferior'],valor,places=14); self.assertAlmostEqual(r['superior'],valor,places=14)

    def test_contabilidade_e_corrupcao(self):
        c=ler_json(RAIZ/'configuracoes/retorno24_001.json')
        t=pd.Timestamp('2023-01-01',tz='UTC'); primeiro=int(t.timestamp()//60)
        minutos=np.ones((3*1440,6)); minutos[:,:4]=100; minutos[1441:,:4]=102
        q=pd.DataFrame({'origem_utc':[t,t+pd.Timedelta(days=1)],'previsao':[.02,0.]})
        for agravado in (False,True):
            r,ordens,_=simular(q,minutos,primeiro,'2023-01-04',c['operacao'],agravado=agravado)
            self.assertEqual(auditar_financeiro(q,minutos,primeiro,c,r,ordens),1)
            errado=copy.deepcopy(ordens); errado[0]['preco_entrada']*=2
            with self.assertRaises(ValueError): auditar_financeiro(q,minutos,primeiro,c,r,errado)


if __name__=='__main__': unittest.main()
