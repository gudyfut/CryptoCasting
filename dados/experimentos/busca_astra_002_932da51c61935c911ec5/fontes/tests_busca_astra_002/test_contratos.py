import copy
import unittest
import tempfile
import time
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
from experimentos.busca_astra_002.contrato import ancoras,validar_receita,validar_proposta,score,selecionar,configuracao,SEEDS
from experimentos.busca_astra_002.dados import Dados,carregar_candles
from experimentos.busca_astra_002.metricas import medir
from experimentos.busca_astra_002.agente import validar_contexto
from experimentos.busca_astra_002.publicacao import intervalo

class Testes(unittest.TestCase):
    def test_metricas_limites(self):
        y=np.array([-2.,-1.,1.,2.]);perfeito=medir(y,y);zero=medir(y,np.zeros(4));inverso=medir(y,-y)
        self.assertEqual(perfeito['mse'],0);self.assertEqual(perfeito['balanced_accuracy'],1)
        self.assertEqual(zero['q_mse'],1);self.assertEqual(zero['cobertura'],0);self.assertIsNone(zero['pearson']);self.assertIsNone(zero['precisao']['alta'])
        self.assertEqual(inverso['balanced_accuracy'],0);self.assertAlmostEqual(inverso['pearson'],-1)
        self.assertEqual(medir(y,np.ones(4))['balanced_accuracy'],.5)
        self.assertAlmostEqual(medir(y,np.array([0,0,1,0]))['cobertura'],.25)
        with self.assertRaises(AssertionError):medir(y,np.full(4,np.nan))
        with self.assertRaises(AssertionError):medir(np.zeros(4),np.zeros(4))

    def test_fator_unico_fixo_e_duplicata(self):
        rr=ancoras();p=dict(acao='experimentar',pai='A0_C05',fator='momentum',valor=True,mecanismo='a',metrica_esperada='a',risco='a',custo='a')
        r=validar_proposta(p,rr);self.assertTrue(r['momentum'])
        with self.assertRaises(AssertionError):validar_proposta(p,dict(rr,N01=r))
        with self.assertRaises(AssertionError):validar_receita(dict(r,ganho_saida=.5))
        with self.assertRaises(AssertionError):validar_receita(dict(r,estado=32))
        with self.assertRaises(AssertionError):validar_receita(dict(r,representacao='crua'))

    def test_cobertura_e_portoes(self):
        def linhas(q):return [{'bloco':b,'seed':s,'metricas':{'mse':q,'q_mse':q,'q_mae':q},'media_constante':{'q_mse':1.},'parametros':20} for b in ['S1','S2','S3'] for s in SEEDS[:3]]
        refs={'A':linhas(1.),'R':linhas(1.01)};c=linhas(.99)
        out=selecionar({'N':list(reversed(c))},refs);self.assertEqual(out['escolhida'],'N')
        self.assertIsNone(selecionar({'N':linhas(1.)},refs)['escolhida'])
        self.assertIsNone(selecionar({'N':c[:-1]},refs)['escolhida'])
        with self.assertRaises(AssertionError):score(c+[c[0]],SEEDS[:3])
        c[0]['metricas']['mse']=2.;self.assertIsNone(selecionar({'N':c},refs)['escolhida'])

    def test_isolamento_prompt(self):
        c={'fase':'busca','recortes':configuracao()['recortes'],'receitas':ancoras(),'historico':[],'rejeicoes':[],'instrucao':'propor'}
        validar_contexto(c)
        with self.assertRaises(AssertionError):validar_contexto(dict(c,teste={}))
        c['historico']=[{'bloco':'B1'}]
        with self.assertRaises(AssertionError):validar_contexto(c)

    def test_bootstrap_identico_e_sinal(self):
        t=pd.date_range('2024-01-01',periods=24*35,freq='h',tz='UTC');x=np.ones((8,len(t)))
        self.assertEqual(intervalo({'B':{'origens':t,'candidata':x,'base':x}},'base',30)['intervalos']['14']['ic95'],[0.,0.])
        out=intervalo({'B':{'origens':t,'candidata':x*.5,'base':x}},'base',30)
        self.assertEqual(out['diferenca_mse'],-.5)
        self.assertEqual(out['intervalos']['7']['ic98_333_bonferroni_tres'],[-.5,-.5])

    def test_coordenador_grade_completa_sem_treino(self):
        """Exercita TODA a fila, controles, promoção e final com worker simulado."""
        from experimentos.busca_astra_002.ciclo import Coordenador
        from infraestrutura.artefatos import salvar_json
        propostas=[('N01','contexto',24),('N01','contexto',168),('N02','contexto',24),('N02','contexto',168),
                   ('N03','contexto',24),('N03','contexto',168),('N04','contexto',24),('N04','contexto',168)]
        respostas=[dict(acao='experimentar',pai=p,fator=f,valor=v,mecanismo='a',metrica_esperada='a',risco='a',custo='a') for p,f,v in propostas]
        with tempfile.TemporaryDirectory() as tmp:
            pasta=Path(tmp);reg=pasta/'reg';reg.mkdir();salvar_json(reg/'inicio_preparo.json',{'inicio_timestamp':time.time()})
            with patch('experimentos.busca_astra_002.ciclo.REG',reg):
                c=Coordenador(pasta,{}, {'versao_cli':'teste'})
            chamadas=[]
            def ajuste(n,b,s,grupo='desenvolvimento',eh_controle=False):
                chamadas.append((n,b,s,grupo,eh_controle));c.jobs.append({'status':'concluido','segundos_totais':1})
                q=.98 if n.startswith('N') else 1.
                linha={'id':n,'bloco':b,'seed':s,'metricas':{'mse':q,'q_mse':q,'q_mae':q},'media_constante':{'q_mse':1.},'parametros':20}
                if not eh_controle and b.startswith('S'):c.rows[n].append(linha)
                return linha
            def consultar(*a,**kw):
                self.assertTrue(all(not b.startswith('B') for _,b,_,_,_ in chamadas))
                return respostas.pop(0)
            with patch.object(c,'ajuste',side_effect=ajuste),patch.object(c,'estado'),patch.object(c,'encerrar',return_value='fim'),\
                 patch('experimentos.busca_astra_002.ciclo.controle',return_value={}),\
                 patch('experimentos.busca_astra_002.agente.consultar',side_effect=consultar),\
                 patch('experimentos.busca_astra_002.publicacao.publicar') as pub:
                self.assertEqual(c.executar(),'fim');pub.assert_called_once()
            self.assertEqual(len(chamadas),197);self.assertEqual(c.consultas,9)
            principais=[(n,b,s) for n,b,s,_,ctrl in chamadas if not ctrl and b.startswith('B')]
            self.assertEqual(len(principais),96);self.assertEqual(len(set(principais)),96)
            self.assertEqual(sum(ctrl for *_,ctrl in chamadas),2)
            self.assertEqual(chamadas[1],('A0_C05','S1',42,'controles/desenvolvimento',True))

    def test_publicacao_completa_com_motor_sintetico(self):
        """Exercita96saídas e800artefatos sem treinar ou simular mercado real."""
        from infraestrutura.artefatos import salvar_json,sha256,ler_json
        from experimentos.busca_astra_002.publicacao import publicar
        t=pd.date_range('2024-01-01',periods=24*35,freq='h',tz='UTC')
        y=np.sin(np.arange(len(t)))*.01;p=y*.2
        q=pd.DataFrame({'indice_candle':np.arange(len(t)),'origem_utc':t,'destino_utc':t+pd.Timedelta(hours=24),'close':100.,'alvo':y,'previsao':p})
        m=medir(y,p);rbase={'epoca':1,'recarga_exata':True,'parametros':20,'teste':m}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);ciclo=root/'ciclo';ciclo.mkdir();fp=root/'f03';fp.mkdir()
            salvar_json(fp/'congelamento.json',{'assinatura':{'fontes':{},'configuracao':{},'spot':{},'futuros':{}}})
            salvar_json(ciclo/'congelamento.json',{'operacional':{'pasta':'f03','congelamento_sha256':sha256(fp/'congelamento.json')}})
            for b in ['B1','B2','B3','B4']:
                for v in ['candidata',*ancoras()]:
                    for s in SEEDS:
                        d=ciclo/'final'/v/f'{b}_{s}';d.mkdir(parents=True)
                        q.to_parquet(d/'previsoes_teste.parquet',index=False)
                        salvar_json(d/'epocas.json',[{'epoca':1,'mse_validacao':1.}]);salvar_json(d/'selecao.json',{'epoca':1})
                        salvar_json(d/'manifesto_ajuste.json',{'sintetico':True})
            def conferir(d):
                b,s=d.name.split('_');return dict(rbase,bloco=b,seed=int(s)),{'partes':{'teste':{'diario_00utc':m}}}
            def simular(serie,mercado,cfg,pol,br,custo,bench):
                self.assertNotIn('alvo',serie.columns)
                resumo={k:0. for k in ['retorno_liquido','drawdown','giro','exposicao_media','exposicao_vendida','comissoes','slippage','funding']}
                resumo.update(politica=pol,braco=br,cenario=custo,benchmark=bench)
                return resumo,[],[],pd.DataFrame({'patrimonio':[10000.]}),[]
            with patch('experimentos.busca_astra_002.publicacao.RAIZ',root),\
                 patch('experimentos.busca_astra_002.publicacao.conferir_ajuste',side_effect=conferir),\
                 patch('experimentos.busca_astra_002.publicacao.intervalo',return_value={'teste_sintetico':True}),\
                 patch('simulacao_operacoes.smart.mercado.carregar',return_value={'spot':None,'futuro':None}),\
                 patch('simulacao_operacoes.revisada.simulador.simular',side_effect=simular) as motor,\
                 patch('simulacao_operacoes.revisada.auditoria.conferir',return_value={'decomposicao_futuros':{}}):
                publicar(ciclo,time.time()+3600)
                self.assertEqual(motor.call_count,800)
            self.assertEqual(ler_json(ciclo/'publicacao.json')['ajustes_principais'],96)
            self.assertEqual(len(ler_json(ciclo/'publicacao/manifesto.json')['carteiras']),800)

