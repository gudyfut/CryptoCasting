"""Confere e apresenta a publicação encerrada, sem simular ou treinar novamente.

Uso: python -B -m analises.etapas.continuidade_moedas.publicar
Não altera o manifesto científico. A entrega possui seu próprio recibo.
"""
import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import zipfile

import matplotlib
matplotlib.use('Agg')
import matplotlib.dates as datas
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np

from infraestrutura.caminhos import RAIZ


def ler(caminho):
    return json.loads(Path(caminho).read_text(encoding='utf-8-sig'))


def sha(caminho):
    with Path(caminho).open('rb') as arquivo:
        return hashlib.file_digest(arquivo, 'sha256').hexdigest()


def salvar(caminho, valor):
    Path(caminho).write_text(json.dumps(valor, ensure_ascii=False, indent=2,
                                     allow_nan=False) + '\n', encoding='utf-8')


def csv_escrever(caminho, linhas):
    with Path(caminho).open('w', newline='', encoding='utf-8-sig') as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(linhas[0]))
        escritor.writeheader()
        escritor.writerows(linhas)


def conferir_intervalo(diferencas, bloco):
    """Reamostra seeds e os mesmos blocos de datas para as duas políticas."""
    gerador = np.random.default_rng(11112026)
    numero_seeds, numero_dias = diferencas.shape
    replicas = np.empty(2000)
    for repeticao in range(len(replicas)):
        sementes = gerador.integers(0, numero_seeds, numero_seeds)
        inicios = gerador.integers(0, numero_dias - bloco + 1,
                                   int(np.ceil(numero_dias / bloco)))
        indices = np.concatenate([np.arange(inicio, inicio + bloco)
                                  for inicio in inicios])[:numero_dias]
        replicas[repeticao] = diferencas[sementes][:, indices].mean()
    return np.quantile(replicas, [.025, .975])


