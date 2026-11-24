from .test_continuidade_diaria import Continuidade
from simulacao_operacoes.continuidade_diaria.simulador import simular
from simulacao_operacoes.continuidade_diaria.auditoria_grade import conferir
import numpy as np


class GradeInteira(Continuidade):
    def rodar(self,m,c,t,prev,modo,agenda=None):
        filtrar=modo!='agenda'
        r,v=simular(t,np.array(prev),np.full(len(t),100.),m,c,modo,agenda=agenda,filtrar_ordens=filtrar)
        conferir(r,v,m,c,modo,t,np.array(prev),np.full(len(t),100.),None,agenda,filtrar_ordens=filtrar)
        return r,v
    def test_xrp_sem_funding_em_posicao_zerada(self):
        m,c,t=self.base();m['negocio'][:]=.5;m['marca'][:]=.5
        m['negocio'][1441:]=.50001;m['marca'][1441:]=.50001;m['funding_preco'][:]=.5
        c.update(tick_preco=.0001,passo_quantidade=.1,nocional_minimo=5.)
        p=np.array([.51,.51,.5]);u=np.full(3,.5)
        r,v=simular(t,p,u,m,c,'liquida');conferir(r,v,m,c,'liquida',t,p,u,None)
        self.assertEqual(r['dias'][-1]['quantidade'],0.);self.assertEqual(len(r['funding']),2)
