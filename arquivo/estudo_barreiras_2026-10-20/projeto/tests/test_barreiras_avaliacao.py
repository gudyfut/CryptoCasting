import unittest
import numpy as np
import pandas as pd

from barreiras.configuracao import FOLDS
from barreiras.particoes import separar
from barreiras.financeiro import retorno_limite,simular
from barreiras.rotulagem import rotular


class TemporalTest(unittest.TestCase):
    def test_purga_maxima_independe_toque_precoce(self):
        datas=pd.date_range('2021-01-01','2024-01-01',freq='h',inclusive='left',tz='UTC')
        q=pd.DataFrame({'origem_utc':datas,'indice_hora':np.arange(len(datas)),
            'expiracao_maxima_utc':datas+pd.Timedelta(hours=168,minutes=1),
            'expiracao_utc':datas+pd.Timedelta(hours=1,minutes=1),'classe':np.arange(len(datas))%3,
            'ambiguo':False,'saida_utc':datas+pd.Timedelta(minutes=2)})
        for nome in ('DB1','DB2','DB3','DB4'):
            b=separar(q,np.ones(len(q),bool),nome)
            limites=FOLDS[nome].limites()
            for k,a,fim in zip(('treino','validacao','teste'),limites[:-1],limites[1:]):
                self.assertTrue((b[k].origem_utc>=a).all())
                self.assertTrue((b[k].expiracao_maxima_utc<fim).all())
                self.assertTrue((b[k].origem_utc<fim-pd.Timedelta(hours=168)).all())
            self.assertGreater(len(b['operacional']),len(b['teste']))


class FinanceiroTest(unittest.TestCase):
    def base(self):
        minutos=np.full((300,6),100.);minutos[:,4:]=1
        tempos=pd.date_range('2023-01-01',periods=3,freq='h',tz='UTC')
        e=np.array([1,61,121]);d=np.full(3,.1)
        y,s,k,p,amb,m=rotular(minutos,e,d,60)
        q=pd.DataFrame({'origem_utc':tempos,'entrada_utc':tempos+pd.Timedelta(minutes=1),
            'saida_utc':tempos+pd.Timedelta(minutes=61),'entrada_indice':e,'distancia':d,
            'horizonte':1,'classe':y,'saida_indice':s,'saida_conhecida_indice':k,
            'preco_entrada':100.,'preco_saida':p,'ambiguo':amb,'motivo_nao_observado':m,'p2':.9})
        primeiro=int(tempos[0].timestamp()//60)
        return q,minutos,primeiro,tempos[0],tempos[0]+pd.Timedelta(minutes=300)

    def test_uma_posicao_sem_reentrada_retroativa(self):
        resumo,ordens,curva=simular(*self.base())
        self.assertEqual(resumo['operacoes'],2)
        self.assertLess(resumo['retorno_liquido'],0)
        self.assertTrue((ordens.fracao<=1).all())

    def test_custo_e_risco_nominal(self):
        q,m,a,i,f=self.base()
        m[5,2]=80
        y,s,k,p,amb,mot=rotular(m,np.array([1]),np.array([.1]),60)
        q=q.iloc[:1].copy()
        q['classe']=y;q['saida_indice']=s;q['saida_conhecida_indice']=k;q['preco_saida']=p
        r,o,c=simular(q,m,a,i,f)
        self.assertAlmostEqual(r['capital_final'],9900.,places=8)
        self.assertGreater(r['taxas'],0)
        agravado,_,_=simular(q,m,a,i,f,agravado=True)
        self.assertLess(agravado['capital_final'],r['capital_final'])

    def test_nao_filtra_futuro_inobservavel(self):
        q,m,a,i,f=self.base();q=q.iloc[:1].copy();q['classe']=-1;q['motivo_nao_observado']=2
        r,_,_=simular(q,m,a,i,f)
        self.assertEqual(r['status'],'nao_auditavel');self.assertIsNone(r['retorno_liquido'])
        q['p2']=.1
        r,_,_=simular(q,m,a,i,f)
        self.assertEqual(r['status'],'auditavel');self.assertEqual(r['operacoes'],0)

    def test_ruim_e_bom_mantem_formulas_de_custo(self):
        self.assertLess(retorno_limite(.001),0)
        self.assertLess(retorno_limite(.01,False),-.01)


if __name__=='__main__':
    unittest.main()
