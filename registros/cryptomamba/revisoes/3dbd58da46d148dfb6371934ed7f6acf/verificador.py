"""Conferência posterior, médias3/6 e figura científica; nunca treina ou seleciona."""
import math
import shutil
from uuid import uuid4
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256, conferir_arquivos
from treinamento.preservacao import conferir


SEEDS = [17, 42, 2026, 7, 123, 31415]


def resumir(chaves, resultados):
    linhas = [resultados[k] for k in chaves]
    n = len(linhas)
    predicao = {}
    for parte in ('validacao', 'teste'):
        metricas = [r['metricas'][parte] for r in linhas]
        m = {nome: float(np.mean([r[nome] for r in metricas])) for nome in
             ('mse', 'rmse', 'mae', 'habilidade_mse', 'acuracia_direcional', 'acerto_balanceado_direcional')}
        m['mse_desvio_seeds'] = float(np.std([r['mse'] for r in metricas], ddof=1)) if n > 1 else None
        m['seeds_melhores_naive'] = sum(r['habilidade_mse'] > 0 for r in metricas)
        m['preco'] = {nome: float(np.mean([r['metricas_preco'][parte][nome] for r in linhas]))
                      for nome in ('rmse_usdt', 'mae_usdt', 'mape_percentual')}
        predicao[parte] = m
    spot = {}
    for perfil in ('base', 'agravado', 'bruto_mesmos_sinais'):
        valores = [r['spot'][perfil] for r in linhas]
        if not all(v['retorno_auditavel'] and v['risco_auditavel'] for v in valores):
            raise ValueError('Spot incompleto: não usar retorno parcial.')
        s = {nome: float(np.mean([v[nome] for v in valores])) for nome in
             ('retorno_liquido', 'drawdown', 'entradas_planejadas', 'custos_observados', 'minutos_expostos_planejados')}
        s['retorno_desvio_seeds'] = float(np.std([v['retorno_liquido'] for v in valores], ddof=1)) if n > 1 else None
        s['seeds_lucrativas'] = sum(v['retorno_liquido'] > 0 for v in valores)
        spot[perfil] = s
    return {'n_seeds': n, 'chaves': chaves, 'predicao': predicao, 'spot': spot}