def main():
    registro = RAIZ / 'registros/continuidade_moedas'
    ponteiro = ler(registro / 'execucao.json')
    pasta = RAIZ / ponteiro['pasta']
    manifesto = ler(pasta / 'manifesto.json')
    for nome, resumo in manifesto['arquivos'].items():
        assert sha(pasta / nome) == resumo, nome
    congelamento = ler(pasta / 'congelamento.json')
    assert sha(pasta / 'congelamento.json') == ponteiro['congelamento_sha256']
    for nome, resumo in congelamento['fontes_entradas'].items():
        assert sha(RAIZ / nome) == resumo, nome
    for nome, resumo in congelamento['pais_artefatos'].items():
        assert sha(RAIZ / nome) == resumo, nome
    resultado = ler(pasta / 'resultados.json')
    conferencia = ler(pasta / 'conferencia.json')
    assert resultado['situacao'] == 'concluido_conferido'
    assert conferencia['heranca_307_carteiras_bytes_exatos']
    moedas = list(congelamento['configuracao']['moedas'])
    fases = ['validacao', 'teste']
    seeds = ['42', '17', '2026']
    unidades = seeds + ['ensemble', 'naive', 'arima', 'sempre_comprado', 'sempre_vendido']
    esperados = {f'{moeda}/{fase}/{unidade}/custo_{custo}/{modo}'
                 for moeda in moedas for fase in fases for custo in [1, 2, 3]
                 for unidade in unidades for modo in ['diaria', 'liquida']}
    esperados |= {f'{moeda}/{fase}/comprar_manter/custo_{custo}/passivo'
                  for moeda in moedas for fase in fases for custo in [1, 2, 3]}
    assert len(esperados) == 408
    assert len(resultado['resultados']) == len(esperados)
    indice = {linha['membro']: linha for linha in resultado['resultados']}
    assert set(indice) == esperados
    curvas, origens, linhas = {}, {}, []
    residuo_maximo, ordens, fundings = 0., 0, 0
    with zipfile.ZipFile(pasta / 'carteiras.zip') as pacote:
        assert pacote.testzip() is None
        assert len(pacote.namelist()) == len(set(pacote.namelist())) == 816
        assert set(pacote.namelist()) == {p + s for p in esperados
                                            for s in ['/resultado.json', '/curva.npz']}
        for nome, resumo in ler(pasta / 'heranca_membros.json').items():
            assert hashlib.sha256(pacote.read(nome)).hexdigest() == resumo
        for nome, linha in indice.items():
            carteira = json.loads(pacote.read(nome + '/resultado.json'))
            assert carteira['metricas'] == linha['metricas']
            curva = dict(np.load(io.BytesIO(pacote.read(nome + '/curva.npz')),
                                 allow_pickle=False))
            saldo = curva['saldos_diarios']
            curvas[nome] = saldo
            origens[(linha['moeda'], linha['fase'])] = curva['origens_ms']
            capital = carteira['regras']['capital_inicial']
            debitos = sum((Decimal(str(o['delta'])) * Decimal(str(o['preenchimento']))
                          + Decimal(str(o['comissao'])) for o in carteira['ordens']), Decimal(0))
            credito = sum((Decimal(str(e['valor'])) for e in carteira['funding']), Decimal(0))
            final = float(Decimal(str(capital)) - debitos + credito)
            residuo_maximo = max(residuo_maximo, abs(final - saldo[-1]))
            np.testing.assert_allclose(final, saldo[-1], atol=1e-7, rtol=0)
            met = linha['metricas']
            np.testing.assert_allclose(saldo[-1] / capital - 1, met['retorno_liquido'], atol=1e-12)
            np.testing.assert_allclose(np.diff(np.log(saldo)).mean(), met['crescimento_log_diario'], atol=1e-12)
            np.testing.assert_allclose(curva['drawdown_acumulado'][-1], met['drawdown_maximo'], atol=1e-12)
            for chave, eventos, valor in [('comissoes', carteira['ordens'], 'comissao'),
                                          ('custo_slippage_ticks', carteira['ordens'], 'custo_slippage_ticks'),
                                          ('funding', carteira['funding'], 'valor')]:
                np.testing.assert_allclose(sum(e[valor] for e in eventos), met[chave], atol=1e-7)
            ordens += len(carteira['ordens'])
            fundings += len(carteira['funding'])
            linhas.append({k: linha[k] for k in ['moeda', 'fase', 'unidade', 'custo', 'modo']} | met)
    medias, comparacao, intervalos = [], [], []
    for moeda in moedas:
        for fase in fases:
            for custo in [1, 2, 3]:
                chave = f'{moeda}/{fase}/{{}}/custo_{custo}/{{}}'
                for modo in ['diaria', 'liquida']:
                    amostras = [indice[chave.format(s, modo)]['metricas'] for s in seeds]
                    media = {k: float(np.mean([a[k] for a in amostras])) for k in amostras[0]
                             if all(isinstance(a[k], (int, float)) for a in amostras)}
                    for k, valor in media.items():
                        np.testing.assert_allclose(valor, resultado['medias_tres_seeds'][moeda][fase][str(custo)][modo][k], atol=1e-12)
                    medias.append(dict(moeda=moeda, fase=fase, custo=custo, modo=modo, seeds=3) | media)
                atual = np.array([np.diff(np.log(curvas[chave.format(s, 'liquida')])) for s in seeds])
                bases = {'liquida_menos_diaria': np.array([np.diff(np.log(curvas[chave.format(s, 'diaria')])) for s in seeds])}
                for un in ['naive', 'arima', 'comprar_manter']:
                    modo = 'passivo' if un == 'comprar_manter' else 'liquida'
                    bases[f'mamba_menos_{un}'] = np.tile(np.diff(np.log(curvas[chave.format(un, modo)])), (3, 1))
                for contraste, base in bases.items():
                    for bloco in [7, 14, 28]:
                        diferencas = atual - base
                        ic = conferir_intervalo(diferencas, bloco)
                        oficial = resultado['contrastes_pareados'][moeda][fase][str(custo)][contraste][str(bloco)]
                        np.testing.assert_allclose(ic, oficial['ic95'], atol=1e-15, rtol=0)
                        np.testing.assert_allclose(diferencas.mean(), oficial['media_delta_log_diario'], atol=1e-15)
                        intervalos.append(dict(moeda=moeda, fase=fase, custo=custo, contraste=contraste,
                                               bloco=bloco, media_log_diaria=float(diferencas.mean()),
                                               ic95_inferior=ic[0], ic95_superior=ic[1]))
            for unidade in ['mamba_media', 'ensemble', 'naive', 'arima', 'comprar_manter']:
                modo = 'passivo' if unidade == 'comprar_manter' else 'liquida'
                met = resultado['medias_tres_seeds'][moeda][fase]['1'][modo] if unidade == 'mamba_media' else indice[f'{moeda}/{fase}/{unidade}/custo_1/{modo}']['metricas']
                comparacao.append(dict(moeda=moeda, fase=fase, unidade=unidade,
                                       **{k: met[k] for k in ['retorno_liquido', 'drawdown_maximo', 'capital_final', 'ordens', 'dias_comprado', 'dias_vendido']}))
            candidatos = ler(pasta / f'arima_{moeda}/candidatos.json')
            melhor = min((c for c in candidatos if c['status'] == 'valido'),
                         key=lambda c: (c['mse_validacao'], c['ordem'][0] + c['ordem'][2], c['ordem'][0], c['ordem'][2]))
            assert melhor == ler(pasta / f'arima_{moeda}/selecao.json')
            controle = ler(pasta / f'arima_{moeda}/controle.json')
            assert all(controle[k] for k in ['parametros_repetidos_exatos', 'previsoes_repetidas_exatas',
                                           'api_previsao_independente_conferida', 'causalidade_por_perturbacao_futura'])
    entrega = pasta / 'publicacao'
    entrega.mkdir(exist_ok=False)
    csv_escrever(entrega / 'carteiras.csv', linhas)
    csv_escrever(entrega / 'medias_tres_seeds.csv', medias)
    csv_escrever(entrega / 'comparacao_referencias.csv', comparacao)
    csv_escrever(entrega / 'contrastes_intervalos.csv', intervalos)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False,
                         'axes.spines.right': False, 'figure.facecolor': 'white'})
    figura, eixos = plt.subplots(2, 2, figsize=(13.5, 8.4), sharex=True)
    for moeda, eixo in zip(moedas, eixos.flat):
        t = origens[(moeda, 'teste')]
        tempo = np.r_[t[0] + 60000, t + 86460000].astype('datetime64[ms]')
        matriz = np.array([curvas[f'{moeda}/teste/{s}/custo_1/liquida'] for s in seeds]) / 10000 - 1
        eixo.fill_between(tempo, matriz.min(axis=0), matriz.max(axis=0), color='#1268a8', alpha=.10,
                          label='Faixa das três seeds (não é IC)')
        for modo, cor, rotulo in [('diaria', '#8c95a2', 'Mamba: zerar/reabrir'), ('liquida', '#1268a8', 'Mamba: continuidade')]:
            media = np.mean([curvas[f'{moeda}/teste/{s}/custo_1/{modo}'] for s in seeds], axis=0) / 10000 - 1
            eixo.plot(tempo, media, color=cor, linewidth=2, label=rotulo)
        for unidade, cor, rotulo, modo in [('arima', '#168271', 'ARIMA: continuidade', 'liquida'),
                                          ('comprar_manter', '#bc6b17', 'Comprar/manter no futuro', 'passivo')]:
            eixo.plot(tempo, curvas[f'{moeda}/teste/{unidade}/custo_1/{modo}'] / 10000 - 1,
                      color=cor, linewidth=1.35, label=rotulo)
        eixo.axhline(0, color='#303b47', linestyle=':', linewidth=1, label='Naive: caixa')
        eixo.set_title(moeda.replace('USDT', ''), loc='left', fontweight='bold')
        eixo.yaxis.set_major_formatter(PercentFormatter(1))
        eixo.xaxis.set_major_locator(datas.MonthLocator(interval=2))
        eixo.xaxis.set_major_formatter(datas.DateFormatter('%b'))
        eixo.grid(axis='y', color='#d9dfe5', alpha=.7)
        eixo.set_ylabel('Retorno acumulado líquido')
    handles, labels = eixos.flat[0].get_legend_handles_labels()
    figura.legend(handles, labels, loc='lower center', bbox_to_anchor=(.5, .045), ncol=3, frameon=False)
    figura.suptitle('Continuidade reduz giro; lucro e estabilidade dependem da moeda', x=.07, y=.98,
                    ha='left', fontsize=16, fontweight='bold')
    figura.text(.07, .935, '2025 retrospectivo • Receita diária padronizada • Média de três carteiras Mamba, sem escolher seeds', color='#4b5865')
    figura.text(.07, .015, 'Capital inicial: 10.000 USDT por carteira. Comissão: 0,05%/lado; slippage provisório: 0,01%/lado; funding incluído.\n'
                          'Comprar/manter: quantidade fixa no mesmo perpétuo. Curva média não é ensemble nem carteira executável.', fontsize=9, color='#4b5865')
    figura.subplots_adjust(top=.88, bottom=.19, left=.07, right=.98, hspace=.25, wspace=.22)
    figura.savefig(entrega / 'comparacao_2025.png', dpi=160)
    figura.savefig(entrega / 'comparacao_2025.pdf')
    plt.close(figura)
    salvar(entrega / 'conferencia_posterior.json', dict(
        utc=datetime.now(timezone.utc).isoformat(), execucao=ponteiro['id'],
        manifesto_cientifico_sha256=sha(pasta / 'manifesto.json'),
        cobertura_exata=408, membros_zip=816, heranca_307_bytes_exatos=True,
        manifesto_fontes_pais_integros=True, ordens_reconciliadas=ordens,
        fundings_reconciliados=fundings, residuo_decimal_maximo_usdt=residuo_maximo,
        medias_recalculadas=48, intervalos_recalculados=len(intervalos),
        selecoes_arima_conferidas=4, novos_backtests=0, novos_treinamentos=0,
        limite='Conferência posterior dos ledgers; não repete a auditoria integral de eventos/preços/risco já publicada.'))
    salvar(pasta / 'entrega_manifesto.json', dict(
        utc=datetime.now(timezone.utc).isoformat(), execucao=ponteiro['id'],
        manifesto_cientifico_sha256=sha(pasta / 'manifesto.json'),
        leitor='codigo/analises/etapas/continuidade_moedas/publicar.py', leitor_sha256=sha(Path(__file__)),
        arquivos={q.relative_to(pasta).as_posix(): sha(q) for q in entrega.iterdir()}))
    print(json.dumps(dict(execucao=ponteiro['id'], carteiras=408, intervalos=len(intervalos),
                          residuo_usdt=residuo_maximo, publicacao=str(entrega)), ensure_ascii=False))


if __name__ == '__main__':
    main()
