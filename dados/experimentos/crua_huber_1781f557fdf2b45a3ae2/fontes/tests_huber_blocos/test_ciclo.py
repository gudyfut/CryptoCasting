import contextlib
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, ler_json, salvar_json, sha256, identidade
from experimentos.huber_blocos import ciclo
from experimentos.huber_blocos.dados import configuracao, receita, Verificador, REG
from experimentos.huber_blocos.estatisticas import contraste
from experimentos.huber_blocos.publicacao import janela_operacional, grade_operacoes


class Blocos(unittest.TestCase):
    def test_grade_64_e_dois_controles_antes_das_outras_seeds(self):
        c=configuracao();g=ciclo.grade(c)
        self.assertEqual(len(g),66);self.assertEqual(sum(not i['controle'] for i in g),64)
        self.assertEqual([(i['bloco'],i['seed'],i['controle']) for i in g[:4]],[('B1',42,False)]*2+[('B1',42,True)]*2)
        self.assertEqual(len({ciclo.chave(i) for i in g if not i['controle']}),64)
        self.assertEqual(len(set(c['seeds'])),8)

    def test_receitas_diferem_apenas_na_perda_e_identificador(self):
        c=configuracao()
        for b in c['blocos']:
            a,z=[receita(c,b,p) for p in ('mse','huber')]
            self.assertEqual({k:v for k,v in a.items() if k not in ('perda','variante')},
                             {k:v for k,v in z.items() if k not in ('perda','variante')})
            self.assertEqual(a['divisao'],c['blocos'][b]);self.assertEqual(a['seeds'],c['seeds'])
            self.assertEqual(a['treino']['taxa_aprendizado'],.0002)

    def test_scalers_nao_veem_futuro_e_sao_reestimados(self):
        from entradas_modelo.pipeline import construir
        n=96*24;i=np.arange(n);preco=100*np.exp(.0001*i+.01*np.sin(i/11))
        t=pd.date_range('2021-01-01',periods=n,freq='h',tz='UTC')
        q=pd.DataFrame({'inicio_utc':t,'fim_utc':t+pd.Timedelta(hours=1),'open':preco*.999,
            'high':preco*1.01,'low':preco*.99,'close':preco,'volume':1+i%20,'completo':True})
        c=ler_json(RAIZ/'configuracoes/entradas_ohlcv24_001.json')
        c['divisao']={'treino':['2021-01-01T00:00:00Z','2021-02-01T00:00:00Z'],
            'validacao':['2021-02-01T00:00:00Z','2021-03-01T00:00:00Z'],
            'teste':['2021-03-01T00:00:00Z','2021-04-01T00:00:00Z']}
        a=construir(q,c,60);qq=q.copy();f=qq.inicio_utc>=pd.Timestamp(c['divisao']['treino'][1])
        qq.loc[f,['open','high','low','close']]*=3;qq.loc[f,'volume']*=10
        z=construir(qq,c,60);self.assertEqual(a.escalas,z.escalas)
        pd.testing.assert_frame_equal(a.partes['treino'],z.partes['treino'])
        np.testing.assert_array_equal(a.janelas(a.partes['treino'].indice_candle.to_numpy()),z.janelas(z.partes['treino'].indice_candle.to_numpy()))
        c2=copy.deepcopy(c);c2['divisao']['treino'][1]='2021-02-08T00:00:00Z';c2['divisao']['validacao'][0]=c2['divisao']['treino'][1]
        b=construir(q,c2,60);self.assertNotEqual(a.escalas,b.escalas)
        for nome in ('treino','validacao','teste'):
            self.assertTrue((b.partes[nome].destino_utc<pd.Timestamp(c2['divisao'][nome][1])).all())

    def test_verificador_fresco_detecta_alteracao_e_ciclo(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'fontes').mkdir();(p/'a.txt').write_text('a',encoding='utf-8')
            sig={'fontes':{}};m={'id':identidade(sig)[:20],'assinatura':sig,'arquivos':{'a.txt':sha256(p/'a.txt')}}
            salvar_json(p/'manifesto.json',m);v=Verificador();v.artefato(p);v.artefato(p)
            (p/'a.txt').write_text('b',encoding='utf-8')
            with self.assertRaises(ValueError):Verificador().artefato(p)
            with self.assertRaises(ValueError):v.arquivos_em(p,{'../fora':'x'})
            v.pilha.add(p.resolve())
            with self.assertRaises(ValueError):v.artefato(p)

    def test_bootstrap_pareado_pesos_iguais_e_empate(self):
        cfg={'dias':[2],'principal':2,'replicas':30,'seed':17}
        b={}
        for nome,n,d in [('A',48,-1.),('B',24,3.)]:
            z=np.ones((8,n))*4;b[nome]={'origens':pd.date_range('2024-01-01',periods=n,freq='h',tz='UTC'),'mse':z,'huber':z+d}
        r=contraste(b,cfg);self.assertAlmostEqual(r['diferenca_mse_huber_menos_mse'],1.)
        np.testing.assert_allclose(r['ic95_seeds_e_tempo']['2'],[1.,1.])
        for v in b.values():v['huber']=v['mse'].copy()
        self.assertEqual(contraste(b,cfg)['ic95_seeds_e_tempo']['2'],[0.,0.])
        b['A']['huber']=b['A']['huber'][:7]
        with self.assertRaises(ValueError):contraste(b,cfg)

    def test_calendario_operacional_nao_depende_do_alvo(self):
        from tests_modelos.apoio import conjunto
        q=conjunto().partes['operacional'].copy();q['previsao']=0.
        fim='2021-02-01T00:00:00Z';a=janela_operacional(q,fim)
        qq=q.copy();qq['alvo']=float('nan');qq['preco_destino']=-1.
        pd.testing.assert_frame_equal(a,janela_operacional(qq,fim))
        self.assertTrue((a.destino_utc<pd.Timestamp(fim)).all());self.assertNotIn('alvo',a.columns)
        self.assertEqual(len(list(grade_operacoes(configuracao()))),408)

    def test_autorizacao_falha_interrompe_e_nao_repete_encerrado(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);a={'execucao':'fixture','seeds':configuracao()['seeds'],'ajustes_reais_total':66,
                'ajustes_principais':64,'controles_reais':2,'abordagem':'huber_blocos','mensagem_usuario':'fixture'}
            salvar_json(p/'a.json',a);ciclo.validar_autorizacao(p/'a.json','fixture')
            with self.assertRaises(ValueError):ciclo.validar_autorizacao(p/'a.json','outro')
            c=configuracao();cfg=receita(c,'B1','mse');salvar_json(p/'progresso.json',{'status':'preparado'})
            x=type('X',(),{'especificacao':type('E',(),{'identidade':'fixture'})()})()
            f={'id':'fixture','contrato':{'configuracao':c,'receitas':{'B1':{'mse':cfg}},'grade':ciclo.grade(c)}}
            with patch.object(ciclo,'conferir_execucao',return_value=(p,f,{'B1':x})),patch.object(ciclo,'exclusividade',return_value=contextlib.nullcontext()),patch.object(ciclo,'ajustar_mse',side_effect=RuntimeError('fixture')) as fn:
                with self.assertRaises(RuntimeError):ciclo.executar(p/'a.json')
                self.assertEqual(fn.call_count,1);self.assertEqual(ler_json(p/'progresso.json')['status'],'interrompido')
                salvar_json(p/'progresso.json',{'status':'concluido'})
                with self.assertRaises(ValueError):ciclo.executar(p/'a.json',True)
                self.assertEqual(fn.call_count,1)

    def test_publicacao_reduzida_com_motor_real_e_relatorio(self):
        from tests_modelos.apoio import conjunto
        from modelos.consumo import ConsumoModelos
        from avaliacao.metricas import calcular
        from treinamento.preservacao import publicar as selar
        from experimentos.huber_blocos import publicacao as pub
        x=ConsumoModelos(conjunto(),'fixture');c=configuracao();c['blocos']={'B1':x._conjunto.contrato['divisao']}
        c['seeds']=[17,42];c['ajustes_principais']=4;c['simulacoes_total']=30;c['bootstrap']['replicas']=5
        receitas={'B1':{v:receita(c,'B1',v) for v in c['variantes']}}
        cb=ler_json(RAIZ/'dados/experimentos/backtest_carteira_8ec8a66648313caa48e3/congelamento.json')['contrato']
        REG.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=REG) as tmp:
            p=Path(tmp);minutos=np.ones((31*1440+5,6));minutos[:,:4]=100.
            primeiro=int(pd.Timestamp('2021-01-01T00:00Z').timestamp()//60)
            for perda in c['variantes']:
                for seed in c['seeds']:
                    t=p/'celulas'/f'B1_{perda}_{seed}'/'tentativa_001';t.mkdir(parents=True);metricas={}
                    for parte,q in x._conjunto.partes.items():
                        q=q.copy();q['previsao']=0.;q.to_parquet(t/f'previsoes_{parte}.parquet',index=False)
                        if parte!='operacional':metricas[parte]=calcular(q.alvo,q.previsao)
                        for row in q.itertuples():minutos[int(row.origem_utc.timestamp()//60)-1-primeiro,3]=row.close
                    salvar_json(t/'resultado.json',{'metricas':metricas});selar(t)
                t=p/'controles'/f'B1_{perda}_42'/'tentativa_001';t.mkdir(parents=True);salvar_json(t/'conclusao.json',{})
            f={'id':'fixture','contrato':{'configuracao':c,'receitas':receitas,'carteira':{'pasta':c['carteira_execucao'],'contrato':cb}}}
            with patch.object(pub,'auditar_ajuste',return_value={'fixture':True}),patch.object(pub,'carregar_minutos',return_value=(minutos,primeiro)):
                dest,r=pub.publicar(p,f,{'B1':x})
            self.assertEqual(len(r['por_ajuste']),4);self.assertEqual(len(r['carteiras']),30)
            self.assertFalse(r['criterio_primario']['media_mse_menor'])
            self.assertEqual(r['medias_por_bloco']['B1']['teste']['huber']['n_seeds'],2)
            (p/'docs').mkdir()
            with patch.object(pub,'RAIZ',p):self.assertEqual(pub.relatar(r),'docs/resultados_huber_blocos.md')
