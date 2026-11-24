"""Orçamento e publicação em fixtures sintéticas; nenhum dado real é ajustado."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import shutil
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,sha256,conferir_arquivos
from experimento_estado_mamba import ciclo
from tests_modelos.apoio import conjunto
from modelos.consumo import ConsumoModelos


class Extensao(unittest.TestCase):
    def test_configuracao_rejeita_segunda_mudanca(self):
        original=ciclo.ler_json
        def alterar(p):
            c=original(p)
            if Path(p).name=='mamba_estado8_001.json':c['treino']['taxa_aprendizado']=.001
            return c
        with patch.object(ciclo,'ler_json',side_effect=alterar),self.assertRaises(ValueError):ciclo.configuracao()

    def test_seis_ajustes_heranca_pareamento_e_publicacao(self):
        # Reutiliza exclusivamente resultados artificiais já qualificados na revisão anterior.
        origem=RAIZ/'registros/treinamento/qualificacoes/09524ec9434041e7805053d7c507987c/ciclo_sintetico/celulas'
        refs={}
        for m in ('mamba','lstm'):
            for s in (17,42,2026):
                chave=f'estado16_{s}' if m=='mamba' else f'lstm_{s}'
                pasta=origem/f'{m}_{s}'/('tentativa_002' if m=='lstm' and s==42 else 'tentativa_001')
                refs[chave]=pasta
        refs.update({m:origem/m/'tentativa_001' for m in ('naive','arima')})
        antes={k:sha256(p/'conclusao.json') for k,p in refs.items()}
        consumo=ConsumoModelos(conjunto(),'sintetico');c=ciclo.configuracao()
        c['divisao']={k:[str(pd.Timestamp(t).date()) for t in v] for k,v in consumo._conjunto.contrato['divisao'].items()}
        c['bootstrap']['replicas']=10
        chamadas=[]
        with tempfile.TemporaryDirectory() as tmp:
            pasta=Path(tmp);f={'id':'somente_fixture_sintetica','contrato':{'configuracao':c,'fontes':{}}}
            salvar_json(pasta/'progresso.json',{'status':'preparado'})
            salvar_json(pasta/'auth.json',{'execucao':f['id'],'seeds':c['seeds'],'ajustes_reais':6,'mensagem_usuario':'fixture'})
            def ajuste_falso(consumo,nome,seed,cfg,config,t,vinculo):
                self.assertEqual(nome,'mamba');chamadas.append(seed)
                return None,{'fixture':True}
            def avaliacao_falsa(consumo,partes,nome,cfg,t,vinculo,rede,r):
                # Cópia explicitamente artificial, apenas para exercitar orquestração/publicação.
                for nome in ('resultado.json','previsoes_validacao.parquet','previsoes_teste.parquet','previsoes_operacional.parquet'):
                    shutil.copy2(refs['estado16_42']/nome,t/nome)
            minutos=np.ones((31*1440,6));minutos[:,:4]=100
            primeiro=int(pd.Timestamp('2021-01-01T00:00Z').timestamp()//60)
            with patch.object(ciclo,'conferir_execucao',return_value=(pasta,f,consumo,consumo._conjunto.partes,refs)), \
                 patch.object(ciclo,'ajustar',side_effect=ajuste_falso),patch.object(ciclo,'avaliar',side_effect=avaliacao_falsa), \
                 patch('experimento_estado_mamba.publicacao.carregar_minutos',return_value=(minutos,primeiro)):
                ciclo.executar(pasta/'auth.json')
                self.assertEqual(chamadas,[42,17,2026,7,123,31415])
                self.assertEqual(ler_json(pasta/'progresso.json')['status'],'concluido')
                with self.assertRaises(ValueError):ciclo.executar(pasta/'auth.json',retomar=True)
            pub=ler_json(pasta/'publicacao.json');d=pasta/pub['pasta']
            conferir_arquivos(d,ler_json(d/'manifesto.json')['arquivos'])
            r=ler_json(d/'resultados.json')
            self.assertEqual(len(r['medias']['teste']['estado8_pareadas']['mse_por_seed']),3)
            self.assertEqual(len(r['medias']['teste']['estado8_seis']['mse_por_seed']),6)
        self.assertEqual(antes,{k:sha256(p/'conclusao.json') for k,p in refs.items()})
