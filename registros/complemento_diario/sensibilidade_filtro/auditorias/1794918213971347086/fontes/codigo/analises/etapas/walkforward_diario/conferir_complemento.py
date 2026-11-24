"""Confere épocas, métricas e contabilidade após o fechamento do walk-forward."""
import io
import json
import zipfile
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from infraestrutura.artefatos import RAIZ, agora, conferir_arquivos, ler_json, salvar_json, sha256


def principal():
    reg = RAIZ / 'registros/walkforward_diario'
    ptr = ler_json(reg / 'execucao.json')
    raiz = RAIZ / ptr['pasta']
    assert sha256(raiz / 'congelamento.json') == ptr['congelamento_sha256']
    f = ler_json(raiz / 'congelamento.json')
    fim = ler_json(raiz / 'fechamento.json')
    assert fim['situacao'] == 'concluido_controles_aprovados'
    conferir_arquivos(raiz, fim['arquivos'])
    pred = ler_json(raiz / 'publicacao/previsao.json')
    ops = ler_json(raiz / 'publicacao/operacoes.json')
    assert len(ops['carteiras']) + len(ops['falhas']) == 108
    diario = pd.read_parquet(RAIZ / f['referencias']['diario']['pasta'] / 'diario.parquet').set_index('open_time', drop=False)
    ajustes = previsoes = carteiras = populacoes = janelas = 0
    maior_erro = 0.0
    with zipfile.ZipFile(raiz / 'publicacao/carteiras.zip') as z:
        assert z.testzip() is None
        for bloco in f['configuracao']['blocos']:
            b = bloco['id']
            escala_registrada = f['escalas'][b]
            datas_treino = np.arange(escala_registrada['primeiro_candle_ms'],
                                     escala_registrada['ultimo_candle_ms'] + 1, 86_400_000)
            unicos = diario.loc[datas_treino, ['open_time', 'open', 'high', 'low', 'close', 'volume']].to_numpy()
            unicos[:, 0] /= 1000
            unicos[:, 5] /= f['configs_blocos'][b]['volume_divisor']
            unicos = unicos.astype(np.float32).astype(np.float64)
            assert len(unicos) == escala_registrada['candles_unicos']
            np.testing.assert_allclose(unicos.mean(axis=0), escala_registrada['media'], rtol=1e-13, atol=1e-10)
            np.testing.assert_allclose(unicos.std(axis=0), escala_registrada['escala'], rtol=1e-13, atol=1e-10)
            limites = [f['configuracao']['treino_inicio'], bloco['treino_fim'],
                       bloco['validacao_fim'], bloco['teste_fim']]
            milissegundos = [int(datetime.fromisoformat(d).replace(tzinfo=timezone.utc).timestamp() * 1000)
                             for d in limites]
            for indice, fase in enumerate(('treino', 'validacao', 'teste')):
                with np.load(raiz / b / 'dados' / f'{fase}.npz', allow_pickle=False) as q:
                    t, fim_alvo = q['origens_ms'], q['fim_alvo_ms']
                    assert np.all(np.diff(t) == 86_400_000)
                    assert np.all(fim_alvo - t == 86_399_999)
                    assert np.all(t >= milissegundos[indice]) and np.all(fim_alvo < milissegundos[indice + 1])
                    np.testing.assert_allclose(q['preco_alvo'] / q['ultimo_close'] - 1, q['y'],
                                               rtol=0, atol=1e-14)
                    indices = t[:, None] - np.arange(14, 0, -1) * 86_400_000
                    bruto = diario.loc[indices.ravel(), ['open_time', 'open', 'high', 'low', 'close', 'volume']]
                    bruto = bruto.to_numpy().reshape(len(t), 14, 6)
                    bruto[:, :, 0] /= 1000
                    bruto[:, :, 5] /= f['configs_blocos'][b]['volume_divisor']
                    medias, escalas = np.array(f['escalas'][b]['media']), np.array(f['escalas'][b]['escala'])
                    refeito = ((bruto.astype(np.float32).astype(np.float64) - medias) / escalas).astype(np.float32)
                    np.testing.assert_array_equal(refeito.transpose(0, 2, 1), q['x'])
                    np.testing.assert_array_equal(diario.loc[t, 'close'].to_numpy(), q['preco_alvo'])
                    np.testing.assert_array_equal(diario.loc[t - 86_400_000, 'close'].to_numpy(), q['ultimo_close'])
                    janelas += len(t)
                populacoes += 1
            with np.load(raiz / b / 'dados/teste.npz', allow_pickle=False) as q:
                alvo = q['y'].copy()
                origens = q['origens_ms'].copy()
            for modelo in ('A', 'L'):
                for seed in f['configuracao']['seeds']:
                    p = raiz / b / 'ajustes' / f'{modelo}_{seed}'
                    epocas = [json.loads(linha) for linha in (p / 'epocas.jsonl').read_text(encoding='utf-8').splitlines()]
                    selecao = ler_json(p / 'selecao.json')
                    assert [e['epoca'] for e in epocas] == list(range(1, 201))
                    melhor = min(epocas, key=lambda e: e['rmse_global_validacao_retorno'])
                    assert selecao['epoca'] == melhor['epoca']
                    np.testing.assert_allclose(selecao['rmse_validacao'], melhor['rmse_global_validacao_retorno'],
                                               rtol=0, atol=1e-15)
                    assert sha256(p / selecao['checkpoint']) == selecao['sha256']
                    ajustes += 1
                for nome in [f'{modelo}_{s}' for s in f['configuracao']['seeds']] + [f'{modelo}_ensemble']:
                    with np.load(raiz / 'publicacao' / b / 'previsoes' / f'{nome}.npz', allow_pickle=False) as q:
                        np.testing.assert_array_equal(q['origens_ms'], origens)
                        np.testing.assert_array_equal(q['alvo_retorno'], alvo)
                        valor = q['previsoes_retorno']
                        mse = float(np.mean((valor - alvo) ** 2))
                        mae = float(np.mean(np.abs(valor - alvo)))
                        rmse = float(np.sqrt(mse))
                        m = pred[b]['metricas'][nome]
                        np.testing.assert_allclose([m['mse_retorno'], m['mae_retorno'], m['rmse_retorno']],
                                                   [mse, mae, rmse], rtol=1e-12, atol=1e-15)
                        if np.any(alvo > 0) and np.any(alvo < 0) and np.any(valor != 0):
                            ba = ((valor[alvo > 0] > 0).mean() + (valor[alvo < 0] < 0).mean()) / 2
                            np.testing.assert_allclose(m['acerto_balanceado'], ba, atol=1e-14)
                    previsoes += 1
            for linha in (v for v in ops['carteiras'] if v['bloco'] == b):
                with np.load(io.BytesIO(z.read(linha['membro'] + '/curva.npz')), allow_pickle=False) as curva:
                    np.testing.assert_array_equal(curva['origens_ms'], origens)
                    saldos = curva['saldos_diarios'].copy()
                dados = json.loads(z.read(linha['membro'] + '/resultado.json'))
                met = dados['metricas']
                np.testing.assert_allclose(saldos[-1], met['capital_final'], rtol=1e-12, atol=1e-7)
                esperado = (dados['regras']['capital_inicial'] + met['pnl_movimento_contrato']
                            + met['funding'] - met['comissoes'] - met['custo_slippage_ticks'])
                erro = abs(met['capital_final'] - esperado)
                maior_erro = max(maior_erro, erro)
                assert erro < 1e-6
                carteiras += 1
    assert ajustes == 24 and previsoes == 32 and populacoes == 12 and carteiras == len(ops['carteiras'])
    destino = reg / 'conferencia_complementar.json'
    assert not destino.exists()
    salvar_json(destino, dict(utc=agora(), situacao='aprovada', execucao=ptr,
                ajustes=ajustes, previsoes=previsoes, populacoes=populacoes, janelas=janelas,
                carteiras=carteiras, falhas=ops['falhas'],
                erro_contabil_maximo=maior_erro, fonte_sha256=sha256(__file__),
                limite='Não reexecuta treinamentos nem verifica liquidação ou execução reais.'))
    print('CONFERENCIA_COMPLEMENTAR_APROVADA', ajustes, previsoes, carteiras, flush=True)


if __name__ == '__main__':
    principal()
