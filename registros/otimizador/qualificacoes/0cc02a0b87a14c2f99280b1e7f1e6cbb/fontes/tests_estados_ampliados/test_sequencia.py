"""Orçamento, sequência, falhas e agrupamento; fixtures exclusivamente artificiais."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import shutil
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,conferir_arquivos,sha256
from experimento_estados_ampliados import ciclo
from tests_modelos.apoio import conjunto
from modelos.consumo import ConsumoModelos


def referencias_sinteticas(estado):
    raiz=RAIZ/'registros/treinamento/qualificacoes/09524ec9434041e7805053d7c507987c/ciclo_sintetico/celulas'
    refs={}
    for m in ('mamba','lstm'):
        for s in (17,42,2026):
            k=f'estado16_{s}' if m=='mamba' else f'lstm_{s}'
            refs[k]=raiz/f'{m}_{s}'/('tentativa_002' if m=='lstm' and s==42 else 'tentativa_001')
    refs.update({m:raiz/m/'tentativa_001' for m in ('naive','arima')})
    # Doubles de resultado somente para testar pareamento/publicação; não representam pesos8/32.
    for n in ([8,32] if estado==64 else [8]):
        refs.update({f'estado{n}_{s}':refs['estado16_42'] for s in ciclo.SEEDS})
    return refs


class Sequencia(unittest.TestCase):
    def test_uma_alteracao_seeds_orcamento(self):
        for n in (32,64):
            c=ciclo.configuracao(n);self.assertEqual(c['seeds'],[17,42,2026,7,123,31415]);self.assertEqual(c['mamba']['estado'],n)
        original=ciclo.ler_json
        def mudar(p):
            c=original(p)
            if Path(p).name=='mamba_estado32_001.json':c['treino']['taxa_aprendizado']=.1
            return c
        with patch.object(ciclo,'ler_json',side_effect=mudar),self.assertRaises(ValueError):ciclo.configuracao(32)
        with self.assertRaises(ValueError):ciclo.configuracao(128)

    def test_autorizacao_vinculada(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'auth.json';a={'ordem':[32,64],'ajustes_reais_total':12,'seeds':ciclo.SEEDS,
                'execucoes':{'32':'id32','64':'id64'},'mensagem_usuario':'fixture'}
            salvar_json(p,a);ciclo.validar_autorizacao(p,32,'id32')
            with self.assertRaises(ValueError):ciclo.validar_autorizacao(p,32,'outro')
            a['ajustes_reais_total']=18;salvar_json(p,a)
            with self.assertRaises(ValueError):ciclo.validar_autorizacao(p,64,'id64')

    def _fila(self,p,estados):
        execucoes={str(n):{'id':f'id{n}','pasta':f'fixture{n}','congelamento_sha256':'sintetico'} for n in (32,64)}
        for n in (32,64):salvar_json(p/f'estado{n}/execucao.json',execucoes[str(n)])
        salvar_json(p/'fila/congelamento.json',{'ordem':[32,64],'execucoes':execucoes})
        salvar_json(p/'auth.json',{'execucoes':{k:v['id'] for k,v in execucoes.items()}})
        return execucoes

    def test_fila_sequencial_sem_reexecutar_concluido(self):
        for ja32 in (False,True):
            with self.subTest(estado32_concluido=ja32),tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp);estados={32:'concluido' if ja32 else 'preparado',64:'preparado'};eventos=[];self._fila(p,estados)
                def executar(n,*args):
                    if n==64:self.assertIn(('conferir',32),eventos)
                    eventos.append(('executar',n));estados[n]='concluido'
                def conferir(n):self.assertEqual(estados[n],'concluido');eventos.append(('conferir',n))
                with patch.object(ciclo,'REGISTROS',p),patch.object(ciclo,'estado_atual',side_effect=lambda n:estados[n]), \
                     patch.object(ciclo,'executar',side_effect=executar),patch.object(ciclo,'conferir_conclusao',side_effect=conferir):
                    ciclo.executar_fila(p/'auth.json')
                esperado=([('executar',32)] if not ja32 else [])+[('conferir',32),('executar',64),('conferir',64)]
                self.assertEqual(eventos,esperado)

    def test_falha32_bloqueia64(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);self._fila(p,{})
            with patch.object(ciclo,'REGISTROS',p),patch.object(ciclo,'estado_atual',return_value='preparado'), \
                 patch.object(ciclo,'executar',side_effect=RuntimeError('falha artificial')) as executar, \
                 patch.object(ciclo,'conferir_conclusao') as conferir:
                with self.assertRaises(RuntimeError):ciclo.executar_fila(p/'auth.json')
                self.assertEqual(executar.call_count,1);self.assertEqual(executar.call_args.args[0],32);conferir.assert_not_called()
            self.assertEqual(ler_json(p/'fila/progresso.json')['status'],'interrompido')

    def test_executor_seis_por_estado_publicacao_e_herancas(self):
        for n in (32,64):
            refs=referencias_sinteticas(n);antes={k:sha256(p/'conclusao.json') for k,p in refs.items()}
            consumo=ConsumoModelos(conjunto(),'sintetico');c=ciclo.configuracao(n)
            c['divisao']={k:[str(pd.Timestamp(t).date()) for t in v] for k,v in consumo._conjunto.contrato['divisao'].items()};c['bootstrap']['replicas']=5
            with self.subTest(estado=n),tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp);f={'id':f'fixture{n}','contrato':{'configuracao':c,'fontes':{}}};chamadas=[]
                salvar_json(p/'progresso.json',{'status':'preparado'})
                salvar_json(p/'auth.json',{'ordem':[32,64],'ajustes_reais_total':12,'seeds':ciclo.SEEDS,'execucoes':{str(n):f['id']},'mensagem_usuario':'fixture'})
                def ajustar(consumo,nome,seed,*args):
                    self.assertEqual(nome,'mamba');chamadas.append(seed);return None,{'parametros':ciclo.PARAMETROS[n]}
                def avaliar(consumo,partes,nome,cfg,t,*args):
                    for arquivo in ('resultado.json','previsoes_validacao.parquet','previsoes_teste.parquet','previsoes_operacional.parquet'):
                        shutil.copy2(refs['estado16_42']/arquivo,t/arquivo)
                minutos=np.ones((31*1440,6));minutos[:,:4]=100;primeiro=int(pd.Timestamp('2021-01-01T00:00Z').timestamp()//60)
                with patch.object(ciclo,'conferir_execucao',return_value=(p,f,consumo,consumo._conjunto.partes,refs)), \
                     patch.object(ciclo,'ajustar',side_effect=ajustar),patch.object(ciclo,'avaliar',side_effect=avaliar), \
                     patch('experimento_estados_ampliados.publicacao.carregar_minutos',return_value=(minutos,primeiro)):
                    ciclo.executar(n,p/'auth.json');self.assertEqual(chamadas,ciclo.ORDEM)
                    with self.assertRaises(ValueError):ciclo.executar(n,p/'auth.json',retomar=True)
                pub=p/ler_json(p/'publicacao.json')['pasta'];conferir_arquivos(pub,ler_json(pub/'manifesto.json')['arquivos'])
                r=ler_json(pub/'resultados.json');self.assertEqual(len(r['por_ajuste']),20 if n==32 else 26)
                self.assertEqual(len(r['medias']['teste'][f'estado{n}_seis']['mse_por_seed']),6)
                self.assertEqual(len(r['medias']['teste']['estado16_tres']['mse_por_seed']),3)
                if n==64:self.assertIn('estado64_seis_menos_estado32_seis',r['contrastes']['teste'])
            self.assertEqual(antes,{k:sha256(p/'conclusao.json') for k,p in refs.items()})