def figura(grupos, efeitos, pasta, benchmarks):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    pasta.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.spines.top': False, 'axes.spines.right': False})
    nomes = [f'estado{n}_taxa{t}' for t in ('0002', '0001') for n in (8, 16, 32, 64)] + ['cryptomamba']
    rotulos = [f'S{n}\n{t}' for t in ('0,0002', '0,0001') for n in (8, 16, 32, 64)] + ['CryptoMamba\nadaptado']
    cores = ['#3C6F91'] * 4 + ['#BE8737'] * 4 + ['#178275']
    fig, axs = plt.subplots(2, 2, figsize=(14, 9))
    for ax, parte, titulo in [(axs[0, 0], 'validacao', 'Validação 2024: habilidade contra Naive (%)'),
                             (axs[0, 1], 'teste', 'Teste 2025: habilidade contra Naive (%)')]:
        vals = [100 * grupos[n]['predicao'][parte]['habilidade_mse'] for n in nomes]
        ax.bar(np.arange(9), vals, color=cores, width=.7)
        ax.set_xticks(np.arange(9), rotulos, fontsize=8)
        ax.set_title(titulo, loc='left', pad=12)
        ax.axhline(0, color='#222', linewidth=.8)
        ax.set_ylabel('Acima de zero favorece o modelo')
    ax = axs[1, 0]
    vals = [100 * grupos[n]['spot']['base']['retorno_liquido'] for n in nomes]
    desvios = [100 * grupos[n]['spot']['base']['retorno_desvio_seeds'] for n in nomes]
    ax.bar(np.arange(9), vals, color=cores, width=.7, yerr=desvios, capsize=3)
    ax.set_xticks(np.arange(9), rotulos, fontsize=8)
    ax.set_title('Spot: retorno líquido médio e desvio entre seeds', loc='left', pad=12)
    ax.axhline(0, color='#222', linewidth=.8, label='Caixa: 0%')
    bh = benchmarks.get('comprar_manter_base', {}).get('retorno_liquido')
    if bh is not None:
        ax.axhline(100 * bh, color='#666', linestyle='--', label='Comprar e manter')
    ax.set_ylabel('Retorno (%) · barras: desvio, não IC')
    ax.legend(frameon=False, fontsize=8)
    ax = axs[1, 1]
    x = np.arange(6)
    for j, (parte, cor) in enumerate([('validacao', '#3C6F91'), ('teste', '#BE8737')]):
        vals = [efeitos[parte][str(s)]['mudanca_relativa_percentual'] for s in SEEDS]
        ax.bar(x + (j - .5) * .36, vals, .34, color=cor, label=parte)
    ax.axhline(0, color='#222', linewidth=.8)
    ax.set_xticks(x, [str(s) for s in SEEDS])
    ax.set_title('CryptoMamba vs S16/0,0002: efeito por seed', loc='left', pad=12)
    ax.set_ylabel('Mudança no MSE (%) · negativo é melhor')
    ax.legend(frameon=False)
    for ax in axs.flat:
        ax.set_axisbelow(True)
        ax.grid(axis='y', color='#E0E5E9')
    fig.suptitle('Uma arquitetura adaptada supera a referência local?', x=.07, y=.98,
                 ha='left', fontsize=17, fontweight='bold')
    fig.text(.07, .025, 'Seis seeds iguais · médias individuais, sem ensemble · 2024/2025 retrospectivos · receita Spot fixa',
             fontsize=10, color='#555')
    fig.subplots_adjust(left=.08, right=.98, top=.89, bottom=.12, hspace=.40, wspace=.25)
    saidas = {}
    for ext in ('png', 'pdf'):
        dest = pasta / f'comparacao_abordagens.{ext}'
        if dest.exists():
            raise FileExistsError('Figura existente: preservar.')
        fig.savefig(dest, dpi=170, bbox_inches='tight', facecolor='white')
        saidas[dest.relative_to(RAIZ).as_posix()] = sha256(dest)
    plt.close(fig)
    return saidas


