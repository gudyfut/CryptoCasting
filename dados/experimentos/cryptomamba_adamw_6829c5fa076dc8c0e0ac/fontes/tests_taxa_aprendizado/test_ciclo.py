from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import shutil
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,sha256,conferir_arquivos
from experimento_taxa_aprendizado import ciclo
from experimento_taxa_aprendizado.publicacao import contraste
from tests_estados_ampliados.test_sequencia import referencias_sinteticas
from tests_modelos.apoio import conjunto
from modelos.consumo import ConsumoModelos


def refs_artificiais():
    r=referencias_sinteticas(64)
    r.update({f'estado64_{s}':r['estado16_42'] for s in ciclo.SEEDS})
    r.update({f'estado16_{s}':r['estado16_42'] for s in (7,123,31415)})
    return r


def autorizacao(p,codigo='fixture'):
    a={'execucao':codigo,'estados':ciclo.ESTADOS,'seeds':ciclo.SEEDS,'ajustes_reais_total':24,'taxa_referencia':.0002,'taxa_candidata':.0001,'mensagem_usuario':'fixture'}
    salvar_json(p,a);return a


class Taxa(unittest.TestCase):
    def test_unico_fator_por_estado_e_grade(self):
        self.assertEqual(ciclo.grade()['ajustes_reais_total'],24)
        for n in ciclo.ESTADOS:
            c=ciclo.configuracao(n);self.assertEqual(c['treino']['taxa_aprendizado'],.0001);self.assertEqual(c['mamba']['estado'],n)
        original=ciclo.ler_json
        def mudar(p):
            c=original(p)
            if Path(p).name=='mamba_taxa0001_estado8_001.json':c['treino']['batch']=128
            return c
        with patch.object(ciclo,'ler_json',side_effect=mudar),self.assertRaises(ValueError):ciclo.configuracao(8)
        with self.assertRaises(ValueError):ciclo.configuracao(128)

    def test_autorizacao_identidade_orcamento_taxa(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'a.json';a=autorizacao(p);ciclo.validar_autorizacao(p,'fixture')
            with self.assertRaises(ValueError):ciclo.validar_autorizacao(p,'outra')
            for campo,valor in [('ajustes_reais_total',6),('taxa_candidata',.0003),('estados',[16])]:
                alterada=dict(a,**{campo:valor});salvar_json(p,alterada)
                with self.assertRaises(ValueError):ciclo.validar_autorizacao(p,'fixture')

    def test_bootstrap_diferenca_pareada_e_bonferroni(self):
        cfg={'dias':[7,14,28],'principal':14,'replicas':200,'seed':20261020};origens=pd.date_range('2025-01-01',periods=1000,freq='h',tz='UTC')
        a=np.sin(np.arange(1000)/80)**2+.5;b=np.full(1000,.9);r=contraste(origens,a,b,cfg)
        self.assertAlmostEqual(r['diferenca_mse_candidata_menos_referencia'],float((a-b).mean()))
        for d in cfg['dias']:
            lo,hi=r['ic95'][str(d)];x,y=r['ic9875_bonferroni_quatro'][str(d)];self.assertLessEqual(x,lo);self.assertGreaterEqual(y,hi)
        z=contraste(origens,np.ones(1000)*2,np.ones(1000),cfg)
        self.assertEqual(z['ic95']['14'],[1.,1.]);self.assertEqual(z['ic9875_bonferroni_quatro']['14'],[1.,1.])

    def _contexto(self,p):
        consumo=ConsumoModelos(conjunto(),'sintetico');cs={n:ciclo.configuracao(n) for n in ciclo.ESTADOS}
        for c in cs.values():
            c['divisao']={k:[str(pd.Timestamp(t).date()) for t in v] for k,v in consumo._conjunto.contrato['divisao'].items()};c['bootstrap']['replicas']=5
        f={'id':'fixture','contrato':{'grade':ciclo.grade(),'configuracoes':{str(n):c for n,c in cs.items()},'fontes':{}}}
        salvar_json(p/'progresso.json',{'status':'preparado'});autorizacao(p/'a.json')
        return p,f,consumo,consumo._conjunto.partes,refs_artificiais()

    def test_executor24_publica53_e_preserva_herancas(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);ctx=self._contexto(p);refs=ctx[-1];antes={k:sha256(t/'conclusao.json') for k,t in refs.items()};chamadas=[]
            def ajustar(consumo,nome,seed,treino,arq,t,v):
                chamadas.append((v['estado'],seed));self.assertEqual(treino['taxa_aprendizado'],.0001);return None,{'parametros':ciclo.PARAMETROS[v['estado']]}
            def avaliar(consumo,partes,nome,cfg,t,*args):
                for nome in ('resultado.json','previsoes_validacao.parquet','previsoes_teste.parquet','previsoes_operacional.parquet'):shutil.copy2(refs['estado16_42']/nome,t/nome)
            minutos=np.ones((31*1440,6));minutos[:,:4]=100;primeiro=int(pd.Timestamp('2021-01-01T00:00Z').timestamp()//60)
            with patch.object(ciclo,'conferir_execucao',return_value=ctx),patch.object(ciclo,'ajustar',side_effect=ajustar),patch.object(ciclo,'avaliar',side_effect=avaliar), \
                 patch('experimento_taxa_aprendizado.publicacao.carregar_minutos',return_value=(minutos,primeiro)):
                ciclo.executar(p/'a.json')
                self.assertEqual(chamadas,[(n,s) for n in ciclo.ESTADOS for s in ciclo.ORDEM_SEEDS])
                with self.assertRaises(ValueError):ciclo.executar(p/'a.json',True)
            pub=p/ler_json(p/'publicacao.json')['pasta'];conferir_arquivos(pub,ler_json(pub/'manifesto.json')['arquivos']);r=ler_json(pub/'resultados.json')
            self.assertEqual(len(r['por_ajuste']),53);self.assertEqual((r['novos'],r['herdados']),(24,29))
            self.assertEqual(set(r['contrastes']['validacao']),{'8','16','32','64'})
            for n in ciclo.ESTADOS:self.assertEqual(r['medias']['teste'][f'candidata_estado{n}']['n_seeds'],6)
            from experimento_taxa_aprendizado import finalizacao
            (p/'docs').mkdir()
            with patch.object(finalizacao,'RAIZ',p):
                finalizacao.relatar(r,{'id':'fixture'},{'arquivo':'fixture/auditoria.json'},{'arquivo':'fixture/comparacao.json'})
                texto=(p/'docs/resultados_taxa_aprendizado.md').read_text(encoding='utf-8')
                self.assertIn('24novos ajustes',texto);self.assertIn('| 64 | 0,0001 |',texto)
            self.assertEqual(antes,{k:sha256(t/'conclusao.json') for k,t in refs.items()})

    def test_falha_interrompe_antes_de_outro_estado(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);ctx=self._contexto(p)
            with patch.object(ciclo,'conferir_execucao',return_value=ctx),patch.object(ciclo,'ajustar',side_effect=RuntimeError('falha artificial')) as ajuste,patch.object(ciclo,'publicar') as publicar:
                with self.assertRaisesRegex(RuntimeError,'falha artificial'):ciclo.executar(p/'a.json')
                self.assertEqual(ajuste.call_count,1);publicar.assert_not_called()
            self.assertEqual(ler_json(p/'progresso.json')['status'],'interrompido')
            self.assertTrue((p/'celulas/estado8_mamba_42/tentativa_001/falha.json').exists())
