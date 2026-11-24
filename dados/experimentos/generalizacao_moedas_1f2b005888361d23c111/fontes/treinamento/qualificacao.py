"""Qualificação sintética integral + conferência dos dados reais sem treiná-los."""
import contextlib
import os
import traceback
import unittest
from uuid import uuid4
from infraestrutura.artefatos import RAIZ, salvar_json, agora, sha256
from modelos.conferencia import conferir_consumo
from .ciclo import fontes, REGISTROS
from .configuracao import carregar
from .ambiente import conferir


def qualificar():
    pasta = REGISTROS / 'qualificacoes' / uuid4().hex
    pasta.mkdir(parents=True)
    ambiente = conferir()
    originais = fontes()
    salvar_json(pasta/'inicio.json', {'utc':agora(),'ambiente':ambiente,'fontes':originais,
                                    'escopo':'somente ajustes sintéticos; dados reais apenas conferência'})
    anterior = os.environ.get('CC_QUALIFICACAO')
    os.environ['CC_QUALIFICACAO'] = str(pasta)
    try:
        suite = unittest.TestSuite()
        for nome in ('tests_dados','tests_modelos','tests_treinamento'):
            suite.addTests(unittest.TestLoader().discover(str(RAIZ/nome)))
        with (pasta/'testes.log').open('w',encoding='utf-8',buffering=1) as log:
            with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                resultado=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
        if not resultado.wasSuccessful() or resultado.skipped:
            raise ValueError('Qualificação requer todos os testes aprovados, sem skips.')
        c=carregar()
        salvar_json(pasta/'conferencia_entradas.json',conferir_consumo(RAIZ/c['entradas_pasta']))
        # Integração do adapter Spot com a base auditada anterior: leitura, sem operação/modelo real.
        from avaliacao.mercado import carregar_minutos
        import numpy as np
        minutos, primeiro=carregar_minutos(RAIZ/c['mercado_pasta'],c['par'])
        anterior_minutos=np.load(RAIZ/'dados/processados/retorno24_d25f6a93a9900725f51e/BTCUSDT/minutos.npy',mmap_mode='r')
        if primeiro != 26824320 or not np.array_equal(minutos,anterior_minutos,equal_nan=True):
            raise ValueError('Adaptação dos minutos divergiu da política qualificada.')
        salvar_json(pasta/'conferencia_spot_entrada.json',{'primeiro_minuto':primeiro,'dimensoes':list(minutos.shape),
                    'igualdade_exata_incluindo_ausencias':True,'simulacao_mercado_executada':False})
        if fontes()!=originais:
            raise ValueError('Fontes mudaram durante a qualificação.')
        arquivos={p.relative_to(pasta).as_posix():sha256(p) for p in pasta.rglob('*') if p.is_file()}
        salvar_json(pasta/'qualificacao.json',{'status':'aprovado','utc':agora(),'fontes':originais,'ambiente':ambiente,
                    'testes':resultado.testsRun,'skips':0,'artefatos':arquivos,'treinamentos_mercado':0,
                    'natureza':'qualificação técnica sintética, não resultado científico'})
    except BaseException:
        salvar_json(pasta/'falha.json',{'utc':agora(),'erro':traceback.format_exc()})
        raise
    finally:
        if anterior is None:
            os.environ.pop('CC_QUALIFICACAO',None)
        else:
            os.environ['CC_QUALIFICACAO']=anterior
    return pasta/'qualificacao.json'
