import ast
import unittest
import torch
from torch import nn
from previsao24.arquivos import RAIZ, ler_json
from previsao24.treino import fixar_seed
from experimento_normalizacao.redes import criar, RedeMambaPreNormalizada
from experimento_penalizacao.otimizador import descrever_grupos
from previsao24.configuracao import celulas


class ContratoNormalizacao(unittest.TestCase):
    def setUp(self):
        self.c = ler_json(RAIZ / 'configuracoes/retorno24_001.json')

    def test_mesma_inicializacao_rng_parametros_e_grupos(self):
        for seed in self.c['seeds']:
            fixar_seed(seed)
            pos = criar('mamba', {**self.c, 'normalizacao_mamba': 'pos'})
            rng = torch.get_rng_state().clone()
            fixar_seed(seed)
            pre = criar('mamba', {**self.c, 'normalizacao_mamba': 'pre'})
            self.assertTrue(torch.equal(rng, torch.get_rng_state()))
            self.assertEqual(list(pos.state_dict()), list(pre.state_dict()))
            for n, p in pos.state_dict().items():
                self.assertTrue(torch.equal(p, pre.state_dict()[n]), n)
            self.assertEqual(sum(p.numel() for p in pre.parameters()), 20129)
            self.assertEqual(descrever_grupos(pos, self.c['treino']), descrever_grupos(pre, self.c['treino']))

    def test_treinador_identico_exceto_fabrica(self):
        antigo = (RAIZ / 'experimento_penalizacao/treino.py').read_text(encoding='utf-8')
        novo = (RAIZ / 'experimento_normalizacao/treino.py').read_text(encoding='utf-8')
        antigo = antigo.replace('from previsao24.redes import criar', 'from .redes import criar')
        antigo = antigo.replace('from .otimizador import criar_otimizador', 'from experimento_penalizacao.otimizador import criar_otimizador')
        self.assertEqual(ast.dump(ast.parse(antigo)), ast.dump(ast.parse(novo)))

    def test_forward_normaliza_antes_e_preserva_residual(self):
        # Bloco linear não comutativo permite verificar a ordem em CPU.
        rede = criar('mamba', {**self.c, 'normalizacao_mamba': 'pre'})
        rede.blocos = nn.ModuleList([nn.Linear(32, 32) for _ in rede.blocos])
        rede.eval()
        x = torch.randn(3, 24, 1)
        esperado = rede.projecao(x)
        for bloco, norma in zip(rede.blocos, rede.normas):
            esperado = esperado + bloco(norma(esperado))
        esperado = rede.saida(rede.norma_final(rede.dropout(esperado))[:, -1, :]).squeeze(-1)
        torch.testing.assert_close(rede(x), esperado, rtol=0, atol=0)
        errado = rede.projecao(x)
        for bloco, norma in zip(rede.blocos, rede.normas):
            errado = norma(errado + bloco(errado))
        errado = rede.saida(rede.norma_final(rede.dropout(errado))[:, -1, :]).squeeze(-1)
        self.assertFalse(torch.allclose(esperado, errado))

    def test_so_mamba_e_posicao_explicita(self):
        with self.assertRaises(ValueError): criar('lstm', {**self.c, 'normalizacao_mamba': 'pre'})
        with self.assertRaises(KeyError): criar('mamba', self.c)
        with self.assertRaises(ValueError): criar('mamba', {**self.c, 'normalizacao_mamba': 'outra'})

    def test_grade_exata_e_controles_predefinidos(self):
        nova = ler_json(RAIZ / 'configuracoes/normalizacao_mamba_001.json')
        grade = [x for f in ('desenvolvimento', 'avaliacao') for x in celulas(self.c, f) if x['modelo'] == 'mamba']
        self.assertEqual(len(grade), nova['ajustes_prenorm'])
        self.assertEqual(len(grade), 384)
        self.assertEqual([x['contexto'] for x in nova['controles_reexecutados']], [24, 336])
        for x in nova['controles_reexecutados']: self.assertIn(x, grade)

    def test_rejeita_cobertura_de_mesmo_tamanho_mas_errada(self):
        from experimento_normalizacao.ciclo import conferir_grade_mamba
        from previsao24.arquivos import identidade
        chaves={identidade(x)[:20]: None for f in ('desenvolvimento','avaliacao') for x in celulas(self.c,f) if x['modelo']=='mamba'}
        conferir_grade_mamba(chaves,self.c)
        chaves.pop(next(iter(chaves)))
        chaves['inesperada']=None
        with self.assertRaises(ValueError): conferir_grade_mamba(chaves,self.c)

    def test_heranca_troca_so_mamba_pelo_comparador_corrigido(self):
        from experimento_normalizacao.analise import combinar_referencias
        from previsao24.arquivos import identidade
        grade=[x for f in ('desenvolvimento','avaliacao') for x in celulas(self.c,f)]
        grade += [{'par':p,'fold':f,'modelo':m} for p in self.c['pares'] for f in self.c['folds_desenvolvimento']+self.c['folds_avaliacao'] for m in ('arima','naive')]
        iniciais={identidade(x)[:20]:'original' for x in grade}
        comparador={identidade(x)[:20]:'corrigido' for x in grade if x['modelo']=='mamba'}
        unidos=combinar_referencias(iniciais,comparador,self.c)
        self.assertEqual(len(unidos),832)
        for x in grade:
            self.assertEqual(unidos[identidade(x)[:20]], 'corrigido' if x['modelo']=='mamba' else 'original')
        self.assertEqual(set(iniciais.values()),{'original'})


if __name__ == '__main__': unittest.main()
