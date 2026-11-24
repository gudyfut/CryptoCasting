"""Mesmo executor completo, somente mercado artificial e orçamento sintético."""
from copy import deepcopy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
import torch
from infraestrutura.artefatos import RAIZ, salvar_json, ler_json, conferir_arquivos, sha256
from testes.modelos.apoio import conjunto
from modelos.consumo import ConsumoModelos
from treinamento import ciclo
from treinamento.configuracao import carregar, grade
from avaliacao.spot import simular
from avaliacao.publicacao import contraste_temporal


class Integracao(unittest.TestCase):
    @unittest.skipUnless(os.name == 'posix' and torch.cuda.is_available(), 'Ciclo sintético exige Linux/WSL e CUDA oficial.')
    def test_ciclo_sintetico_completo(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(os.environ.get('CC_QUALIFICACAO', tmp)) / 'ciclo_sintetico'
            raiz.mkdir(parents=True)
            consumo = ConsumoModelos(conjunto(), 'sintetico')
            c = carregar()
            c['treino'].update(epocas=2, paciencia=2)
            c['bootstrap']['replicas'] = 20
            c['divisao'] = {k:[str(pd.Timestamp(t).date()) for t in ts] for k,ts in consumo._conjunto.contrato['divisao'].items()}
            c['configuracao_modelos'] = str(RAIZ/c['configuracao_modelos'])
            congelado = {'id':'qualificacao_sintetica', 'contrato': {'configuracao':c, 'fontes':{}}}
            salvar_json(raiz/'progresso.json', {'status':'aguardando_ok'})
            aprovacao = raiz/'autorizacao_sintetica.json'
            salvar_json(aprovacao, {'execucao':congelado['id'], 'acao':'treinar_validar_testar',
                        'celulas':[q['chave'] for q in grade(c)], 'mensagem_usuario':'fixture sintética, não autorização de mercado',
                        'utc':'sintetico'})
            n=31*1440
            minutos=np.ones((n,6),float)
            minutos[:,:4]=100+np.arange(n)[:,None]*.00001
            primeiro=int(pd.Timestamp('2021-01-01T00:00Z').timestamp()//60)
            from treinamento.neural import ajustar
            chamadas = []
            def interromper(*args, **kwargs):
                chamadas.append(args[1])
                if len(chamadas) == 2:
                    raise RuntimeError('interrupção artificial antes do segundo ajuste')
                return ajustar(*args, **kwargs)
            with patch.object(ciclo,'conferir_execucao',return_value=(raiz,congelado,consumo,consumo._conjunto.partes)), \
                 patch('avaliacao.mercado.carregar_minutos',return_value=(minutos,primeiro)):
                with patch('treinamento.neural.ajustar', side_effect=interromper), self.assertRaises(RuntimeError):
                    ciclo.executar(aprovacao)
                principal=raiz/'celulas/mamba_42/tentativa_001/conclusao.json'
                preservado=sha256(principal)
                self.assertEqual(ler_json(raiz/'progresso.json')['status'],'interrompido')
                ciclo.executar(aprovacao, retomar=True)
                self.assertEqual(sha256(principal),preservado)
                self.assertTrue((raiz/'celulas/lstm_42/tentativa_001/falha.json').is_file())
                self.assertTrue((raiz/'celulas/lstm_42/tentativa_002/conclusao.json').is_file())
                self.assertEqual(ler_json(raiz/'progresso.json')['status'],'concluido')
                self.assertEqual(len(list((raiz/'celulas').glob('*/tentativa_*/conclusao.json'))),10)
                with self.assertRaises(ValueError):
                    ciclo.executar(aprovacao, retomar=True)
            pub=ler_json(raiz/'publicacao.json')
            p=raiz/pub['pasta']
            conferir_arquivos(p,ler_json(p/'manifesto.json')['arquivos'])
            resultado=ler_json(p/'resultados.json')
            self.assertEqual(set(resultado['por_ajuste']), {'mamba_17','mamba_42','mamba_2026','lstm_17','lstm_42','lstm_2026','naive','arima'})
            self.assertEqual(resultado['por_ajuste']['naive']['spot']['base']['retorno_liquido'],0)

    def test_spot_custos_lacuna_e_fronteira(self):
        p=carregar()['operacao']
        t=pd.Timestamp('2025-01-01T00:00Z')
        q=pd.DataFrame({'origem_utc':[t], 'previsao':[.1]})
        m=np.ones((3*1440,6));m[:,:4]=100
        r,_,_=simular(q,m,int(t.timestamp()//60),'2025-01-04',p)
        esperado=(1-p['slippage'])*(1-p['taxa'])/((1+p['slippage'])*(1+p['taxa']))-1
        self.assertAlmostEqual(r['retorno_liquido'],esperado)
        m[1,0]=np.nan
        r,_,_=simular(q,m,int(t.timestamp()//60),'2025-01-04',p)
        self.assertIsNone(r['retorno_liquido'])
        r,_,_=simular(q,m,int(t.timestamp()//60),'2025-01-02',p)
        self.assertEqual(r['entradas_planejadas'],0)

    def test_bootstrap_sinal_e_igualdade(self):
        t=pd.date_range('2025-01-01',periods=40*24,freq='h',tz='UTC')
        c=dict(carregar()['bootstrap'],replicas=50)
        r=contraste_temporal(t,np.ones(len(t)),np.ones(len(t)),c)
        self.assertEqual(r['diferenca_mse_a_menos_b'],0)
        self.assertTrue(all(x==[0,0] for x in r['ic95'].values()))
