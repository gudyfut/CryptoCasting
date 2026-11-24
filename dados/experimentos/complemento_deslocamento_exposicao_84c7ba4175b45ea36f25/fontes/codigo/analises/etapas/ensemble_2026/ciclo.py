"""Avaliação do ensemble antigo em período posterior; nunca ajusta pesos/escalas."""
import argparse
from contextlib import contextmanager
from copy import deepcopy
import csv
from datetime import datetime, timezone
import io
import json
import math
import os
from pathlib import Path
import platform
import shutil
import traceback
import zipfile

import numpy as np
import pandas as pd

from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256, identidade, conferir_arquivos
from .entradas import preparar as preparar_janelas

REG = RAIZ / 'registros/ensemble_2026'
CFG = RAIZ / 'configuracoes/ensemble_2026_001.json'
DIA = 86400000


def contexto():
    ptr = ler_json(REG / 'execucao.json')
    p = RAIZ / ptr['pasta']
    assert sha256(p / 'congelamento.json') == ptr['congelamento_sha256']
    f = ler_json(p / 'congelamento.json')
    conferir_arquivos(RAIZ, f['fontes'])
    conferir_arquivos(p / 'fontes', f['fontes'])
    conferir_arquivos(RAIZ, f['pais'])
    return ptr, p, f


def estado(situacao, **campos):
    salvar_json(REG / 'estado.json', dict(utc=agora(), situacao=situacao, **campos))


@contextmanager
def etapa(nome):
    ptr, p, f = contexto()
    assert not (p / 'fechamento.json').exists(), 'Avaliação já encerrada.'
    assert not list(p.glob('incidente_*.json')), 'Investigar incidente antes de continuar.'
    lock = p / 'execucao.lock'
    with lock.open('x', encoding='utf-8') as arquivo:
        json.dump(dict(host=platform.node(), pid=os.getpid(), fase=nome, utc=agora()), arquivo)
    salvar_json(p / f'processo_{nome}.json', dict(host=platform.node(), pid=os.getpid(), utc=agora(), python=os.sys.executable))
    estado(nome, execucao=ptr)
    try:
        yield ptr, p, f
        contexto()
    except BaseException:
        salvar_json(p / f'incidente_{nome}.json', dict(utc=agora(), erro=traceback.format_exc()))
        estado('interrompido_preservado', execucao=ptr, fase=nome)
        raise
    finally:
        lock.unlink()