class DadosReaisSemTreino(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.q=carregar_candles(True)

    def test_separacao_purga_escalas(self):
        r=ancoras()['A0_C05']
        for b,div in configuracao()['recortes'].items():
            d=Dados(self.q,r,b)
            for parte,periodo in [('treino',div['treino']),('validacao',div['parada']),('comparacao',div['comparacao'])]:
                z=d.tabela.iloc[d.indices[parte]]
                self.assertTrue((z.origem_utc>=pd.Timestamp(periodo[0],tz='UTC')).all())
                self.assertTrue((z.destino_utc<pd.Timestamp(periodo[1],tz='UTC')).all())
            y=d.y[d.indices['treino']];self.assertEqual(d.ym,float(y.mean()));self.assertEqual(d.ys,float(y.std()))
            self.assertLess(d.indices['treino'][-1]+24,d.indices['validacao'][0]);self.assertLess(d.indices['validacao'][-1]+24,d.indices['comparacao'][0])

    def test_causalidade_grupos_e_origens_comuns(self):
        r=ancoras()['A0_C05'];base=Dados(self.q,r,'S1');ix=base.indices['comparacao'][100]
        qq=self.q.copy();campos=['open','high','low','close','volume'];qq.loc[ix+1:,campos]*=1.2
        for grupo,extras in [('momentum',2),('volatilidade',2),('volume_relativo',1)]:
            rr=dict(r,**{grupo:True});a=Dados(self.q,rr,'S1');b=Dados(qq,rr,'S1')
            for parte in base.indices:np.testing.assert_array_equal(a.indices[parte],base.indices[parte])
            np.testing.assert_array_equal(a.janelas([ix]),b.janelas([ix]));self.assertEqual(a.janelas([ix]).shape,(1,72,5+extras))
            self.assertNotEqual(a.y[ix],b.y[ix])
            self.assertEqual(a.escalas,b.escalas)

    def test_ancoras_equivalencia_matrizes_finais(self):
        from experimentos.busca_astra.dados import Dados as Antigos,carregar_candles as carregar
        q=carregar(False)
        for b in ['B1','B2','B3','B4']:
            for r in ancoras().values():
                legado={k:v for k,v in r.items() if k not in ['momentum','volatilidade','volume_relativo']}
                a=Dados(q,r,b);v=Antigos(q,legado,b)
                self.assertEqual(a.escalas,v.escalas)
                for parte in a.indices:
                    np.testing.assert_array_equal(a.indices[parte],v.indices[parte]);ids=a.indices[parte][::137]
                    np.testing.assert_array_equal(a.janelas(ids),v.janelas(ids))
                    np.testing.assert_array_equal(a.y[ids],v.y[ids])

if __name__=='__main__':unittest.main()
