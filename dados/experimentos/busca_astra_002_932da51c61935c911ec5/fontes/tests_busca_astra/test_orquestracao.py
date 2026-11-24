import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from experimentos.busca_astra.ciclo import Coordenador
from experimentos.busca_astra.contrato import REFERENCIA
from experimentos.busca_astra.agente import validar_contexto

class Orquestracao(unittest.TestCase):
    def test_prompt_rejeita_teste_e_carteiras(self):
        validar_contexto({'referencia':[{'validacao':{'mse':1.}}]})
        for nome in ['teste','carteiras','finalista']:
            with self.assertRaises(ValueError):validar_contexto({'x':[{'oculto':{nome:1}}]})

    def rodar_falso(self,ganho):
        with tempfile.TemporaryDirectory() as tmp:
            c=Coordenador(Path(tmp),{'id':'sintetico'}, {'configuracao':{'selecao':{}},'ambiente_coordenador':{'codex':'fake'}})
            chamadas=[]
            def ajuste(r,b,s,grupo,controle=False):
                chamadas.append((b,s,grupo,controle))
                e=1. if r==REFERENCIA else ganho
                return {'bloco':b,'seed':s,'parametros':100,'validacao':{'mse':e,'mse_naive':1.}}
            receitas=[dict(REFERENCIA,contexto=24,estado=e,dropout=d) for e in [8,16,32,64] for d in [0.,.1,.2]]
            propostas=[{'acao':'experimentar','receita':r,'hipotese':'sintetica'} for r in receitas]
            with patch.object(c,'ajuste',side_effect=ajuste),patch.object(c,'estado'),patch.object(c,'checar'), \
                 patch.object(c,'encerrar',side_effect=lambda a,b:(a,b)), \
                 patch('experimentos.busca_astra.dados.carregar_candles',return_value=None), \
                 patch('experimentos.busca_astra.dados.Dados',return_value=None), \
                 patch('experimentos.busca_astra.dados.diagnostico',return_value={}), \
                 patch('experimentos.busca_astra.agente.consultar',side_effect=propostas) as agente, \
                 patch('experimentos.busca_astra.ciclo.controle_cpu',return_value={'aprovado':True}), \
                 patch('experimentos.busca_astra.publicacao.publicar') as pub:
                saida=c.executar()
                return chamadas,saida,agente.call_count,pub.call_count

    def test_teto108_controles_e_12consultas(self):
        chamadas,saida,n,pub=self.rodar_falso(.9)
        self.assertEqual(len(chamadas),108)
        self.assertEqual(n,12);self.assertEqual(pub,1)
        self.assertTrue(chamadas[1][3])
        final=[x for x in chamadas if x[2]=='final/candidata']
        self.assertEqual(len(final),32)
        ctrl=next(i for i,x in enumerate(chamadas) if x[2]=='controles/finalista')
        self.assertEqual(chamadas[ctrl-1],('B1',42,'final/candidata',False))
        self.assertEqual(chamadas[ctrl+1],('B1',17,'final/candidata',False))

    def test_sem_ganho_nao_abre_teste_final(self):
        chamadas,saida,n,pub=self.rodar_falso(1.1)
        self.assertEqual(len(chamadas),43)
        self.assertEqual(pub,0);self.assertEqual(saida[0],'concluido_sem_finalista')
        self.assertFalse(any(b.startswith('B') for b,s,g,ctrl in chamadas))

if __name__=='__main__':unittest.main()