def preparar():
    assert not (REG / 'execucao.json').exists(), 'Não substituir execução existente.'
    cfg = ler_json(CFG)
    pai = ler_json(RAIZ / 'registros/continuidade_moedas/execucao.json')
    assert pai['id'] == cfg['referencia']
    pasta_pai = RAIZ / pai['pasta']
    assert sha256(pasta_pai / 'congelamento.json') == pai['congelamento_sha256']
    anterior = ler_json(pasta_pai / 'congelamento.json')
    conferir_arquivos(pasta_pai, ler_json(pasta_pai / 'manifesto.json')['arquivos'])
    pais = {str((pasta_pai / n).relative_to(RAIZ).as_posix()): sha256(pasta_pai / n)
            for n in ['congelamento.json', 'manifesto.json', 'resultados.json', 'carteiras.zip']}
    moedas = deepcopy(anterior['moedas'])
    for simbolo, info in moedas.items():
        base = RAIZ / info['base']
        for nome in ['escalas.json', 'fechamento.json']:
            arquivo = base / nome
            pais[arquivo.relative_to(RAIZ).as_posix()] = sha256(arquivo)
        for seed in cfg['seeds']:
            d = base / 'ajustes' / f'seed_{seed}'
            sel = ler_json(d / 'selecao.json')
            assert sha256(d / sel['checkpoint']) == sel['sha256']
            for arquivo in [d / 'selecao.json', d / sel['checkpoint'], base / 'publicacao/previsoes' / f'teste_{seed}.npz']:
                pais[arquivo.relative_to(RAIZ).as_posix()] = sha256(arquivo)
        diario = RAIZ / info['diario']['pasta'] / 'diario.parquet'
        pais[diario.relative_to(RAIZ).as_posix()] = sha256(diario)
    fontes = {}
    for pacote in ['codigo/analises/etapas/ensemble_2026', 'codigo/entradas_modelo', 'codigo/modelos',
                   'codigo/experimento_cryptomamba', 'codigo/experimentos/cryptomamba_reproducivel',
                   'codigo/experimentos/alvo_retorno_diario', 'codigo/simulacao_operacoes/continuidade_diaria',
                   'codigo/simulacao_operacoes/revisada', 'codigo/infraestrutura', 'testes/ensemble_2026']:
        for arquivo in (RAIZ / pacote).glob('*.py'):
            fontes[arquivo.relative_to(RAIZ).as_posix()] = sha256(arquivo)
    for nome in ['codigo/mercado_futuros/periodo_publico.py', 'codigo/mercado_futuros/multimoeda.py',
                 'codigo/mercado_futuros/historico_operacional.py', 'codigo/mercado_futuros/pipeline.py',
                 'codigo/experimentos/generalizacao_moedas/avaliacao.py', 'codigo/simulacao_operacoes/diaria_24h.py',
                 'codigo/experimentos/padronizacao_diaria/qualificacao.py',
                 'codigo/simulacao_operacoes/envelopes_marcacao.py', 'codigo/treinamento/otimizacao.py',
                 'configuracoes/ensemble_2026_001.json', 'docs/protocolo_ensemble_2026.md']:
        fontes[nome] = sha256(RAIZ / nome)
    for nome in ['exposicao_inventario.json', 'exposicao_complementar.json', 'exposicao.json']:
        caminho = REG / nome
        pais[caminho.relative_to(RAIZ).as_posix()] = sha256(caminho)
    f = dict(utc=agora(), configuracao=cfg, referencia=pai, moedas=moedas, fontes=fontes, pais=pais,
             autorizacao='Pesquisador autorizou ensemble BTC/ETH/BNB/XRP em2026 até último dia completo, mesmos modelos/regras, coleta necessária e comparação com comprar/manter; sem novos treinos.')
    codigo = identidade(f)[:20]
    p = RAIZ / 'dados/reavaliacoes' / f'ensemble_2026_{codigo}'
    p.mkdir(parents=True, exist_ok=False)
    for nome in fontes:
        destino = p / 'fontes' / nome
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(RAIZ / nome, destino)
    salvar_json(p / 'congelamento.json', f)
    ptr = dict(id=codigo, pasta=p.relative_to(RAIZ).as_posix(), congelamento_sha256=sha256(p / 'congelamento.json'))
    salvar_json(REG / 'execucao.json', ptr)
    salvar_json(REG / 'autorizacao.json', dict(utc=agora(), execucao=ptr, escopo=f['autorizacao'], treinar=False))
    estado('preparado_autorizado', execucao=ptr, novos_treinamentos=0)
    print(json.dumps(ptr), flush=True)


def mercado():
    from mercado_futuros.periodo_publico import coletar
    with etapa('coletando') as (ptr, p, f):
        assert not (p / 'mercados.json').exists()
        inicio = int(pd.Timestamp(f['configuracao']['inicio'], tz='UTC').timestamp() * 1000)
        fim = int(pd.Timestamp(f['configuracao']['fim_exclusivo'], tz='UTC').timestamp() * 1000)
        saida = {}
        for simbolo in f['configuracao']['moedas']:
            destino = RAIZ / 'dados/mercado/ensemble_2026' / ptr['id'] / simbolo
            mp = coletar(destino, simbolo, inicio, fim)
            mp['pasta'] = destino.relative_to(RAIZ).as_posix()
            saida[simbolo] = mp
            estado('coletando', execucao=ptr, moedas_concluidas=len(saida), total_moedas=4)
        salvar_json(p / 'mercados.json', saida)
        estado('mercados_conferidos', execucao=ptr, moedas_concluidas=4)


def conferir_mercado(ptr):
    d = RAIZ / ptr['pasta']
    assert sha256(d / 'manifesto.json') == ptr['manifesto_sha256']
    conferir_arquivos(d, ler_json(d / 'manifesto.json')['arquivos'])


