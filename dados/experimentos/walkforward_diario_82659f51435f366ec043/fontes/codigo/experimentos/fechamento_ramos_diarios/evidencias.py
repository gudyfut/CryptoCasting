"""Herança verificável e preservação; funciona no Windows sem importar torch."""
import json
from copy import deepcopy
from pathlib import Path
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, ler_json, sha256, salvar_json, conferir_arquivos
from entradas_modelo.padronizacao_diaria import preparar_com_escalas
from experimentos.eixo_temporal_diario.evidencias import inspecionar as inspecionar_fatorial
from .contratos import CFG, REG, FASES, conferir, configuracao_moeda, receita, selecionar_prefixo


def historia(p):
    return [json.loads(l) for l in (p/'epocas.jsonl').read_text(encoding='utf-8').splitlines()]


def provar_ajuste(p, cfg, seed):
    h = historia(p); escolhido = selecionar_prefixo(h)
    s = ler_json(p/'selecao.json'); i = ler_json(p/'inicio.json')
    assert len(h) in (200, 1000)
    assert s['epoca'] == escolhido['epoca']
    assert s['rmse_validacao'] == escolhido['rmse_global_validacao_retorno']
    assert sha256(p/s['checkpoint']) == s['sha256']
    assert i['seed'] == seed
    anterior = deepcopy(i['configuracao']); anterior['epocas'] = 200
    anterior.setdefault('politica_penalizacao', 'uniforme')
    assert anterior == cfg['treinamento'], (p, anterior, cfg['treinamento'])
    assert ler_json(p/'conclusao.json')['situacao'] == 'concluido'
    return dict(pasta=p.relative_to(RAIZ).as_posix(), epoca=s['epoca'], checkpoint=s,
                historico_sha256=sha256(p/'epocas.jsonl'), epocas_originais=len(h),
                prefixo200_completo=True, minimo_prefixo_igual_selecao=True)


def preservar_fechado(p, preservacao):
    fecho = ler_json(p/'fechamento.json')
    assert fecho['situacao'] == 'concluido_conferido'
    conferir_arquivos(p, fecho['arquivos'])
    if (p/'congelamento.json').exists():
        f = ler_json(p/'congelamento.json')
        if 'fontes' in f: conferir_arquivos(p/'fontes', f['fontes'])
    for arquivo in p.rglob('*'):
        if arquivo.is_file(): preservacao[arquivo.relative_to(RAIZ).as_posix()] = sha256(arquivo)


