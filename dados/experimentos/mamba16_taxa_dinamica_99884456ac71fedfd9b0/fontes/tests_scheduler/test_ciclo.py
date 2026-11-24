import contextlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json
from experimentos.taxa_dinamica import ciclo
from experimentos.taxa_dinamica.agendamento import criar_agendador,POLITICA
from analises.metricas import resumir,faixas_validacao


class Scheduler(unittest.TestCase):
    def test_configuracao_e_ast_nao_mudam_outro_fator(self):
        c=ciclo.configuracao();self.assertEqual(c['mamba']['estado'],16);self.assertTrue(ciclo.conferir_treinador()['demais_instrucoes_iguais'])
        ler=ciclo.ler_json
        def mudar(p):
            v=ler(p)
            if Path(p).name==Path(ciclo.CONFIG).name:v['treino']['taxa_aprendizado']=.0001
            return v
        with patch.object(ciclo,'ler_json',side_effect=mudar),self.assertRaises(ValueError):ciclo.configuracao()

    def test_trajetoria_taxa_e_contador_parada_independente(self):
        import torch
        from treinamento.selecao import SelecaoEpoca
        p=torch.nn.Parameter(torch.tensor([1.]));o=torch.optim.AdamW([p],lr=.0002);sch=criar_agendador(o,POLITICA);sel=SelecaoEpoca(10);taxas=[]
        for epoca in range(1,12):
            sel.observar(epoca,1.);sch.step(1.);taxas.append(o.param_groups[0]['lr'])
        self.assertEqual(taxas,[.0002,.0002,.0002,.0001,.0001,.0001,.00005,.00005,.00005,.000025,.000025])
        self.assertTrue(sel.parar);self.assertEqual(sel.epoca,1)

    def test_sem_estagnacao_nao_reduz(self):
        import torch
        p=torch.nn.Parameter(torch.tensor([1.]));o=torch.optim.AdamW([p],lr=.0002);s=criar_agendador(o,POLITICA)
        for v in [1.,.8,.7,.6]:s.step(v)
        self.assertEqual(o.param_groups[0]['lr'],.0002)

    def test_diagnostico_constante_empates_e_origens(self):
        q=pd.DataFrame({'indice_candle':[1,2,3,4],'alvo':[1.,-1.,2.,-2.],'previsao':[0.,0.,0.,0.]})
        d=resumir(q,q);self.assertIsNone(d['pearson']);self.assertIsNone(d['spearman']);self.assertEqual(d['empates_referencia'],1.)
        with self.assertRaises(ValueError):resumir(q,q.assign(indice_candle=[2,3,4,5]))
        v=q.assign(previsao=[-.02,-.01,.01,.02]);a=faixas_validacao(v,v)
        b=faixas_validacao(v,v.assign(alvo=[999.,-999.,1.,2.]))
        self.assertEqual(a['cortes_derivados_somente_validacao'],b['cortes_derivados_somente_validacao'])
        self.assertEqual(len(faixas_validacao(q,q)['faixas']),1)

    def test_autorizacao_e_parada_em_falha(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);a={'execucao':'fixture','seeds':ciclo.SEEDS,'ajustes_reais_total':6,'abordagem':'mamba16_taxa_dinamica','mensagem_usuario':'fixture'}
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
        from experimentos.taxa_dinamica import publicacao as pub
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
            self.assertEqual(r['medias']['teste']['scheduler_seis']['n_seeds'],6);self.assertEqual(r['medias']['teste']['lstm_tres']['n_seeds'],3)
            self.assertEqual(len(list((saida/'carteira').rglob('verificacao.json'))),54)
            (p/'docs').mkdir()
            with patch.object(pub,'RAIZ',p):pub.relatar(r)