def inferencia():
    os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
    import fcntl
    import torch
    from treinamento.otimizacao import fixar_seed
    from experimentos.alvo_retorno_diario.treinamento import carregar_rede, inferir
    from experimentos.padronizacao_diaria.qualificacao import ambiente
    with etapa('inferindo') as (ptr, p, f):
        assert not (p / 'inferencia.json').exists()
        with (RAIZ / 'registros/operacional_futuros/gpu.lock').open('a+b') as gpu:
            fcntl.flock(gpu, fcntl.LOCK_EX | fcntl.LOCK_NB)
            assert torch.cuda.is_available()
            salvar_json(p / 'ambiente_inferencia.json', ambiente())
            cfg = f['configuracao']
            inicio = int(pd.Timestamp(cfg['inicio'], tz='UTC').timestamp() * 1000)
            fim = int(pd.Timestamp(cfg['fim_exclusivo'], tz='UTC').timestamp() * 1000)
            origens = np.arange(inicio, fim, DIA, dtype=np.int64)
            mercados = ler_json(p / 'mercados.json')
            controles = []
            for simbolo, info in f['moedas'].items():
                conferir_mercado(mercados[simbolo])
                base = RAIZ / info['base']
                c = info['configuracao']
                escalas = ler_json(base / 'escalas.json')
                antigo = pd.read_parquet(RAIZ / info['diario']['pasta'] / 'diario.parquet')
                novo = pd.read_parquet(RAIZ / mercados[simbolo]['pasta'] / 'diario.parquet')
                completo = pd.concat([antigo[antigo.open_time >= inicio-14*DIA], novo], ignore_index=True)
                z = preparar_janelas(completo, origens, c, escalas)
                d = p / 'previsoes' / simbolo
                d.mkdir(parents=True, exist_ok=False)
                np.savez_compressed(d / 'entradas.npz', **z)
                precos = []
                for seed in cfg['seeds']:
                    fixar_seed(seed)
                    rede = carregar_rede(base / 'ajustes' / f'seed_{seed}', c)
                    antes = {k: v.detach().cpu().clone() for k, v in rede.state_dict().items()}
                    guardado = dict(np.load(base / 'publicacao/previsoes' / f'teste_{seed}.npz', allow_pickle=False))
                    passado = preparar_janelas(antigo, guardado['origens_ms'], c, escalas)
                    repetido = inferir(rede, passado['x'], lote=32)
                    np.testing.assert_array_equal(repetido, guardado['previsoes_retorno'])
                    retorno = inferir(rede, z['x'], lote=32)
                    np.testing.assert_array_equal(retorno, inferir(rede, z['x'], lote=32))
                    for chave, valor in rede.state_dict().items():
                        assert torch.equal(antes[chave], valor.detach().cpu()), chave
                    preco = z['ultimo_close'] * (1+retorno)
                    precos.append(preco)
                    np.savez_compressed(d / f'seed_{seed}.npz', origens_ms=origens, previsoes=preco, previsoes_retorno=retorno)
                    controles.append(dict(simbolo=simbolo, seed=seed, reproducao_2025_exata=True,
                                          repeticao_2026_exata=True, pesos_inalterados=True,
                                          previsoes_2025=len(repetido), previsoes_2026=len(retorno)))
                    del rede
                    torch.cuda.empty_cache()
                    print('INFERENCIA', simbolo, seed, len(retorno), 'CONTROLES_EXATOS', flush=True)
                # Mesma combinação em preço do executor anterior, não voto/maioria.
                media = np.mean(precos, axis=0)
                np.savez_compressed(d / 'ensemble.npz', origens_ms=origens, previsoes=media,
                                    previsoes_retorno=media/z['ultimo_close']-1, ultimo_close=z['ultimo_close'], y=z['y'])
                estado('inferindo', execucao=ptr, modelos_concluidos=len(controles), modelos_previstos=12)
            salvar_json(p / 'inferencia.json', dict(utc=agora(), controles=controles, novos_treinamentos=0,
                        escalas_reajustadas=False, modelos=12, previsoes_por_modelo=len(origens)))
            estado('previsoes_conferidas', execucao=ptr, modelos_concluidos=12)


