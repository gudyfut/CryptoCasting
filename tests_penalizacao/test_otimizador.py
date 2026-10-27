import ast
import copy
import unittest
from pathlib import Path
import torch
from previsao24.arquivos import RAIZ,ler_json
from previsao24.redes import criar
from experimento_penalizacao.otimizador import criar_otimizador,grupos_parametros


class PenalizacaoTeste(unittest.TestCase):
    def setUp(self):
        self.c=ler_json(RAIZ/'configuracoes/retorno24_001.json')

    def test_cobertura_ordem_e_excecoes(self):
        r=criar('mamba',self.c); g=grupos_parametros(r,.001)
        self.assertEqual([id(p) for x in g for p in x['params']],[id(p) for p in r.parameters()])
        nomes=[n for x in g if x['weight_decay']==0 for n in x['nomes']]
        self.assertEqual(nomes,['blocos.0.A_log','blocos.0.D','blocos.1.A_log','blocos.1.D'])
        self.assertEqual(sum(p.numel() for x in g if x['weight_decay']==0 for p in x['params']),2176)
        self.assertEqual(sum(p.numel() for x in g for p in x['params']),20129)

    def test_criacao_nao_muda_rng_ou_pesos(self):
        r=criar('mamba',self.c); rng=torch.get_rng_state().clone(); pesos=copy.deepcopy(r.state_dict())
        criar_otimizador(r,self.c['treino'])
        self.assertTrue(torch.equal(rng,torch.get_rng_state()))
        for n,p in r.state_dict().items(): self.assertTrue(torch.equal(p,pesos[n]))

    def test_gradiente_zero_isola_penalizacao(self):
        r=criar('mamba',self.c)
        for p in r.parameters(): p.data.fill_(2.0); p.grad=torch.zeros_like(p)
        o=criar_otimizador(r,self.c['treino']); o.step()
        esperado=2*(1-.0002*.001)
        for p in r.parameters():
            valor=2.0 if getattr(p,'_no_weight_decay',False) else esperado
            torch.testing.assert_close(p,torch.full_like(p,valor),rtol=0,atol=0)

    def test_lstm_permanece_um_grupo_uniforme(self):
        r=criar('lstm',self.c); g=grupos_parametros(r,.001)
        self.assertEqual(len(g),1); self.assertEqual(g[0]['weight_decay'],.001)

    def test_treinador_so_troca_otimizador(self):
        a=(RAIZ/'previsao24/treino.py').read_text(encoding='utf-8')
        b=(RAIZ/'experimento_penalizacao/treino.py').read_text(encoding='utf-8')
        a=a.replace('from .arquivos import','from previsao24.arquivos import').replace('from .metricas import','from previsao24.metricas import').replace('from .redes import','from previsao24.redes import')
        a=a.replace('from previsao24.redes import criar','from previsao24.redes import criar\nfrom .otimizador import criar_otimizador')
        a=a.replace("otimizador=torch.optim.AdamW(rede.parameters(),lr=t['taxa_aprendizado'],weight_decay=t['weight_decay'],betas=(.9,.999),eps=1e-8)", 'otimizador=criar_otimizador(rede,t)')
        self.assertEqual(ast.dump(ast.parse(a)),ast.dump(ast.parse(b)))


if __name__=='__main__': unittest.main()
