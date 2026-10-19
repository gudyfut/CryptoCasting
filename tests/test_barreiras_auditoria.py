import copy
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from barreiras.auditoria import auditar_financeiro,rotulo_referencia
from barreiras.rotulagem import rotular
from barreiras.financeiro import simular
from barreiras.estatistica import comparar,incerteza_financeira
from barreiras.configuracao import carregar


class AuditoriaTest(unittest.TestCase):
    def test_rotulador_independente_com_lacunas_gaps_e_toques(self):
        rng=np.random.default_rng(31)
        n=2000
        p=np.exp(np.cumsum(rng.normal(0,.002,n)))*100
        m=np.column_stack([p,p*1.003,p*.997,p,np.ones(n),np.ones(n)])
        m[700:705]=np.nan;m[1000:1010,5]=0
        entradas=np.arange(1,1900,7);d=rng.uniform(.001,.08,len(entradas))
        y,s,k,precos,amb,mot=rotular(m,entradas,d,60)
        for i,e in enumerate(entradas):
            r=rotulo_referencia(m,int(e),d[i],1)
            self.assertEqual(r[0],y[i])
            if y[i]>=0:
                self.assertEqual(r[1],s[i]);self.assertAlmostEqual(r[2],precos[i]);self.assertEqual(r[3],amb[i])

    def test_auditoria_independente_rejeita_ledger_adulterado(self):
        m=np.full((1440,6),100.);m[:,4:]=1
        m[30,1]=120;m[160,2]=80
        datas=pd.date_range('2023-01-01',periods=20,freq='h',tz='UTC')
        e=np.arange(20)*60+1;d=np.full(20,.1)
        y,s,k,p,amb,mot=rotular(m,e,d,60)
        primeiro=int(datas[0].timestamp()//60)
        q=pd.DataFrame({'origem_utc':datas,'entrada_utc':datas+pd.Timedelta(minutes=1),
            'saida_utc':pd.to_datetime((primeiro+s)*60,unit='s',utc=True),'entrada_indice':e,'distancia':d,
            'horizonte':1,'classe':y,'saida_indice':s,'saida_conhecida_indice':k,'preco_entrada':100.,
            'preco_saida':p,'ambiguo':amb,'motivo_nao_observado':mot,'p2':.9})
        fim=datas[0]+pd.Timedelta(days=1);limites=(None,None,datas[0],fim)
        for opcoes in ({},{'agravado':True},{'superior_ambiguo':True},{'filtro':False}):
            r,o,c=simular(q,m,primeiro,datas[0],fim,**opcoes)
            auditar_financeiro(q,m,primeiro,limites,r,o,c,**opcoes)
            adulterado=o.copy();adulterado.loc[0,'quantidade']*=2
            with self.assertRaisesRegex(ValueError,'Contabilidade'):
                auditar_financeiro(q,m,primeiro,limites,r,adulterado,c,**opcoes)

    def test_intervalos_nao_inventam_ganho_sem_diferenca(self):
        datas=pd.date_range('2023-01-01',periods=24*90,freq='h',tz='UTC')
        q=pd.DataFrame({'origem_utc':datas,'classe':np.arange(len(datas))%3,'p0':.2,'p1':.3,'p2':.5})
        r=comparar(q,q)
        self.assertEqual(r['diferenca_log_loss'],0)
        self.assertEqual(r['intervalos']['14'],[0.,0.])
        curva=pd.DataFrame({'minuto_utc':datas.as_unit('s').astype('int64')//60,'patrimonio':10000.})
        self.assertEqual(incerteza_financeira(curva)['intervalos']['14']['retorno_liquido'],[0.,0.])

    def test_contrato_rejeita_final_e_campos_ignorados(self):
        raiz=Path(__file__).resolve().parents[1]
        original=json.loads((raiz/'configuracoes/ciclo_001.json').read_text())
        with tempfile.TemporaryDirectory() as pasta:
            p=Path(pasta)/'c.json'
            for alteracao in ({'folds':['B1']},{'campo_inventado':7},{'backend':'fallback'}):
                c=copy.deepcopy(original);c.update(alteracao);p.write_text(json.dumps(c))
                with self.assertRaises(ValueError):
                    carregar(p)


if __name__=='__main__':
    unittest.main()
