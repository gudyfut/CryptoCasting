import ast
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from infraestrutura.artefatos import salvar_json
from experimento_otimizador import ciclo


class Ablacao(unittest.TestCase):
    def test_fator_unico_e_rejeicao_de_taxa(self):
        c=ciclo.configuracao();self.assertEqual(c['otimizador']['nome'],'AdamW')
        self.assertEqual(c['treino']['taxa_aprendizado'],.01)
        ler=ciclo.ler_json
        def mudar(p):
            v=ler(p)
            if Path(p).name==Path(ciclo.CONFIG).name:v['treino']['taxa_aprendizado']=.001
            return v
        with patch.object(ciclo,'ler_json',side_effect=mudar),self.assertRaises(ValueError):ciclo.configuracao()
        self.assertTrue(ciclo.equivalencia_treinador()['ast_demais_instrucoes_identico'])

    def test_adam_sem_decay_equivale_e_com_decay_difere(self):
        import torch
        for wd in (0.,.001):
            a=torch.nn.Parameter(torch.tensor([1.,-2.],dtype=torch.float64))
            b=torch.nn.Parameter(a.detach().clone())
            oa=torch.optim.Adam([a],lr=.01,weight_decay=wd)
            ob=torch.optim.AdamW([b],lr=.01,weight_decay=wd)
            for _ in range(3):
                a.grad=torch.tensor([.0001,-.0002],dtype=torch.float64);b.grad=a.grad.clone();oa.step();ob.step()
            if wd==0:self.assertTrue(torch.equal(a,b))
            else:self.assertGreater(float((a-b).detach().abs().max()),1e-4)

    def test_inicializacao_dimensoes_decay_e_atualizacao(self):
        import torch
        from treinamento.otimizacao import fixar_seed
        from modelos.consumo import ConsumoModelos
        from tests_modelos.apoio import conjunto
        from experimento_cryptomamba.modelo import criar_rede
        from experimento_otimizador.treino import otimizador
        consumo=ConsumoModelos(conjunto(),'sintetico');c=ciclo.configuracao()
        fixar_seed(42);a=criar_rede(consumo.especificacao,c)
        fixar_seed(42);b=criar_rede(consumo.especificacao,ciclo.anterior.configuracao())
        self.assertTrue(all(torch.equal(v,b.state_dict()[k]) for k,v in a.state_dict().items()))
        opt,grupos=otimizador(a,c);self.assertIsInstance(opt,torch.optim.AdamW)
        marcados={n for n,p in a.named_parameters() if getattr(p,'_no_weight_decay',False)}
        self.assertEqual(len(marcados),24)
        self.assertTrue(all(g['weight_decay']==(0. if g['nome'] in marcados else .001) for g in grupos))
        pesos={k:v.detach().clone() for k,v in a.state_dict().items()}
        x=torch.randn(2,168,5,device='cuda');y=a.train()(x)
        self.assertEqual(tuple(y.shape),(2,));self.assertEqual(sum(p.numel() for p in a.parameters()),139317)
        loss=(y**2).mean();loss.backward();self.assertTrue(all(p.grad is None or torch.isfinite(p.grad).all() for p in a.parameters()))
        opt.step();self.assertTrue(any(not torch.equal(v,a.state_dict()[k]) for k,v in pesos.items()))

    def test_autorizacao_nao_amplia_orcamento(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'a.json';a={'execucao':'id','seeds':ciclo.SEEDS,'ajustes_reais_total':6,'abordagem':'cryptomamba_adamw','mensagem_usuario':'fixture'}
            salvar_json(p,a);ciclo.validar_autorizacao(p,'id')
            a['ajustes_reais_total']=12;salvar_json(p,a)
            with self.assertRaises(ValueError):ciclo.validar_autorizacao(p,'id')

    def test_executor_para_em_falha_e_nao_repete_encerrado(self):
        import contextlib
        c=ciclo.configuracao()
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);salvar_json(p/'progresso.json',{'status':'preparado'})
            f={'id':'id','contrato':{'configuracao':c}};consumo=type('C',(),{'especificacao':type('E',(),{'identidade':'fixture'})()})()
            with patch.object(ciclo,'conferir_execucao',return_value=(p,f,consumo,{}, {},p)),patch.object(ciclo,'validar_autorizacao',return_value={}),patch.object(ciclo,'exclusividade',return_value=contextlib.nullcontext()),patch.object(ciclo,'ajustar',side_effect=RuntimeError('fixture')) as ajuste:
                with self.assertRaises(RuntimeError):ciclo.executar(p/'autorizacao.json')
                self.assertEqual(ajuste.call_count,1)
                self.assertEqual(ciclo.ler_json(p/'progresso.json')['status'],'interrompido')
                self.assertTrue((p/'celulas/cryptomamba_adamw_42/tentativa_001/falha.json').exists())
                salvar_json(p/'progresso.json',{'status':'concluido'})
                with self.assertRaises(ValueError):ciclo.executar(p/'autorizacao.json',True)
                self.assertEqual(ajuste.call_count,1)
