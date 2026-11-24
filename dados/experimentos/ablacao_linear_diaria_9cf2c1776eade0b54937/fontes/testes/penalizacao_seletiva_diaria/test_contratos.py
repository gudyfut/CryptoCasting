import ast
import copy
import unittest
from infraestrutura.artefatos import RAIZ,ler_json
from experimentos.penalizacao_seletiva_diaria.contratos import conferir_configuracao,receita


class Contratos(unittest.TestCase):
    def setUp(self):
        self.c=ler_json(RAIZ/'configuracoes/penalizacao_seletiva_diaria_001.json')
        self.anterior=ler_json(RAIZ/'configuracoes/eixo_temporal_diario_001.json')

    def test_unico_fator(self):
        self.assertTrue(conferir_configuracao(self.c,self.anterior))
        a,s=receita(self.c,'A'),receita(self.c,'S')
        for c in (a,s):
            c['treinamento'].pop('politica_penalizacao');c['treinamento'].pop('penalizacao')
        self.assertEqual(a,s)
        for campo,valor in [('taxa',.001),('epocas',201),('weight_decay',0),('lote',64)]:
            c=copy.deepcopy(self.c);c['treinamento'][campo]=valor
            with self.assertRaises(AssertionError):conferir_configuracao(c,self.anterior)
        c=copy.deepcopy(self.c);c['operacoes']['slippage_por_lado']=.0005
        with self.assertRaises(AssertionError):conferir_configuracao(c,self.anterior)

    def test_treinador_mesmo_algoritmo(self):
        original=(RAIZ/'codigo/experimentos/sem_penalizacao_diaria/treinamento.py').read_text(encoding='utf8')
        novo=(RAIZ/'codigo/experimentos/penalizacao_seletiva_diaria/treinamento.py').read_text(encoding='utf8')
        novo=novo.replace('opt=construir_otimizador(rede,cfg,d)',"opt=torch.optim.Adam(rede.parameters(),lr=cfg['taxa'],weight_decay=cfg['weight_decay'])")
        novo=novo.replace("epoca in c['observacao_epocas']",'epoca in EPOCAS').replace('grad=gradientes(rede,opt)',"grad=gradientes(rede,cfg['weight_decay'])")
        fun=lambda s:next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name=='ajustar')
        self.assertEqual(ast.dump(fun(original)),ast.dump(fun(novo)))

    def test_avaliador_mesmas_operacoes(self):
        original=(RAIZ/'codigo/experimentos/eixo_temporal_diario/avaliacao.py').read_text(encoding='utf8')
        novo=(RAIZ/'codigo/experimentos/penalizacao_seletiva_diaria/avaliacao.py').read_text(encoding='utf8')
        novo=novo.replace("variante == 'A'","variante in ('A','B')").replace("'recargas_validacao_exatas':6","'recargas_validacao_exatas':12").replace("'previsoes_herdadas_exatas_validacao_teste':6","'previsoes_herdadas_exatas_validacao_teste':12")
        self.assertEqual(ast.dump(ast.parse(original)),ast.dump(ast.parse(novo)))


if __name__=='__main__':unittest.main()
