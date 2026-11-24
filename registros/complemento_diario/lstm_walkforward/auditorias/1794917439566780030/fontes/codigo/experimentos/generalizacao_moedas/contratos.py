"""Receita por moeda e verificações causais, sem selecionar por resultados."""
from copy import deepcopy
import numpy as np
import pandas as pd
from entradas_modelo.padronizacao_diaria import preparar_com_escalas

SIMBOLOS = ('ETHUSDT', 'BNBUSDT', 'XRPUSDT')


def configurar(referencia, simbolo, contrato):
    assert simbolo in SIMBOLOS and contrato['simbolo'] == simbolo
    c = deepcopy(referencia)
    c['ciclo'] = 'generalizacao_moedas_001_' + simbolo
    c['simbolo'] = simbolo
    c['periodos']['treino'][0] = pd.Timestamp(contrato['inicio_diario_ms'], unit='ms', tz='UTC').strftime('%Y-%m-%d')
    c['operacoes'].update(contrato['regras_simbolo'])
    c['antecessora'] = 'f3f8772670f244779ad7'
    c['exposicao'] = 'Receita escolhida retrospectivamente em BTC; outras moedas já presentes em estudos antigos. Não afirmar holdout intocado.'
    assert c['normalizar'] and c['treinamento']['weight_decay'] == .001
    assert c['treinamento']['taxa'] == .01 and c['seeds'] == [42, 17, 2026]
    return c


def preparar(diario, c):
    dados, escalas = preparar_com_escalas(diario, c)
    assert escalas['ultimo_candle_ms'] < int(pd.Timestamp('2024-01-01', tz='UTC').timestamp()*1000)
    for fase, z in dados.items():
        assert z['x'].shape == (len(z['y']), 6, 14) and z['x'].dtype == np.float32
        assert np.isfinite(z['x']).all() and np.isfinite(z['y']).all()
        assert np.all(np.diff(z['origens_ms']) == 86400000)
        assert np.all(z['fim_alvo_ms'] == z['origens_ms'] + 86399999)
        fim = int(pd.Timestamp(c['periodos'][fase][1], tz='UTC').timestamp()*1000)
        assert np.all(z['fim_alvo_ms'] < fim)
        np.testing.assert_array_equal(z['y'], z['preco_alvo']/z['ultimo_close']-1)
    assert len(dados['validacao']['y']) == 351 and len(dados['teste']['y']) == 350
    return dados, escalas


def reconciliar_diario_minuto(pasta):
    diario = pd.read_parquet(pasta/'diario.parquet').set_index('open_time')
    minuto = pd.read_parquet(pasta/'klines.parquet', columns=['open_time','open','high','low','close','volume'])
    agrupado = minuto.groupby(minuto.open_time//86400000).agg(open=('open','first'), high=('high','max'),
        low=('low','min'), close=('close','last'), volume=('volume','sum'))
    agrupado.index = agrupado.index*86400000
    observado = diario.loc[agrupado.index, agrupado.columns]
    np.testing.assert_allclose(agrupado.iloc[:,:4], observado.iloc[:,:4], rtol=1e-10, atol=1e-8)
    divergente=~np.isclose(agrupado.volume, observado.volume, rtol=1e-8, atol=1e-4)
    diferencas=[]
    for t in agrupado.index[divergente]:
        assert int(t) in (1736812800000,1738108800000), 'Divergência de volume ainda não diagnosticada'
        diferencas.append({'dia_ms':int(t),'diario_oficial':float(observado.loc[t,'volume']),
                          'soma_minutos':float(agrupado.loc[t,'volume']),
                          'delta_relativo':float(agrupado.loc[t,'volume']/observado.loc[t,'volume']-1)})
    return {'dias':len(agrupado), 'ohlc_concordante':True, 'volume_concordante':not len(diferencas),
            'divergencias_volume':diferencas,
            'decisao':'Preservar volume do arquivo diário oficial como na referência, sem mesclar revisões API ou substituir por soma de minutos. Divergências conhecidas 14/29 janeiro2025 registradas antes de treinar.',
            'limite':'Duas granularidades da mesma fonte; não constitui fonte independente nem concordância integral de volume.'}
