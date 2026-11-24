"""Recalcula o critério de seleção nos vetores de validação preservados."""
import argparse
import math
import numpy as np
from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256
from .comum import contexto, pais, carregar_npz, conferir_unidade
from .inventario import REG, relativo


def executar(etapa):
    _, p, f = contexto(etapa)
    refs = pais()
    resultados = []
    for ajuste in sorted((p / 'ajustes').iterdir()):
        conferir_unidade(ajuste)
        nome = ajuste.name
        if nome == 'controle_fixa_42':
            origem = refs['fixa'] / 'BTCUSDT/dados/validacao.npz'
        elif nome.startswith('controle_original'):
            origem = refs['walkforward'] / 'B1/dados/validacao.npz'
        else:
            bloco = nome.split('_')[0] if not nome.startswith('controle_') else 'B1'
            origem = p / bloco / 'dados/validacao.npz'
        real = carregar_npz(origem)
        guardado = carregar_npz(ajuste / 'validacao.npz')
        for k, v in real.items():
            if k != 'x':
                np.testing.assert_array_equal(v, guardado[k])
        erro = math.sqrt(math.fsum((float(a)-float(b))**2 for a, b in zip(guardado['previsoes'], real['y']))/len(real['y']))
        s = ler_json(ajuste / 'selecao.json')
        np.testing.assert_allclose(erro, s['rmse_validacao'], rtol=1e-12, atol=1e-15)
        resultados.append(dict(ajuste=nome, n=len(real['y']), rmse_recalculado=erro,
            rmse_selecao=s['rmse_validacao'], diferenca=erro-s['rmse_validacao'],
            origem=relativo(origem), origem_sha256=sha256(origem), previsoes_sha256=sha256(ajuste / 'validacao.npz')))
    assert len(resultados) == (14 if etapa == 'lstm_walkforward' else 28)
    destino = REG / etapa / 'criterio_validacao_recalculado.json'
    assert not destino.exists(), 'Conferência já preservada.'
    salvar_json(destino, dict(utc=agora(), situacao='aprovada', ajustes=len(resultados), resultados=resultados,
        fonte=dict(arquivo=relativo(__file__), sha256=sha256(__file__)),
        metodo='Alvos/metadados cotejados com dados preparados; RMSE por math.fsum a partir das previsões recarregadas.'))
    print('CRITERIO_VALIDACAO_RECALCULADO', len(resultados), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('etapa', choices=['lstm_walkforward', 'ablacao_timestamp'])
    executar(parser.parse_args().etapa)
