import ast
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from infraestrutura.artefatos import salvar_json
from experimento_otimizador import ciclo


class Ablacao(unittest.TestCase):
    def test_publicacao_separa_65_series_e_54_carteiras_artificiais(self):
        import copy
        import numpy as np
        import pandas as pd
        from tests_cryptomamba.test_adaptacao import refs_sinteticas
        from tests_modelos.apoio import conjunto
        from modelos.consumo import ConsumoModelos
        from experimento_otimizador import publicacao
        refs=refs_sinteticas();base=refs['estado16_42']
        refs.update({f'cryptomamba_{s}':base for s in ciclo.SEEDS})
        self.assertEqual(len(refs),59)
        c=ciclo.configuracao();consumo=ConsumoModelos(conjunto(),'sintetico')
        c['divisao']={k:[str(pd.Timestamp(t).date()) for t in v] for k,v in consumo._conjunto.contrato['divisao'].items()}
        c['bootstrap']['replicas']=5
        fake={'retorno_auditavel':True,'risco_auditavel':True,'retorno_liquido':0.,'drawdown':0.,'capital_final':10000.,
              'entradas_planejadas':0,'custos_observados':0.,'minutos_expostos_planejados':0}
        minimos=np.ones((31*1440,6));minimos[:,:4]=100
        primeiro=int(pd.Timestamp('2021-01-01T00:00Z').timestamp()//60)
        for b in ('validacao','teste'):
            q=pd.read_parquet(base/f'previsoes_{b}.parquet')
            for row in q.itertuples():
                i=int(pd.Timestamp(row.origem_utc).timestamp()//60)-1-primeiro
                minimos[i,3]=row.close
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);ant=p/'anterior';ant.mkdir()
            res={k:{'metricas':ciclo.ler_json(t/'resultado.json')['metricas'],
                    'spot':{perfil:fake for perfil in ('base','agravado','bruto_mesmos_sinais')},
                    'tentativa_origem':t.relative_to(ciclo.RAIZ).as_posix()}
                 for k,t in refs.items()}
            salvar_json(ant/'resultados.json',{'por_ajuste':res})
            with patch.object(publicacao,'auditar_checkpoint',return_value={'natureza':'fixture'}),\
                 patch.object(publicacao,'carregar_minutos',return_value=(minimos,primeiro)),\
                 patch.object(publicacao,'carregar',return_value=(minimos,primeiro)),\
                 patch.object(publicacao,'spot_r0',side_effect=lambda *a,**k:(copy.deepcopy(fake),[],[])):
                pub,r=publicacao.publicar(p,{'id':'fixture','contrato':{'configuracao':c}},consumo._conjunto.partes,
                                         {s:base for s in ciclo.SEEDS},refs,ant)
            self.assertEqual((r['novos'],r['herdados'],len(r['por_ajuste'])),(6,59,65))
            self.assertEqual(len(r['carteiras']),54)
            self.assertEqual(r['medias']['teste']['adamw_seis']['n_seeds'],6)
            self.assertEqual(r['medias']['teste']['lstm_tres']['n_seeds'],3)
            self.assertEqual(len(list((pub/'carteira').rglob('verificacao.json'))),54)
            (p/'docs').mkdir()
            with patch.object(publicacao,'RAIZ',p):
                publicacao.relatar(r)
                self.assertTrue((p/'docs/resultados_otimizador_cryptomamba.md').exists())

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
            inicio=a.detach().clone();grad=torch.tensor([-.0001,.0002],dtype=torch.float64)
            a.grad=grad.clone();b.grad=grad.clone();oa.step();ob.step()
            g_adam=grad+wd*inicio
            esperado_adam=inicio-.01*g_adam/(g_adam.abs()+1e-8)
            esperado_adamw=inicio*(1-.01*wd)-.01*grad/(grad.abs()+1e-8)
            torch.testing.assert_close(a,esperado_adam,rtol=1e-12,atol=1e-12)
            torch.testing.assert_close(b,esperado_adamw,rtol=1e-12,atol=1e-12)
            if wd==0:self.assertTrue(torch.equal(a,b))
            else:self.assertGreater(float((a-b).detach().abs().max()),.01)

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
