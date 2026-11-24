from copy import deepcopy
import unittest
import numpy as np
from infraestrutura.artefatos import RAIZ, ler_json
from experimentos.fechamento_ramos_diarios.contratos import CFG, conferir, receita, configuracao_moeda, ordem_trabalhos
from experimentos.fechamento_ramos_diarios.avaliacao import contrastar


class Contratos(unittest.TestCase):
    def setUp(self):
        self.c=ler_json(CFG)
        p=self.c['referencia_continuidade']
        self.antigas=ler_json(RAIZ/p['pasta']/'congelamento.json')['moedas']

    def test_somente_alteracoes_autorizadas(self):
        self.assertTrue(conferir(self.c,self.antigas))
        for caminho,valor in [('taxa',.001),('epocas',201),('lote',64),('parada_antecipada',True)]:
            c=deepcopy(self.c);c['moedas']['BTCUSDT']['treinamento'][caminho]=valor
            with self.assertRaises(AssertionError):conferir(c,self.antigas)

    def test_guardas_grade_populacao(self):
        for chave,valor in [('seeds',[42]),('max_ajustes_cientificos',13),('slippage_cenarios',[.0005])]:
            c=deepcopy(self.c);c[chave]=valor
            with self.assertRaises(AssertionError):conferir(c,self.antigas)
        c=deepcopy(self.c);c['moedas']['BTCUSDT']['periodos']['teste'][1]='2027-01-01'
        with self.assertRaises(AssertionError):conferir(c,self.antigas)

    def test_controles_antecedem_demais_seeds(self):
        ordem=ordem_trabalhos(self.c)
        self.assertEqual(sum(not j['controle'] for j in ordem),12)
        self.assertEqual(sum(j['controle'] for j in ordem),8)
        for simbolo in self.c['moedas']:
            trabalhos=[j for j in ordem if j['simbolo']==simbolo]
            self.assertEqual([j['seed'] for j in trabalhos],[42,42,42,17,2026])
            self.assertEqual([j['controle'] for j in trabalhos],[True,False,True,False,False])

    def test_fatores_sem_mutar_receita(self):
        cfg=configuracao_moeda(self.c,'BTCUSDT');antes=deepcopy(cfg)
        for v,ramos,decay in [('A',True,.001),('B',True,0.),('L',False,.001),('L0',False,0.)]:
            r=receita(cfg,v)
            self.assertEqual(r['ramos_mamba'],ramos)
            self.assertEqual(r['treinamento']['weight_decay'],decay)
            self.assertEqual(r['eixo'],'canais')
        self.assertEqual(cfg,antes)

    def test_interacao_pareada_sem_confundir_sinal(self):
        c=configuracao_moeda(self.c,'BTCUSDT')
        c['bootstrap']={'seed':4,'replicas':30,'blocos':[7,14,28]}
        a={v:np.full((3,60),n,dtype=float) for v,n in [('A',7),('L',5),('B',6),('L0',1)]}
        r=contrastar(a,{},c,False)
        self.assertEqual(r['A_menos_L']['14']['media'],2.)
        self.assertEqual(r['B_menos_L0']['14']['media'],5.)
        self.assertEqual(r['interacao']['14']['media'],3.)
        self.assertEqual(r['interacao']['14']['ic95'],[3.,3.])


if __name__=='__main__':unittest.main()
