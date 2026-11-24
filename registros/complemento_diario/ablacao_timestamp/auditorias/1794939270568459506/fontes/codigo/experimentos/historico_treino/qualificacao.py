"""Qualifica o contraste, fontes e recarga antes de qualquer ajuste real."""
from pathlib import Path
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, salvar_json, agora
from entradas_modelo.operacional_futuros import preparar
from .contrato import calendario, FASES


def conferir_par(a, b):
    if a.canais != b.canais or a.contexto != b.contexto:
        raise ValueError('Contrato de entrada mudou além do histórico.')
    for fase in FASES:
        np.testing.assert_array_equal(a.indices[fase], b.indices[fase])
        np.testing.assert_array_equal(a.alvo[a.indices[fase]], b.alvo[b.indices[fase]])
    if not set(b.indices['treino']).issubset(a.indices['treino']) or len(b.indices['treino']) >= len(a.indices['treino']):
        raise ValueError('A janela móvel deve ser subconjunto próprio do treino acumulado.')
    return {nome: {'acumulado': len(a.indices[nome]), 'movel12': len(b.indices[nome])} for nome in a.indices}


def sintetico(destino, receita):
    import torch
    from treinamento.operacional_futuros import ajustar
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA oficial obrigatório.')
    d = Path(destino); d.mkdir(parents=True, exist_ok=False)
    rng = np.random.default_rng(190)
    n = 24 * 800
    t = pd.date_range('2021-01-01', periods=n, freq='h', tz='UTC').as_unit('ms').asi8
    c = 100 * np.exp(np.cumsum(rng.normal(0, .001, n)))
    q = pd.DataFrame(dict(open_time=t, close_time=t+3599999, open=c, high=c*1.002,
                          low=c*.998, close=c, volume=rng.uniform(1, 100, n)))
    y = np.column_stack([np.sin(np.arange(n)/30)*.01, np.cos(np.arange(n)/30)*.01])
    cal = dict(id='Q', treino=['2021-01-01','2022-07-01'], validacao=['2022-07-01','2022-08-01'],
               calibracao=['2022-08-01','2022-09-01'], comparacao=['2022-09-01','2022-10-01'])
    a = preparar(q, receita, calendario(cal,'acumulado'), y)
    b = preparar(q, receita, calendario(cal,'movel12'), y)
    cobertura = conferir_par(a,b)
    # Treinamento artificial curto percorre o treinador de produção e duas escalas.
    for nome, dados in [('acumulado',a),('movel12',b)]:
        dados.indices = {k:v[:128 if k=='treino' else 32] for k,v in dados.indices.items()}
        for repeticao in (1,2):
            ajustar(dados, receita, 42, d/f'{nome}_{repeticao}', {'tipo':'qualificacao_artificial','braco':nome}, epocas=2, paciencia=2)
        for fase in FASES:
            x=np.load(d/f'{nome}_1'/(fase+'.npz')); z=np.load(d/f'{nome}_2'/(fase+'.npz'))
            np.testing.assert_allclose(x['previsoes'],z['previsoes'],rtol=0,atol=1e-7)
    return {'status':'aprovado','utc':agora(),'gpu':torch.cuda.get_device_name(),'torch':torch.__version__,
            'treinos_reais':0,'repeticao_sintetica_atol':1e-7,'recarga_exata':True,'cobertura':cobertura}
