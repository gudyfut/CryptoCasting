import contextlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, ler_json, salvar_json
from experimentos.perda_huber import ciclo
from experimentos.perda_huber.perda import atualizar_lote, POLITICA


class Huber(unittest.TestCase):
    def test_fator_unico_e_ast(self):
        c = ciclo.configuracao()
        self.assertEqual(c['treino']['taxa_aprendizado'], .0002)
        self.assertTrue(ciclo.conferir_treinador()['acumulacao_igual'])
        original = ciclo.ler_json
        def alterar(p):
            r = original(p)
            if Path(p).name == Path(ciclo.CONFIG).name:
                r['treino']['taxa_aprendizado'] = .0001
            return r
        with patch.object(ciclo, 'ler_json', side_effect=alterar), self.assertRaises(ValueError):
            ciclo.configuracao()

    def test_formula_gradientes_juncao_e_extremos(self):
        import torch
        x = torch.tensor([-3., -1., -.5, 0., .5, 1., 3.], dtype=torch.float64, requires_grad=True)
        loss = 2 * torch.nn.functional.huber_loss(x, torch.zeros_like(x), delta=1., reduction='none')
        torch.testing.assert_close(loss, torch.tensor([5., 1., .25, 0., .25, 1., 5.], dtype=torch.float64))
        loss.sum().backward()
        torch.testing.assert_close(x.grad, torch.tensor([-2., -2., -1., 0., 1., 2., 2.], dtype=torch.float64))
        x = torch.tensor([-.999999, 0., .999999], dtype=torch.float64, requires_grad=True)
        a = 2 * torch.nn.functional.huber_loss(x, torch.zeros_like(x), delta=1., reduction='sum')
        b = (x ** 2).sum()
        torch.testing.assert_close(a, b)
        torch.testing.assert_close(torch.autograd.grad(a, x)[0], torch.autograd.grad(b, x)[0])

    def test_microbatch_ultimo_lote_e_equivalencia_mse(self):
        import torch, copy
        from treinamento.otimizacao import atualizar_lote as mse
        class Rede(torch.nn.Module):
            def __init__(self):
                super().__init__(); self.linear = torch.nn.Linear(2, 1).double()
            def forward(self, x):
                return self.linear(x).flatten()
        torch.manual_seed(42)
        a = Rede(); b = copy.deepcopy(a)
        x = torch.tensor([[.1,.2],[2.,-3.],[.2,.1],[-5.,2.],[.4,.1]], dtype=torch.float64)
        y = torch.tensor([.1,10.,.2,-9.,.3], dtype=torch.float64)
        oa, ob = (torch.optim.SGD(n.parameters(),lr=.01) for n in (a,b))
        atualizar_lote(a,oa,x,y,2,1e6,POLITICA)
        ob.zero_grad(); loss=2*torch.nn.functional.huber_loss(b(x),y,delta=1.,reduction='mean'); loss.backward(); ob.step()
        for u,v in zip(a.parameters(),b.parameters()): torch.testing.assert_close(u,v,rtol=1e-12,atol=1e-12)
        a=Rede(); b=copy.deepcopy(a); x=torch.zeros((5,2),dtype=torch.float64); y=a(x).detach()+.1
        oa, ob = (torch.optim.SGD(n.parameters(),lr=.01) for n in (a,b))
        atualizar_lote(a,oa,x,y,2,1e6,POLITICA); mse(b,ob,x,y,2,1e6)
        for u,v in zip(a.parameters(),b.parameters()): torch.testing.assert_close(u,v,rtol=1e-12,atol=1e-12)

    def test_contratos_nao_broadcast_nan_ou_delta_invalido(self):
        import torch
        a=torch.nn.Linear(2,1); o=torch.optim.AdamW(a.parameters(),lr=.0002); x=torch.ones((2,2)); y=torch.zeros(2)
        with self.assertRaises(ValueError): atualizar_lote(a,o,x,y,2,1.,POLITICA)
        with self.assertRaises(ValueError): atualizar_lote(a,o,x[:0],y[:0],2,1.,POLITICA)
        with self.assertRaises(ValueError): atualizar_lote(a,o,x,y,2,1.,dict(POLITICA,delta=0))
        class Saida(torch.nn.Module):
            def __init__(self): super().__init__(); self.p=torch.nn.Parameter(torch.tensor(0.))
            def forward(self,x): return self.p.expand(len(x))
        a=Saida();o=torch.optim.SGD(a.parameters(),lr=.01)
        with self.assertRaises(ValueError): atualizar_lote(a,o,x,torch.tensor([float('nan'),0.]),1,1.,POLITICA)

    def test_selecao_mse_independente_da_perda_treino(self):
        from treinamento.selecao import SelecaoEpoca
        s=SelecaoEpoca(2)
        for e,m in enumerate([3.,2.,4.,5.],1): s.observar(e,m)
        self.assertEqual(s.epoca,2); self.assertTrue(s.parar)

    def test_autorizacao_e_parada_em_falha(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);a={'execucao':'fixture','seeds':ciclo.SEEDS,'ajustes_reais_total':6,'abordagem':'mamba16_perda_huber','mensagem_usuario':'fixture'}
            salvar_json(p/'a.json',a);ciclo.validar_autorizacao(p/'a.json','fixture')
            with self.assertRaises(ValueError):ciclo.validar_autorizacao(p/'a.json','outro')
            salvar_json(p/'progresso.json',{'status':'preparado'})
            consumo=type('C',(),{'especificacao':type('E',(),{'identidade':'fixture'})()})();f={'id':'fixture','contrato':{'configuracao':ciclo.configuracao()}}
            with patch.object(ciclo,'conferir_execucao',return_value=(p,f,consumo,{},{})),patch.object(ciclo,'exclusividade',return_value=contextlib.nullcontext()),patch.object(ciclo,'ajustar',side_effect=RuntimeError('fixture')) as ajustar:
                with self.assertRaises(RuntimeError):ciclo.executar(p/'a.json')
                self.assertEqual(ajustar.call_count,1);self.assertEqual(ler_json(p/'progresso.json')['status'],'interrompido')
                salvar_json(p/'progresso.json',{'status':'concluido'})
                with self.assertRaises(ValueError):ciclo.executar(p/'a.json',True)
                self.assertEqual(ajustar.call_count,1)

    def test_publicacao59_e_54carteiras_com_dados_artificiais(self):
        import copy
        from tests_modelos.apoio import conjunto
        from modelos.consumo import ConsumoModelos
        from avaliacao.metricas import calcular
        from experimentos.perda_huber import publicacao as pub
        consumo=ConsumoModelos(conjunto(),'fixture');partes=consumo._conjunto.partes;c=ciclo.configuracao()
        c['divisao']={k:[str(pd.Timestamp(v).date()) for v in vs] for k,vs in consumo._conjunto.contrato['divisao'].items()};c['bootstrap']['replicas']=5
        ciclo.REG.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ciclo.REG) as tmp:
            p=Path(tmp);base=p/'referencia';base.mkdir();metricas={};minutos=np.ones((31*1440,6));minutos[:,:4]=100.
            primeiro=int(pd.Timestamp('2021-01-01T00:00Z').timestamp()//60)
            for b in ('validacao','teste','operacional'):
                q=partes[b].copy();q['previsao']=0.;q.to_parquet(base/f'previsoes_{b}.parquet',index=False)
                if b!='operacional':
                    metricas[b]=calcular(q.alvo,q.previsao)
                    for row in q.itertuples():minutos[int(pd.Timestamp(row.origem_utc).timestamp()//60)-1-primeiro,3]=row.close
            salvar_json(base/'resultado.json',{'metricas':metricas})
            keys=[f'estado{n}_{s}' for n in [8,16,32,64] for s in ciclo.SEEDS]+[f'taxa0001_estado{n}_{s}' for n in [8,16,32,64] for s in ciclo.SEEDS]+[f'lstm_{s}' for s in [17,42,2026]]+['naive','arima']
            refs={k:base for k in keys};fake={'retorno_auditavel':True,'risco_auditavel':True,'retorno_liquido':0.,'drawdown':0.,'capital_final':10000.,'entradas_planejadas':0,'custos_observados':0.,'minutos_expostos_planejados':0}
            anteriores={k:{'metricas':metricas,'spot':{x:fake for x in ['base','agravado','bruto_mesmos_sinais']},'tentativa_origem':base.relative_to(RAIZ).as_posix()} for k in keys}
            ant=p/'anterior';ant.mkdir();salvar_json(ant/'resultados.json',{'por_ajuste':anteriores})
            with patch.object(pub,'auditar_checkpoint',return_value={'natureza':'fixture'}),patch.object(pub,'carregar_minutos',return_value=(minutos,primeiro)),patch.object(pub,'carregar',return_value=(minutos,primeiro)),patch.object(pub,'spot_r0',side_effect=lambda *a,**k:(copy.deepcopy(fake),[],[])):
                saida,r=pub.publicar(p,{'id':'fixture','contrato':{'configuracao':c}},partes,{s:base for s in ciclo.SEEDS},refs,ant)
            self.assertEqual((r['novos'],r['herdados'],len(r['por_ajuste'])),(6,53,59));self.assertEqual(len(r['carteiras']),54)
            self.assertEqual(r['medias']['teste']['huber_seis']['n_seeds'],6);self.assertEqual(r['medias']['teste']['lstm_tres']['n_seeds'],3)
            self.assertEqual(len(list((saida/'carteira').rglob('verificacao.json'))),54)
            (p/'docs').mkdir()
            with patch.object(pub,'RAIZ',p):pub.relatar(r)
