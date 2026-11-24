"""Orçamento complementar, configuração e publicação testados com fixtures sintéticas."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import shutil
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,sha256,conferir_arquivos
from experimento_complemento16 import ciclo
from tests_estados_ampliados.test_sequencia import referencias_sinteticas
from tests_modelos.apoio import conjunto
from modelos.consumo import ConsumoModelos


class Complemento(unittest.TestCase):
    def test_heranca_confere_estado64_explicitamente(self):
        with patch.object(ciclo,'abrir64',side_effect=RuntimeError('fim fixture')) as abrir:
            with self.assertRaisesRegex(RuntimeError,'fim fixture'):ciclo.referencias()
            abrir.assert_called_once_with(64)

    def test_configuracao_identica_r0_e_orcamento(self):
        c=ciclo.configuracao();self.assertEqual(c['mamba']['estado'],16)
        self.assertEqual(ciclo.NOVAS,[7,123,31415]);self.assertFalse(set(ciclo.NOVAS)&set(c['seeds_pareadas']))
        self.assertEqual(set(ciclo.NOVAS)|set(c['seeds_pareadas']),set(ciclo.SEEDS))
        original=ciclo.ler_json
        def mudar(p):
            r=original(p)
            if Path(p).name==Path(ciclo.CONFIG).name:r['treino']['batch']=128
            return r
        with patch.object(ciclo,'ler_json',side_effect=mudar),self.assertRaises(ValueError):ciclo.configuracao()

    def test_autorizacao_identidade_seeds_orcamento(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'a.json';a={'execucao':'id','seeds_novas':ciclo.NOVAS,'seeds_finais':ciclo.SEEDS,'ajustes_reais_total':3,'mensagem_usuario':'fixture'}
            salvar_json(p,a);ciclo.validar_autorizacao(p,'id')
            with self.assertRaises(ValueError):ciclo.validar_autorizacao(p,'outra')
            a['ajustes_reais_total']=6;salvar_json(p,a)
            with self.assertRaises(ValueError):ciclo.validar_autorizacao(p,'id')

    def test_so_tres_novas_publicacao_seis_sem_reexecutar(self):
        refs=referencias_sinteticas(64)
        refs.update({f'estado64_{s}':refs['estado16_42'] for s in ciclo.SEEDS})
        antes={k:sha256(t/'conclusao.json') for k,t in refs.items()}
        consumo=ConsumoModelos(conjunto(),'sintetico');c=ciclo.configuracao()
        c['divisao']={k:[str(pd.Timestamp(t).date()) for t in v] for k,v in consumo._conjunto.contrato['divisao'].items()};c['bootstrap']['replicas']=5
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);f={'id':'fixture','contrato':{'configuracao':c,'fontes':{}}};salvar_json(p/'progresso.json',{'status':'preparado'})
            salvar_json(p/'a.json',{'execucao':'fixture','seeds_novas':ciclo.NOVAS,'seeds_finais':ciclo.SEEDS,'ajustes_reais_total':3,'mensagem_usuario':'fixture'})
            chamadas=[]
            def ajustar(consumo,nome,seed,*args):
                chamadas.append(seed);self.assertEqual(nome,'mamba');return None,{'parametros':20257}
            def avaliar(consumo,partes,nome,cfg,t,*args):
                for nome in ('resultado.json','previsoes_validacao.parquet','previsoes_teste.parquet','previsoes_operacional.parquet'):
                    shutil.copy2(refs['estado16_42']/nome,t/nome)
            minutos=np.ones((31*1440,6));minutos[:,:4]=100;primeiro=int(pd.Timestamp('2021-01-01T00:00Z').timestamp()//60)
            with patch.object(ciclo,'conferir_execucao',return_value=(p,f,consumo,consumo._conjunto.partes,refs)), \
                 patch.object(ciclo,'ajustar',side_effect=ajustar),patch.object(ciclo,'avaliar',side_effect=avaliar), \
                 patch('experimento_complemento16.publicacao.carregar_minutos',return_value=(minutos,primeiro)):
                ciclo.executar(p/'a.json');self.assertEqual(chamadas,[7,123,31415])
                with self.assertRaises(ValueError):ciclo.executar(p/'a.json',retomar=True)
            pub=p/ler_json(p/'publicacao.json')['pasta'];conferir_arquivos(pub,ler_json(pub/'manifesto.json')['arquivos'])
            r=ler_json(pub/'resultados.json');self.assertEqual(len(r['por_ajuste']),29)
            self.assertEqual(len(r['medias']['teste']['estado16_seis']['mse_por_seed']),6)
            novos=[k for k,v in r['por_ajuste'].items() if v['origem_ajuste']=='novo']
            self.assertEqual(set(novos),{'estado16_7','estado16_123','estado16_31415'})
        self.assertEqual(antes,{k:sha256(t/'conclusao.json') for k,t in refs.items()})