def analisar():
    reg = RAIZ / 'registros/cryptomamba'
    if (reg / 'analise_interpretativa_atual.json').exists():
        raise FileExistsError('Análise existente: consultar recibo, não repetir.')
    ptr = ler_json(reg / 'execucao.json')
    base = RAIZ / ptr['pasta']
    fim = ler_json(reg / 'fechamento.json')
    if fim['situacao'] != 'concluido_conferido' or ler_json(base / 'processo.json')['ativo']:
        raise ValueError('Aguardar conclusão e pós-conferência sem processo ativo.')
    conferir_arquivos(base, {'congelamento.json': ptr['congelamento_sha256']})
    f = ler_json(base / 'congelamento.json')
    conferir_arquivos(RAIZ, f['contrato']['fontes'])
    conferir_arquivos(base / 'fontes', f['contrato']['fontes'])
    for recibo in (fim['auditoria'], fim['comparacao']):
        conferir_arquivos(RAIZ, {recibo['arquivo']: recibo['sha256']})
    pp = ler_json(base / 'publicacao.json')
    pub = base / pp['pasta']
    conferir_arquivos(pub, {'manifesto.json': pp['manifesto_sha256']})
    conferir_arquivos(pub, ler_json(pub / 'manifesto.json')['arquivos'])
    r = ler_json(pub / 'resultados.json')
    assert r['novos'] == 6 and r['herdados'] == 53 and len(r['por_ajuste']) == 59
    verificacoes, diagnosticos, ajustes = {}, {}, {}
    for chave, item in r['por_ajuste'].items():
        t = RAIZ / item['tentativa_origem']
        conferir(t)
        verificacoes[chave] = {}
        for parte in ('validacao', 'teste'):
            q = pd.read_parquet(t / f'previsoes_{parte}.parquet')
            p, y = q.previsao.to_numpy(float), q.alvo.to_numpy(float)
            n = len(q)
            mse = math.fsum(float(v) ** 2 for v in p - y) / n
            mae = math.fsum(abs(float(v)) for v in p - y) / n
            for nome, calculado in [('mse', mse), ('mae', mae), ('rmse', math.sqrt(mse))]:
                assert math.isclose(calculado, item['metricas'][parte][nome], rel_tol=1e-12, abs_tol=1e-17)
            precos = q.close.to_numpy(float) * np.exp(p)
            erros = precos - q.preco_destino.to_numpy(float)
            pm = {'rmse_usdt': float(np.sqrt(np.mean(erros ** 2))), 'mae_usdt': float(np.mean(abs(erros))),
                  'mape_percentual': float(100 * np.mean(abs(erros / q.preco_destino.to_numpy(float))))}
            for nome, valor in pm.items():
                assert math.isclose(valor, item['metricas_preco'][parte][nome], rel_tol=1e-12, abs_tol=1e-12)
            verificacoes[chave][parte] = {'n': n, 'mse_recalculado': mse, 'mae_recalculado': mae, 'preco': pm}
            if chave.startswith('cryptomamba_'):
                distintos = len(np.unique(p))
                dp, dy = (float(np.std(p)) if distintos > 1 else 0.), float(np.std(y))
                diagnosticos.setdefault(chave, {})[parte] = {'desvio_previsoes': dp, 'desvio_alvo': dy,
                    'razao_desvios': dp / dy, 'media_previsao': float(p.mean()),
                    'valores_distintos': distintos,
                    'previsoes_positivas_fracao': float(np.mean(p > 0)),
                    'correlacao': float(np.corrcoef(p, y)[0, 1]) if dp > 0 else None}
        if chave.startswith('cryptomamba_'):
            ajustes[chave] = ler_json(t / 'ajuste.json')
    grupos = {}
    for nome, seeds in [('tres', SEEDS[:3]), ('seis', SEEDS)]:
        g = {'cryptomamba': resumir([f'cryptomamba_{s}' for s in seeds], r['por_ajuste'])}
        for estado in (8, 16, 32, 64):
            for taxa, prefixo in [('0002', ''), ('0001', 'taxa0001_')]:
                g[f'estado{estado}_taxa{taxa}'] = resumir([f'{prefixo}estado{estado}_{s}' for s in seeds], r['por_ajuste'])
        for baseline in ('naive', 'arima'):
            g[baseline] = resumir([baseline], r['por_ajuste'])
        if nome == 'tres':
            g['lstm'] = resumir([f'lstm_{s}' for s in seeds], r['por_ajuste'])
        grupos[nome] = g
    efeitos = {parte: {str(s): {
        'diferenca_mse': r['por_ajuste'][f'cryptomamba_{s}']['metricas'][parte]['mse'] - r['por_ajuste'][f'estado16_{s}']['metricas'][parte]['mse'],
        'mudanca_relativa_percentual': 100 * (r['por_ajuste'][f'cryptomamba_{s}']['metricas'][parte]['mse'] / r['por_ajuste'][f'estado16_{s}']['metricas'][parte]['mse'] - 1)}
        for s in SEEDS} for parte in ('validacao', 'teste')}
    anterior = ler_json(reg / 'preservacao_antes.json')
    conferir_arquivos(RAIZ, anterior['arquivos'])
    br = RAIZ / 'dados/experimentos/ohlcv_modular_ab5baf3eab3a2e66d8b2/publicacoes/tentativa_001'
    conferir_arquivos(br, ler_json(br / 'manifesto.json')['arquivos'])
    benchmarks = ler_json(br / 'resultados.json')['referencias_economicas']
    externo = ler_json(reg / 'diagnostico_naive_publico.json')
    pe = RAIZ / externo['pasta']
    conferir_arquivos(pe, {'manifesto.json': externo['manifesto_sha256']})
    conferir_arquivos(pe, ler_json(pe / 'manifesto.json')['arquivos'])
    diagnostico_externo = ler_json(pe / externo['analise'])
    indice_sensibilidade = ler_json(reg / 'sensibilidade_atual.json')
    if set(indice_sensibilidade) != {str(s) for s in SEEDS}:
        raise ValueError('Concluir diagnósticos de sensibilidade das seis seeds antes da interpretação.')
    sensibilidades = {}
    for s, recibo in indice_sensibilidade.items():
        conferir_arquivos(RAIZ, {recibo['arquivo']: recibo['sha256']})
        sensibilidades[s] = ler_json(RAIZ / recibo['arquivo'])
    dest = reg / 'revisoes' / uuid4().hex
    dest.mkdir(parents=True)
    shutil.copy2(__file__, dest / 'verificador.py')
    doc = RAIZ / 'docs/resultados_cryptomamba_adaptado.md'
    shutil.copy2(doc, dest / 'relatorio_automatico.md')
    a = {'utc': agora(), 'execucao': ptr['id'], 'natureza': 'conferência posterior independente por somas; sem treino ou seleção',
         'grupos': grupos, 'efeitos_por_seed': efeitos, 'diagnosticos': diagnosticos, 'ajustes_novos': ajustes,
         'sensibilidade_inicial_vs_checkpoint': sensibilidades,
         'contrastes': r['contrastes'], 'criterio_primario': r['criterio_primario'], 'conferencias': verificacoes,
         'referencias_economicas': benchmarks, 'diagnostico_externo_naive': diagnostico_externo,
         'fonte': pub.relative_to(RAIZ).as_posix(),
         'preservados': len(anterior['arquivos']), 'limites': ['Desvios entre seeds não são IC temporais.',
         'Recorte3 e diagnóstico de concentração são posteriores/exploratórios.',
         'Núcleo equivalente não implica reprodução de treino/artigo; comparação é de abordagem composta.',
         'Métricas de preço são derivadas do retorno; não treinamento direto em dólares.']}
    salvar_json(dest / 'analise.json', a)
    figuras = figura(grupos['seis'], efeitos, RAIZ / f'docs/figuras/cryptomamba_{ptr["id"]}', benchmarks)
    salvar_json(dest / 'figuras.json', {'fonte_sha256': sha256(dest / 'analise.json'), 'arquivos': figuras})
    salvar_json(dest / 'manifesto.json', {'arquivos': {p.name: sha256(p) for p in dest.iterdir() if p.is_file()}})
    ponteiro = {'arquivo': (dest / 'analise.json').relative_to(RAIZ).as_posix(), 'sha256': sha256(dest / 'analise.json')}
    salvar_json(reg / 'analise_interpretativa_atual.json', ponteiro)
    linhas = ['', '## Revisão independente e recorte de três seeds', '',
        'As 59 séries tiveram MSE/MAE/RMSE de retorno e métricas de preço recalculados por outro procedimento. '
        'O relatório automático anterior foi preservado junto ao verificador. O recorte abaixo mantém17/42/2026 '
        'em todas as redes para comparação com LSTM; é posterior e não substitui o critério principal de seis seeds.', '',
        '| Modelo (3 seeds nas redes) | MSE validação | MSE teste | RMSE preço teste (USDT) | MAPE preço teste (%) | Spot líquido |',
        '|---|---:|---:|---:|---:|---:|']
    for nome, g in grupos['tres'].items():
        v, t = g['predicao']['validacao'], g['predicao']['teste']
        linhas.append(f'| {nome} | {v["mse"]:.9f} | {t["mse"]:.9f} | {t["preco"]["rmse_usdt"]:.2f} | {t["preco"]["mape_percentual"]:.3f} | {100*g["spot"]["base"]["retorno_liquido"]:+.3f}% |')
    linhas += ['', '## A rede usa as entradas ou responde quase sempre igual?', '',
        '| Seed | Valores previstos distintos no teste | Desvio previsão / desvio alvo | Saídas distintas em 8 janelas, antes → depois | Máximo gradiente da saída nas entradas |',
        '|---|---:|---:|---:|---:|']
    for s in SEEDS:
        d = diagnosticos[f'cryptomamba_{s}']['teste']
        sens = sensibilidades[str(s)]
        linhas.append(f'| {s} | {d["valores_distintos"]} | {d["razao_desvios"]:.6g} | '
                      f'{sens["inicial"]["valores_distintos"]} → {sens["treinada"]["valores_distintos"]} | '
                      f'{sens["gradiente_saida_soma_em_relacao_entradas"]["maior_absoluto"]:.6g} |')
    constantes = sum(diagnosticos[f'cryptomamba_{s}']['teste']['valores_distintos'] == 1 for s in SEEDS)
    linhas += ['', f'Em {constantes}/6 checkpoints, o retorno previsto no teste foi exatamente constante. '
        'Uma constante positiva pode reduzir o erro em um ano de alta sem reconhecer movimentos específicos. '
        'Uma constante abaixo dos custos implica permanecer em caixa; retorno Spot zero não demonstra capacidade '
        'de selecionar boas operações. O diagnóstico inicial/checkpoint usa oito janelas reais só de passado, '
        'sem otimizador ou ajuste adicional. Pesos próximos de zero e gradiente zero evidenciam perda de '
        'sensibilidade sob esta receita; isolar a causa entre Adam/L2/taxa/escala/arquitetura exige outro contraste '
        'autorizado. As tentativas degeneradas foram preservadas, não substituídas.', '',
        'RMSE de preço pesa mais erros em dias nos quais BTC é caro; MSE de retorno mede a variação relativa. '
        'MAPE de preço em torno de 2% não equivale a 98% de acerto direcional nem a 2% de lucro.', '',
        f'![Comparação das abordagens](figuras/cryptomamba_{ptr["id"]}/comparacao_abordagens.png)', '',
        'Habilidade acima de zero significa MSE menor que Naive. As barras de dispersão financeira mostram desvio '
        'entre seeds, não confiança estatística ou incerteza do preço. Métricas e retornos são médias dos modelos individuais.', '',
        f'[Análise independente e diagnósticos](../{ponteiro["arquivo"]}). Nenhum dado, checkpoint, receita ou publicação foi sobrescrito.']
    linhas += ['', '## Persistência nos dados públicos do CryptoMamba: diagnóstico separado', '',
        'O Naive também foi calculado nos CSVs públicos fixados no mesmo commit do código. '
        'São 350 alvos de teste conforme CMambaDataset(window_size=14), com a última janela excluída '
        'pelo próprio __len__ público. Uma segunda conferência usou as classes originais e float32. '
        'Nenhuma rede foi treinada neste diagnóstico; ele não integra os 59 resultados Binance.', '',
        '| Origem | RMSE (USD) | MAE (USD) | MAPE (%) |', '|---|---:|---:|---:|']
    for nome, m in [('Naive calculado no split público', diagnostico_externo['metricas_globais']['test']['naive']),
                    ('CryptoMamba-v reportado no artigo', diagnostico_externo['numeros_artigo_cryptomamba_v'])]:
        linhas.append(f'| {nome} | {m["rmse_usd"]:.2f} | {m["mae_usd"]:.2f} | {m["mape_percentual"]:.3f} |')
    linhas += ['', 'Os números publicados são maiores neste confronto numérico, mas não foram recalculados '
        'dos checkpoints/previsões do artigo. A identidade da população exata da tabela não foi certificada; '
        'não há contraste pareado ou conclusão de significância. A tabela principal do artigo não inclui Naive. '
        'Esse diagnóstico sustenta manter persistência como referência; não refuta o trabalho nem prova '
        'vantagem da nossa arquitetura.', '',
        '[Artigo, tabela 3](https://arxiv.org/html/2501.01010v2), '
        f'[fontes e recibos do cálculo independente](../{externo["pasta"]}/analise_naive.json).']
    doc.write_text(doc.read_text(encoding='utf-8-sig') + '\n'.join(linhas) + '\n', encoding='utf-8')
    cat = ler_json(RAIZ / 'registros/catalogo_estudos.json')
    for row in cat['rodadas_ohlcv']:
        if row.get('execucao') == ptr['id']:
            row['analise_interpretativa'] = ponteiro
    salvar_json(RAIZ / 'registros/catalogo_estudos.json', cat)
    print(ponteiro)
    return a


if __name__ == '__main__':
    analisar()
