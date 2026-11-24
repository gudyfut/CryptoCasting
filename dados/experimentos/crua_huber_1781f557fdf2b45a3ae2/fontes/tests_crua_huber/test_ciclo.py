import contextlib
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, ler_json, salvar_json
from experimentos.crua_huber import ciclo, publicacao as pub
from experimentos.crua_huber.dados import VARIANTES
from experimentos.crua_huber.estatisticas import CONTRASTES, contraste


class CruaHuber(unittest.TestCase):
    def test_grade_32_mais_um_controle_antes_de_outras_seeds(self):
        g = ciclo.grade(ciclo.configuracao())
        self.assertEqual(len(g), 33)
        self.assertEqual(sum(i['controle'] for i in g), 1)
        self.assertEqual([(i['seed'], i['controle']) for i in g[:3]], [(42, False), (42, True), (17, False)])
        self.assertEqual(len({(i['bloco'], i['seed']) for i in g if not i['controle']}), 32)

    def test_diferenca_cientifica_unica_da_receita_crua_mse(self):
        c = ciclo.configuracao()
        f = ler_json(RAIZ/c['origens']['entradas_niveis']['pasta']/'congelamento.json')
        ignorar = {'versao', 'ciclo', 'hipotese', 'variante', 'referencia_execucao', 'controle', 'perda'}
        for b in c['blocos']:
            a = f['contrato']['receitas'][b]['crua']
            z = ciclo.receita(b)
            self.assertEqual({k:v for k,v in a.items() if k not in ignorar},
                             {k:v for k,v in z.items() if k not in ignorar})
            self.assertEqual(a['perda']['nome'], 'MSELoss')
            self.assertEqual(z['perda']['nome'], 'HuberLoss')
            self.assertEqual(z['perda']['delta'], 1.)
            self.assertEqual(z['normalizacao'], 'identidade')
            self.assertEqual(z['mamba']['estado'], 16)

    def test_contraste_interacao_aditiva_zero_e_sinergia(self):
        cfg = {'dias': [2], 'principal': 2, 'seed': 12, 'replicas': 30}
        b = {'B1': {'origens': pd.date_range('2024-01-01', periods=48, freq='h', tz='UTC')}}
        # Efeitos independentes de -1 e -2: combinação 7, interação exatamente zero.
        for v, valor in zip(VARIANTES, [10., 9., 8., 7.]):
            b['B1'][v] = np.full((8, 48), valor)
        self.assertEqual(contraste(b, CONTRASTES['interacao'], cfg)['diferenca_mse'], 0)
        b['B1']['crua_huber'][:] = 6.
        r = contraste(b, CONTRASTES['interacao'], cfg)
        self.assertEqual(r['diferenca_mse'], -1.)
        self.assertEqual(r['decisao'], 'negativo')
        self.assertEqual(r['familia_contrastes'], 4)
        b['B1']['crua_mse'] = b['B1']['crua_mse'][:7]
        with self.assertRaises(ValueError):
            contraste(b, CONTRASTES['interacao'], cfg)

    def test_blocos_peso_igual_nao_quantidade_de_linhas(self):
        c = {'dias': [2], 'principal': 2, 'seed': 1, 'replicas': 20}
        b = {}
        for nome, n, d in [('B1', 48, -1.), ('B2', 24, 3.)]:
            b[nome] = {'origens': pd.date_range('2024-01-01', periods=n, freq='h', tz='UTC'),
                'crua_mse': np.ones((8,n))*4, 'crua_huber': np.ones((8,n))*(4+d)}
        r = contraste(b, CONTRASTES['huber_na_crua'], c)
        self.assertEqual(r['diferenca_mse'], 1.)
        np.testing.assert_allclose(r['intervalos']['2']['ic_bonferroni_98_75'], [1.,1.])

    def test_origem_correta_para_as_quatro_combinacoes(self):
        c = ciclo.configuracao()
        refs = {}
        for n, pt in c['origens'].items():
            refs[n] = {'pasta': RAIZ/pt['pasta'], 'congelamento': ler_json(RAIZ/pt['pasta']/'congelamento.json')}
        f = {'contrato': {'receitas': {'B1': ciclo.receita('B1')}}}
        for v, nome in [('relativa_mse','B1_mse_42'), ('relativa_huber','B1_huber_42'), ('crua_mse','B1_crua_42')]:
            p, _, _, herdado = pub.origem_ajuste(RAIZ, f, refs, 'B1', v, 42)
            self.assertEqual(p.name, nome)
            self.assertTrue(herdado)
        p, _, cfg, herdado = pub.origem_ajuste(RAIZ, f, refs, 'B1', 'crua_huber', 42)
        self.assertEqual(p.name, 'B1_crua_huber_42')
        self.assertFalse(herdado)
        self.assertEqual(cfg['perda']['nome'], 'HuberLoss')

    def test_autorizacao_falha_e_ciclo_encerrado_nao_repetido(self):
        c = ciclo.configuracao()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            salvar_json(p/'autorizacao.json', {'execucao':'fixture','reais_novos_total':33,
                'seeds':c['seeds'],'mensagem_usuario':'fixture','congelamento_sha256':'hash'})
            f = {'id':'fixture','contrato':{'configuracao':c,'grade':ciclo.grade(c),
                'receitas':{b:ciclo.receita(b) for b in c['blocos']}}}
            ciclo.validar_autorizacao(p/'autorizacao.json', f)
            errado = copy.deepcopy(f);errado['id']='outro'
            with self.assertRaises(ValueError):ciclo.validar_autorizacao(p/'autorizacao.json', errado)
            salvar_json(p/'progresso.json', {'status':'preparado'})
            salvar_json(p/'reg/execucao.json', {'id':'fixture'})
            x = type('C', (), {'especificacao':type('E', (), {'identidade':'fixture'})()})()
            with patch.object(ciclo,'conferir_execucao',return_value=(p,f,{b:{'crua':x} for b in c['blocos']},{})), \
                 patch.object(ciclo,'exclusividade',return_value=contextlib.nullcontext()), \
                 patch.object(ciclo,'sha256',return_value='hash'),patch.object(ciclo,'REG',p/'reg'),patch.object(ciclo,'RAIZ',p), \
                 patch.object(ciclo,'ajustar',side_effect=RuntimeError('falha sintética')) as ajustar:
                with self.assertRaises(RuntimeError):ciclo.executar(p/'autorizacao.json')
                self.assertEqual(ajustar.call_count,1)
                self.assertEqual(ler_json(p/'progresso.json')['status'],'interrompido')
                salvar_json(p/'progresso.json', {'status':'concluido'})
                with self.assertRaises(ValueError):ciclo.executar(p/'autorizacao.json')
                self.assertEqual(ajustar.call_count,1)

    def test_publicacao_completa_com_dados_artificiais(self):
        from tests_entradas_niveis.test_ciclo import sinteticos
        from avaliacao.metricas import calcular
        c = copy.deepcopy(ciclo.configuracao())
        c['bootstrap']['replicas'] = 5
        x = sinteticos()['crua']
        c['blocos'] = {b:copy.deepcopy(x._conjunto.contrato['divisao']) for b in c['blocos']}
        ciclo.REG.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ciclo.REG) as tmp:
            p = Path(tmp);base = p/'base/tentativa_001';base.mkdir(parents=True)
            metricas = {};minutos = np.ones((31*1440,6));minutos[:,:4]=100000.
            primeiro = int(pd.Timestamp('2021-01-01T00:00Z').timestamp()//60)
            for parte in ('validacao','teste','operacional'):
                q = x._conjunto.partes[parte].copy();q['previsao']=0.
                q.to_parquet(base/f'previsoes_{parte}.parquet',index=False)
                for row in q.itertuples():
                    minutos[int(row.origem_utc.timestamp()//60)-1-primeiro,3]=row.close
                if parte!='operacional':metricas[parte]=calcular(q.alvo,q.previsao)
            salvar_json(base/'resultado.json', {'metricas':metricas,'recarga_exata':True})
            salvar_json(base/'conclusao.json', {'status':'concluido','arquivos':{}})
            salvar_json(p/'controle_reproducao.json', {'mesma_epoca':True})
            resumo = {k:0. for k in ('retorno_liquido','drawdown_minuto_close','exposicao_media',
                'comissoes_usdt','slippage_usdt','ordens_executadas')}
            resumo['capital_final']=10000.
            herancas = {n:{'pasta':p/n,'publicacao':p/n/'publicacao','congelamento':{},
                'resultados':{'carteiras':{}}} for n in ('huber_blocos','entradas_niveis')}
            h = herancas['huber_blocos']['resultados'];h['naives']={b:{'metricas':metricas} for b in c['blocos']}
            herancas['huber_blocos']['congelamento']={'contrato':{'carteira':{'pasta':str(p),'contrato':{
                'configuracao':ler_json(RAIZ/'configuracoes/backtest_carteira_001.json')}}}}
            for b in c['blocos']:
                for v,nome in [('mse','huber_blocos'),('huber','huber_blocos'),('crua','entradas_niveis')]:
                    for s in c['seeds']:
                        for pol in c['politicas']:
                            for custo in c['cenarios']:
                                herancas[nome]['resultados']['carteiras'][f'{b}/{v}/{s}/{pol}/{custo}']=resumo.copy()
                for pol in ('comprar_manter','caixa'):
                    for custo in c['cenarios']:
                        h['carteiras'][f'{b}/benchmark/benchmark/{pol}/{custo}']=resumo.copy()
            dest=p/'publicacao';dest.mkdir()
            f = {'id':'fixture','contrato':{'configuracao':c,'receitas':{b:ciclo.receita(b) for b in c['blocos']}}}
            def origem(_p,_f,_r,b,v,s):
                return base.parent,f,ciclo.receita(b),v!='crua_huber'
            with patch.object(pub,'origem_ajuste',side_effect=origem), \
                 patch.object(pub,'auditar_ajuste',return_value={'natureza':'fixture'}), \
                 patch.object(pub,'carregar_minutos',return_value=(minutos,primeiro)):
                r = pub.produzir(p,f,{b:{'relativa':x,'crua':x} for b in c['blocos']},herancas,dest)
            self.assertEqual(len(r['por_ajuste']),128)
            self.assertEqual(sum(not z['herdado'] for z in r['por_ajuste'].values()),32)
            self.assertEqual((r['simulacoes_novas'],r['simulacoes_herdadas'],len(r['carteiras'])),(192,600,792))
            self.assertEqual(len(list(dest.glob('carteiras/**/verificacao.json'))),192)
            self.assertTrue(all(x['decisao']=='inconclusivo' for x in r['contrastes']['teste'].values()))
            self.assertFalse(r['criterio_primario']['melhora_clara_contra_tres_referencias'])
            with patch.object(pub,'RAIZ',p):
                (p/'docs').mkdir();pub.relatar(r)


if __name__ == '__main__':
    unittest.main()
