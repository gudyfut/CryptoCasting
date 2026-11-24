"""Recalcula a intervenção de ramos a partir das previsões preservadas."""
import json
from pathlib import Path

import numpy as np

from infraestrutura.artefatos import RAIZ, agora, conferir_arquivos, ler_json, salvar_json, sha256


def principal():
    reg = RAIZ / 'registros/walkforward_diario'
    ptr = ler_json(reg / 'diagnostico_ramos_tentativa_002.json')
    assert ptr['situacao'] == 'concluido_conferido'
    p = RAIZ / ptr['execucao']['pasta']
    assert sha256(p / 'congelamento.json') == ptr['execucao']['congelamento_sha256']
    assert sha256(p / 'fechamento.json') == ptr['fechamento_sha256']
    f, fim = ler_json(p / 'congelamento.json'), ler_json(p / 'fechamento.json')
    conferir_arquivos(p, fim['arquivos'])
    original = RAIZ / f['execucao']['pasta']
    assert sha256(original / 'fechamento.json') == f['fechamento_sha256']
    config = ler_json(original / 'congelamento.json')
    resultados = ler_json(p / 'resultado.json')['resultados']
    assert len(resultados) == 12
    for linha in resultados:
        b, seed = linha['bloco'], linha['seed']
        with np.load(original / b / 'dados/teste.npz', allow_pickle=False) as q:
            y, t = q['y'].copy(), q['origens_ms'].copy()
        with np.load(p / f'{b}_A_{seed}.npz', allow_pickle=False) as q:
            np.testing.assert_array_equal(t, q['origens_ms'])
            normal, sem = q['previsao'].copy(), q['previsao_sem_ramos'].copy()
        with np.load(original / 'publicacao' / b / 'previsoes' / f'A_{seed}.npz', allow_pickle=False) as q:
            np.testing.assert_array_equal(normal, q['previsoes_retorno'])
        delta = normal - sem
        limite = config['configs_blocos'][b]['operacoes']['filtro_retorno_absoluto']
        decisao = lambda v: np.where(v > limite, 1, np.where(v < -limite, -1, 0))
        esperado = [np.max(abs(delta)), np.sqrt(np.mean(delta**2)), np.mean((normal-y)**2), np.mean((sem-y)**2)]
        observado = [linha[k] for k in ('max_diferenca', 'rms_diferenca', 'mse_normal', 'mse_sem_ramos')]
        np.testing.assert_allclose(esperado, observado, rtol=1e-13, atol=1e-15)
        assert linha['decisoes_diferentes'] == int(np.sum(decisao(normal) != decisao(sem)))
    destino = reg / 'conferencia_sondagem.json'
    assert not destino.exists()
    salvar_json(destino, dict(utc=agora(), situacao='aprovada', execucao=ptr['execucao'],
                checkpoints=12, fonte_sha256=sha256(__file__),
                limite='Recalcula diferenças preservadas; não repetiu inferência CUDA nem retreinamento.'))
    print('SONDAGEM_AUDITADA', len(resultados), flush=True)


if __name__ == '__main__':
    principal()
