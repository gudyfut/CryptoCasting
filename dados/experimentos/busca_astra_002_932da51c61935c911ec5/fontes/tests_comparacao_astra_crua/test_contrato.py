import copy
import unittest
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ
from experimentos.comparacao_astra_crua.contrato import grade,ASTRA,CRUA,SEEDS,FINAIS,validar_pedido
from experimentos.comparacao_astra_crua.publicacao import intervalo

class Contrato(unittest.TestCase):
    def test_grade_orcamento_controles(self):
        g=grade();self.assertEqual(len(g),34)
        self.assertEqual([j['tipo'] for j in g[:3]],['controle_astra','crua','controle_crua'])
        principais=[(x['bloco'],x['seed']) for x in g if x['tipo']=='crua']
        self.assertEqual(principais,[(b,s) for b in FINAIS for s in SEEDS]);self.assertEqual(len(set(principais)),32)
        self.assertEqual({k for k in ASTRA if ASTRA[k]!=CRUA[k]},{'representacao','contexto'})
    def pedido(self):
        p=RAIZ/'dados/experimentos/teste_sem_execucao';ptr={'id':'sintetico','pasta':p.relative_to(RAIZ).as_posix()}
        q={'numero':1,'execucao':ptr,'item':grade()[0], 'destino':(p/'controle_astra/B1_42').relative_to(RAIZ).as_posix(),'limite_segundos':2700}
        return p,ptr,q
    def test_pedido_legitimo(self):
        p,ptr,q=self.pedido();self.assertEqual(validar_pedido(q,p,ptr,[dict(q,status='iniciado')]),p/'controle_astra/B1_42')
    def test_repeticao_destino_receita_orcamento_bloqueados(self):
        p,ptr,q=self.pedido()
        with self.assertRaises(AssertionError):validar_pedido(q,p,ptr,[dict(q,status='concluido')])
        for campo,valor in [('destino','fora'),('numero',35),('item',dict(grade()[0],seed=99)),('limite_segundos',99999)]:
            z=copy.deepcopy(q);z[campo]=valor
            with self.assertRaises(AssertionError):validar_pedido(z,p,ptr,[dict(z,status='iniciado')])
    def test_intervalo_constante_e_nulo(self):
        dias=pd.date_range('2020-01-01',periods=96,freq='h',tz='UTC')
        blocos={b:{'origens':dias,'astra':np.ones((8,96)),'crua':np.full((8,96),2.),'naive':np.ones((8,96))} for b in FINAIS}
        q=intervalo(blocos,'astra','crua',replicas=20);self.assertEqual(q['diferenca_mse'],-1.)
        for r in q['intervalos'].values():self.assertEqual(r['ic98_333_bonferroni_tres_contrastes'],[-1.,-1.])
        q=intervalo(blocos,'astra','naive',replicas=20);self.assertEqual(q['diferenca_mse'],0.)
    def test_peso_igual_blocos(self):
        blocos={}
        for i,b in enumerate(FINAIS):
            n=24*(i+1);blocos[b]={'origens':pd.date_range('2020-01-01',periods=n,freq='h',tz='UTC'),
                'astra':np.full((8,n),float(i)), 'crua':np.zeros((8,n))}
        self.assertEqual(intervalo(blocos,'astra','crua',replicas=20)['diferenca_mse'],1.5)

if __name__=='__main__':unittest.main()