def intervalo(diferenca, bloco):
    rng = np.random.default_rng(11112026)
    n = len(diferenca)
    replicas = []
    for _ in range(2000):
        indices = (rng.integers(0, n-bloco+1, int(np.ceil(n/bloco)))[:, None] + np.arange(bloco)).ravel()[:n]
        replicas.append(float(diferenca[indices].mean()))
    return dict(media_log_diaria=float(diferenca.mean()), ic95=np.quantile(replicas, [.025, .975]).tolist(),
                bloco=bloco, replicas=2000, limite='Ensemble fixo; reamostragem temporal, não de seeds; quatro moedas correlacionadas.')


def avaliar():
    from experimentos.generalizacao_moedas.avaliacao import carregar_mercado
    from simulacao_operacoes.continuidade_diaria.simulador import simular
    from simulacao_operacoes.continuidade_diaria.auditoria_grade import conferir
    with etapa('simulando') as (ptr, p, f):
        assert not (p / 'resultados.json').exists()
        assert len(ler_json(p / 'inferencia.json')['controles']) == 12
        mercados = ler_json(p / 'mercados.json')
        anterior = ler_json(RAIZ / f['referencia']['pasta'] / 'resultados.json')
        linhas, controles, intervalos, previsoes = [], [], {}, []
        with zipfile.ZipFile(p / 'carteiras.zip', 'x', compression=zipfile.ZIP_DEFLATED) as pacote:
            for simbolo, info in f['moedas'].items():
                # Controle de toda a carteira2025, com os mesmos sinais/quantidades.
                base = RAIZ / info['base']
                anteriores = [dict(np.load(base / 'publicacao/previsoes' / f'teste_{s}.npz', allow_pickle=False)) for s in f['configuracao']['seeds']]
                t0, u0 = anteriores[0]['origens_ms'], anteriores[0]['ultimo_close']
                pr0 = np.mean([a['previsoes'] for a in anteriores], axis=0)
                regras = deepcopy(info['configuracao']['operacoes'])
                regras['slippage_por_lado'] = .0001
                m0 = carregar_mercado(info['mercado'])
                velho, cv0 = simular(t0, pr0, u0, m0, regras, 'liquida')
                conferir(velho, cv0, m0, regras, 'liquida', t0, pr0, u0, None)
                esperado = next(x['metricas'] for x in anterior['resultados'] if x['moeda']==simbolo and x['fase']=='teste' and x['unidade']=='ensemble' and x['custo']==1 and x['modo']=='liquida')
                for k, v in esperado.items():
                    if isinstance(v, (int, float)):
                        np.testing.assert_allclose(velho['metricas'][k], v, atol=1e-7, rtol=1e-10)
                controles.append(dict(simbolo=simbolo, reproducao_ensemble_2025=True, retorno_liquido=esperado['retorno_liquido']))
                del m0
                conferir_mercado(mercados[simbolo])
                m = carregar_mercado(mercados[simbolo])
                z = dict(np.load(p / 'previsoes' / simbolo / 'ensemble.npz', allow_pickle=False))
                t, prev, ultimo = z['origens_ms'], z['previsoes'], z['ultimo_close']
                real, pred = z['y']/ultimo-1, prev/ultimo-1
                previsoes.append(dict(simbolo=simbolo, n=len(t), mse_retorno=float(np.mean((pred-real)**2)),
                                  mse_naive_retorno=float(np.mean(real**2)), mae_retorno=float(np.mean(abs(pred-real))),
                                  vies_retorno=float(np.mean(pred-real)), acerto_sinal=float(np.mean(np.sign(pred)==np.sign(real)))))
                intervalos[simbolo] = {}
                for custo in f['configuracao']['slippage_por_lado']:
                    regras = deepcopy(info['configuracao']['operacoes'])
                    regras['slippage_por_lado'] = custo
                    curvas = {}
                    for unidade in ['ensemble', 'comprar_manter']:
                        if unidade == 'ensemble':
                            r, cv = simular(t, prev, ultimo, m, regras, 'liquida')
                            auditoria = conferir(r, cv, m, regras, 'liquida', t, prev, ultimo, None)
                        else:
                            from simulacao_operacoes.diaria_24h import arredondar_preco
                            inicio = int(np.searchsorted(m['tempo'], t[0]+60000))
                            fill = arredondar_preco(float(m['negocio'][inicio, 0])*(1+custo), 1, regras['tick_preco'])
                            lotes = math.floor(regras['capital_inicial']*regras['fracao_nocional']/fill/regras['passo_quantidade'])
                            agenda = np.full(len(t), lotes, dtype=np.int64)
                            r, cv = simular(t, ultimo, ultimo, m, regras, 'agenda', 1, agenda)
                            auditoria = conferir(r, cv, m, regras, 'agenda', t, ultimo, ultimo, 1, agenda)
                        nome = f'{simbolo}/{unidade}/slippage_{custo:.4f}'
                        pacote.writestr(nome+'/resultado.json', json.dumps(dict(regras=regras, **r), ensure_ascii=False, allow_nan=False))
                        b = io.BytesIO()
                        np.savez_compressed(b, origens_ms=t, **cv)
                        pacote.writestr(nome+'/curva.npz', b.getvalue())
                        linhas.append(dict(simbolo=simbolo, unidade=unidade, slippage_por_lado=custo, membro=nome,
                                           metricas=r['metricas'], auditoria=auditoria))
                        curvas[unidade] = cv['saldos_diarios']
                    delta = np.diff(np.log(curvas['ensemble'])) - np.diff(np.log(curvas['comprar_manter']))
                    intervalos[simbolo][str(custo)] = {str(b): intervalo(delta, b) for b in [7, 14, 28]}
                    print('BACKTEST', simbolo, custo, len(linhas), '/24', flush=True)
                del m
        assert len(linhas) == 24 and len(controles) == 4
        salvar_json(p / 'resultados.json', dict(utc=agora(), execucao=ptr, carteiras=linhas, controles_2025=controles,
                    intervalos_ensemble_menos_comprar_manter=intervalos, metricas_previsoes=previsoes,
                    recorte=f['configuracao'], exposicao=ler_json(REG / 'exposicao.json'), novos_treinamentos=0))
        with (p / 'comparacao.csv').open('w', newline='', encoding='utf-8-sig') as arquivo:
            saida = [dict(simbolo=l['simbolo'], unidade=l['unidade'], slippage_por_lado=l['slippage_por_lado'], **l['metricas']) for l in linhas]
            escritor = csv.DictWriter(arquivo, fieldnames=list(saida[0]))
            escritor.writeheader()
            escritor.writerows(saida)
        contexto()
        salvar_json(p / 'manifesto.json', dict(utc=agora(), execucao=ptr,
                    arquivos={a.relative_to(p).as_posix(): sha256(a) for a in p.rglob('*') if a.is_file()
                              and a.name not in ['manifesto.json', 'execucao.lock'] and not a.name.startswith('processo_')}))
        salvar_json(p / 'fechamento.json', dict(utc=agora(), situacao='concluido_conferido', execucao=ptr,
                    carteiras=24, controles_inferencia=12, controles_financeiros_2025=4, novos_treinamentos=0,
                    fontes_pais_antes_depois_preservados=True, manifesto_sha256=sha256(p / 'manifesto.json')))
        salvar_json(REG / 'fechamento.json', dict(execucao=ptr, arquivo=(p / 'fechamento.json').relative_to(RAIZ).as_posix(), sha256=sha256(p / 'fechamento.json')))
        estado('concluido_conferido', execucao=ptr, carteiras_concluidas=24, novos_treinamentos=0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('acao', choices=['preparar', 'mercado', 'inferencia', 'avaliar', 'conferir'])
    acao = parser.parse_args().acao
    if acao == 'conferir':
        print(contexto()[0])
    else:
        globals()[acao]()


if __name__ == '__main__':
    main()