def inspecionar():
    c = ler_json(CFG)
    herdado = inspecionar_fatorial(ler_json(RAIZ/'configuracoes/eixo_temporal_diario_001.json'))
    preservacao = herdado['preservacao']
    ptr = herdado['continuidade']; f_cont = ler_json(RAIZ/ptr['pasta']/'congelamento.json')
    conferir(c, f_cont['moedas'])
    for nome in ('eixo_temporal_diario', 'penalizacao_seletiva_diaria', 'ablacao_linear_diaria'):
        pp = ler_json(RAIZ/f'registros/{nome}/execucao.json')
        assert sha256(RAIZ/pp['pasta']/'congelamento.json') == pp['congelamento_sha256']
        preservar_fechado(RAIZ/pp['pasta'], preservacao)
    linear = ler_json(RAIZ/'registros/ablacao_linear_diaria/execucao.json')
    modelos_l = ler_json(RAIZ/linear['pasta']/'modelos.json')
    indice = ler_json(RAIZ/'registros/ensemble_2026/modelos_utilizados.json')
    resultado = {}
    for simbolo, info in f_cont['moedas'].items():
        cfg = configuracao_moeda(c, simbolo); base = RAIZ/info['base']
        preservar_fechado(base, preservacao)
        assert ler_json(base/'controle.json')['aprovado']
        diario, mercado = info['diario'], info['mercado']
        for ref in (diario, mercado):
            p = RAIZ/ref['pasta']; assert sha256(p/'manifesto.json') == ref['manifesto_sha256']
            conferir_arquivos(p, ler_json(p/'manifesto.json')['arquivos'])
            preservacao[(p/'manifesto.json').relative_to(RAIZ).as_posix()] = sha256(p/'manifesto.json')
        dados, escalas = preparar_com_escalas(pd.read_parquet(RAIZ/diario['pasta']/'diario.parquet'), cfg)
        assert escalas == ler_json(base/'escalas.json')
        assert escalas['ultimo_candle_ms'] < 1704067200000
        modelos = {}; bases = {'A': info['base']}
        if simbolo == 'BTCUSDT':
            bases.update(B=herdado['referencias']['B']['ponteiro']['pasta'], L=linear['pasta'])
        for variante, caminho_base in bases.items():
            for seed in cfg['seeds']:
                chave = f'{variante}_{seed}'
                ajuste = RAIZ/modelos_l[chave]['pasta'] if variante == 'L' else RAIZ/caminho_base/'ajustes'/f'seed_{seed}'
                prova = provar_ajuste(ajuste, receita(cfg, variante), seed)
                prefixo = f'{variante}_{seed}' if variante == 'L' else str(seed)
                prova['previsoes'] = {fase:f'{caminho_base}/publicacao/previsoes/{fase}_{prefixo}.npz'
                                      for fase in ('validacao', 'teste')}
                for fase, caminho in prova['previsoes'].items():
                    with np.load(RAIZ/caminho, allow_pickle=False) as q:
                        for k in ('origens_ms', 'ultimo_close', 'fim_alvo_ms'):
                            np.testing.assert_array_equal(dados[fase][k], q[k])
                        np.testing.assert_array_equal(dados[fase]['y'], q['alvo_retorno'])
                modelos[chave] = prova
                if variante == 'A':
                    original = next(x for x in indice['modelos'] if x['simbolo']==simbolo and x['seed']==seed)
                    assert original['checkpoint_sha256'] == prova['checkpoint']['sha256']
                    assert RAIZ/original['checkpoint'] == ajuste/prova['checkpoint']['checkpoint']
        for fase, z in dados.items():
            assert z['x'].shape == (len(z['y']), 6, 14) and z['x'].dtype == np.float32
            assert all(np.isfinite(v).all() for v in z.values())
            assert np.all(np.diff(z['origens_ms']) == 86400000)
            assert np.all(z['fim_alvo_ms'] == z['origens_ms']+86399999)
            fim = pd.Timestamp(cfg['periodos'][fase][1], tz='UTC').value//1000000
            assert np.all(z['fim_alvo_ms'] < fim)
            np.testing.assert_array_equal(z['y'], z['preco_alvo']/z['ultimo_close']-1)
        assert [len(dados[f]['y']) for f in ('validacao', 'teste')] == [351, 350]
        resultado[simbolo] = dict(diario=diario, mercado_minuto=mercado, modelos=modelos,
                                  escalas=escalas, populacoes={fase:len(z['y']) for fase,z in dados.items()})
    # Conservar também interrupções/continuação da generalização, não só os vencedores publicados.
    geral = ler_json(RAIZ/'registros/generalizacao_moedas/execucao.json')
    for raiz in (RAIZ/geral['pasta'], RAIZ/'registros/generalizacao_moedas'):
        for arquivo in raiz.rglob('*'):
            if arquivo.is_file(): preservacao[arquivo.relative_to(RAIZ).as_posix()] = sha256(arquivo)
    return dict(moedas=resultado, continuidade=ptr, preservacao=preservacao,
                novos_ajustes_cientificos=12, novos_controles=8, epocas_novas=4000,
                limite='Herança prefixo200 comprovada em históricos; recargas CUDA e controles novos ainda obrigatórios.')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument('destino'); args = parser.parse_args()
    p = Path(args.destino); assert not p.exists()
    salvar_json(p, inspecionar()); print('REFERENCIAS_CONFERIDAS', flush=True)
