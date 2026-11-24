"""Leitura independente de previsões e ledgers publicados; nenhum treino/backtest novo."""
import csv
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256, conferir_arquivos

SEEDS = (42, 17, 2026)


def incerteza(erros, logs):
    n = erros.shape[1]; saida = {}
    for bloco in (7, 14, 28):
        rng = np.random.default_rng(3105); amostras = []
        for _ in range(2000):
            si = rng.integers(0, 3, 3)
            ix = (rng.integers(0, n-bloco+1, int(np.ceil(n/bloco)))[:, None]+np.arange(bloco)).ravel()[:n]
            amostras.append([erros[si][:, ix].mean(), logs[si][:, ix].mean()])
        ic = np.quantile(amostras, [.025, .975], axis=0)
        saida[str(bloco)] = {'delta_mse_retorno_vs_naive_ic95': ic[:, 0].tolist(), 'crescimento_log_diario_ic95': ic[:, 1].tolist()}
    return saida


def executar():
    reg = RAIZ/'registros/generalizacao_moedas'
    assert ler_json(reg/'estado.json')['situacao'] == 'concluido_conferido_continuacao'
    ret = reg/'retomadas/20261110'
    assert not ler_json(ret/'processo.json')['ativo']
    assert ler_json(ret/'reproducao_parcial.json')['aprovado']
    ptr = ler_json(reg/'execucao.json'); p = RAIZ/ptr['pasta']
    assert sha256(p/'congelamento.json') == ptr['congelamento_sha256']
    f = ler_json(p/'congelamento.json')
    anterior = [json.loads(x) for x in (p/'XRPUSDT/ajustes/seed_42/epocas.jsonl').read_text().splitlines()]
    continuado = [json.loads(x) for x in (p/'XRPUSDT/continuacao_001/ajustes/seed_42/epocas.jsonl').read_text().splitlines()]
    assert len(anterior) == 390 and len(continuado) == 1000
    assert all(all(x[k] == y[k] for k in ('epoca', 'perda_treino_rmse_lotes', 'rmse_global_validacao_retorno', 'taxa')) for x, y in zip(anterior, continuado))
    conferir_arquivos(RAIZ, ler_json(ret/'preparo.json')['artefatos_preservados'])
    btc = RAIZ/f['referencia']['pasta']; fb = ler_json(btc/'congelamento.json')
    assert sha256(btc/'congelamento.json') == f['referencia']['congelamento_sha256']
    receitas = {'BTC': (btc, fb['configuracao'], fb['mercado_minuto'])}
    for moeda in ('ETH', 'BNB', 'XRP'):
        simbolo = moeda+'USDT'; m = f['moedas'][simbolo]
        receitas[moeda] = (p/simbolo/('continuacao_001' if moeda == 'XRP' else ''), m['configuracao'], m['mercado'])
    dest = reg/'conferencias'/agora().replace(':', '').replace('+', '_'); dest.mkdir(parents=True, exist_ok=False)
    resultados = {}; linhas_csv = []; curvas_fig = {}; referencias = {}; n_arquivos = 0; n_operacoes = 0; residuo = 0.
    for moeda, (base, c, mercado) in receitas.items():
        fechamento = ler_json(base/'fechamento.json'); conferir_arquivos(base, fechamento['arquivos']); n_arquivos += len(fechamento['arquivos'])
        assert ler_json(base/'controle.json')['aprovado']
        a = np.load(base/'ajustes/seed_42/validacao.npz')['previsoes']
        b = np.load(base/'ajustes/controle_42/validacao.npz')['previsoes']; np.testing.assert_array_equal(a, b)
        assert ler_json(base/'ajustes/seed_42/selecao.json')['epoca'] == ler_json(base/'ajustes/controle_42/selecao.json')['epoca']
        for nome in ('seed_42', 'controle_42', 'seed_17', 'seed_2026'):
            ajuste = base/'ajustes'/nome
            hist = [json.loads(x) for x in (ajuste/'epocas.jsonl').read_text().splitlines()]
            assert [h['epoca'] for h in hist] == list(range(1, 1001))
            escolhida = min(hist, key=lambda h: h['rmse_global_validacao_retorno'])
            sel = ler_json(ajuste/'selecao.json')
            assert sel['epoca'] == escolhida['epoca'] and sel['sha256'] == sha256(ajuste/sel['checkpoint'])
            assert ler_json(ajuste/'conclusao.json')['recarga_exata']
        pub = base/'publicacao'; resumo = ler_json(pub/'resumo.json')['resumos']; pm = ler_json(pub/'previsao.json')
        cartas = ler_json(pub/'carteiras.json'); assert len(cartas) == 70
        referencias[moeda] = {'pasta': base.relative_to(RAIZ).as_posix(), 'fechamento_sha256': sha256(base/'fechamento.json')}
        dados = {}; resultados[moeda] = {}; origens_comuns = {}
        for fase in ('validacao', 'teste'):
            erros = []; diagnosticos = []; precos = []; maes = []; sinais = []; sinais_ultima = None
            for seed in SEEDS:
                z = np.load(pub/'previsoes'/f'{fase}_{seed}.npz'); u = z['ultimo_close']; y = z['y']; prev = z['previsoes']
                real = y/u-1; pred = prev/u-1; err = pred-real
                np.testing.assert_allclose(pred, z['previsoes_retorno'], atol=1e-14, rtol=1e-12)
                np.testing.assert_allclose(real, z['alvo_retorno'], atol=1e-14, rtol=1e-12)
                m = next(v['metricas'] for v in pm if v['fase'] == fase and v['seed'] == seed)
                rec = {'mse_retorno': float(np.mean(err**2)), 'rmse_retorno': float(np.sqrt(np.mean(err**2))),
                       'mae_retorno': float(np.mean(abs(err))), 'acerto_sinal': float(np.mean(np.sign(pred) == np.sign(real))),
                       'vies_retorno': float(np.mean(err)), 'mse_usdt2': float(np.mean((prev-y)**2)),
                       'rmse_usdt': float(np.sqrt(np.mean((prev-y)**2))), 'mae_usdt': float(np.mean(abs(prev-y)))}
                for k, v in rec.items(): np.testing.assert_allclose(m[k], v, rtol=1e-11, atol=1e-16)
                erros.append(err**2-real**2); precos.append(prev); maes.append(rec)
                diagnosticos.append({'seed': seed, 'previsao_media_pct': float(pred.mean()*100), 'desvio_previsao_pct': float(pred.std()*100),
                    'correlacao': float(np.corrcoef(pred, real)[0, 1]) if pred.std()>0 and real.std()>0 else None, 'fracao_preve_alta': float(np.mean(pred>0)),
                    'min_pct': float(pred.min()*100), 'max_pct': float(pred.max()*100), 'real_desvio_pct': float(real.std()*100)})
                if sinais_ultima is not None: np.testing.assert_array_equal(z['origens_ms'], sinais_ultima)
                sinais_ultima = z['origens_ms'].copy(); dados[(fase, str(seed))] = (z['origens_ms'], u, prev)
            for nome, pred in [('ensemble', np.mean(precos, axis=0)), ('naive', u), ('sempre_comprado', u), ('sempre_vendido', u)]: dados[(fase, nome)] = (sinais_ultima, u, pred)
            medias = {k: float(np.mean([m[k] for m in maes])) for k in maes[0]}
            for k, v in medias.items(): np.testing.assert_allclose(resumo[fase]['previsao_media_seeds'][k], v, rtol=1e-11, atol=1e-16)
            medias.update(mse_naive_retorno=float(np.mean(real**2)), habilidade_mse_retorno_naive=1-medias['mse_retorno']/float(np.mean(real**2)))
            origens_comuns[fase] = sinais_ultima
            resultados[moeda][fase] = {'previsao_media_seeds': medias, 'diagnosticos': diagnosticos, 'operacoes_por_seed': [], 'cenarios': {}}
            dados[(fase, 'erros')] = np.array(erros)
        k = pd.read_parquet(RAIZ/mercado['pasta']/'klines.parquet', columns=['open_time', 'open']).set_index('open_time')['open']
        fnd = pd.read_parquet(RAIZ/mercado['pasta']/'funding.parquet'); ft = fnd.fundingTime.to_numpy(); fr = fnd.fundingRate.to_numpy(); fp = fnd.markPrice.to_numpy()
        curvas = {}; cfg = c['operacoes']
        for carta in cartas:
            fase, nome, cen = carta['fase'], carta['unidade'], carta['cenario']; pasta = RAIZ/carta['pasta']
            r = ler_json(pasta/'resultado.json'); z = np.load(pasta/'curva.npz'); saldo = cfg['capital_inicial']
            ts, u, pred = dados[(fase, nome)]; s = np.where(abs(pred/u-1)>cfg['filtro_retorno_absoluto'], np.sign(pred/u-1), 0)
            if nome.startswith('sempre_'): s = np.full(len(ts), 1 if nome == 'sempre_comprado' else -1)
            cc = c['cenarios'][cen]
            if cc['lado']: s = np.where(s == cc['lado'], s, 0)
            por_dia = {o['origem_ms']: o for o in r['operacoes']}; assert len(por_dia) == len(r['operacoes'])
            for i, t in enumerate(ts):
                if int(t) not in por_dia:
                    assert s[i] == 0; np.testing.assert_allclose(z['saldos_diarios'][i+1], saldo, atol=1e-7, rtol=0); continue
                o = por_dia[int(t)]; lado = int(s[i]); q = o['quantidade']; n_operacoes += 1
                assert lado == o['lado'] and o['entrada_ms'] == int(t)+60000 and o['saida_ms'] == o['entrada_ms']+86400000
                slip = cfg['slippage_por_lado']*cc['slippage_multiplicador']; tick = cfg['tick_preco']; passo = cfg['passo_quantidade']
                pe = float(k.loc[o['entrada_ms']])*(1+lado*slip); ps = float(k.loc[o['saida_ms']])*(1-lado*slip)
                pe = (math.ceil(pe/tick) if lado>0 else math.floor(pe/tick))*tick
                ps = (math.floor(ps/tick) if lado>0 else math.ceil(ps/tick))*tick
                np.testing.assert_allclose([pe, ps], [o['preco_entrada'], o['preco_saida']], atol=1e-8, rtol=0)
                assert q == math.floor(saldo*cfg['fracao_nocional']/pe/passo)*passo
                ix = (ft>=o['entrada_ms']) & (ft<o['saida_ms']); fin = -lado*q*math.fsum(fr[ix]*fp[ix]); com = q*(pe+ps)*cfg['comissao_por_lado']
                liq = lado*q*(ps-pe)-com+fin; residuo = max(residuo, abs(liq-o['pnl_liquido']))
                np.testing.assert_allclose([saldo, liq, fin, com], [o['caixa_antes'], o['pnl_liquido'], o['funding'], o['comissao']], atol=1e-7, rtol=0)
                saldo += liq; np.testing.assert_allclose(saldo, z['saldos_diarios'][i+1], atol=1e-7, rtol=0)
            env = z['patrimonio_envelope']; dd = float(np.max(1-env/np.maximum.accumulate(env)))
            np.testing.assert_allclose([saldo, dd], [r['metricas']['capital_final'], r['metricas']['drawdown_maximo']], atol=1e-7, rtol=0)
            np.testing.assert_allclose(r['metricas']['retorno_liquido'], saldo/cfg['capital_inicial']-1, atol=1e-12)
            ops = r['operacoes']; pnl = np.array([o['pnl_liquido'] for o in ops]); logs_carteira = np.diff(np.log(z['saldos_diarios']))
            conferir_metricas = {'operacoes': len(ops), 'compras': sum(o['lado'] == 1 for o in ops), 'vendas': sum(o['lado'] == -1 for o in ops),
                'comissoes': sum(o['comissao'] for o in ops), 'funding': sum(o['funding'] for o in ops),
                'pnl_compras': sum(o['pnl_liquido'] for o in ops if o['lado'] == 1), 'pnl_vendas': sum(o['pnl_liquido'] for o in ops if o['lado'] == -1),
                'fracao_dias_posicionado': len(ops)/len(ts), 'crescimento_log_diario': float(logs_carteira.mean())}
            if len(pnl): conferir_metricas['taxa_acerto_liquido'] = float((pnl>0).mean())
            if (pnl<0).any(): conferir_metricas['profit_factor'] = float(pnl[pnl>0].sum()/-pnl[pnl<0].sum())
            for chave, valor in conferir_metricas.items(): np.testing.assert_allclose(r['metricas'][chave], valor, rtol=1e-11, atol=1e-9)
            if cen == 'base': curvas[(fase, nome)] = z['saldos_diarios'].copy()
            if nome in ('42', '17', '2026'):
                resultados[moeda][fase]['cenarios'].setdefault(cen, []).append(r['metricas'])
                if cen == 'base': resultados[moeda][fase]['operacoes_por_seed'].append({'seed': int(nome), **r['metricas']})
            elif cen == 'base': resultados[moeda][fase][nome+'_operacoes'] = r['metricas']
        for fase in ('validacao', 'teste'):
            ff = resultados[moeda][fase]
            for cen, vals in ff['cenarios'].items():
                assert len(vals) == 3
                ff['cenarios'][cen] = {key: float(np.mean([v[key] for v in vals])) for key in vals[0] if all(v[key] is not None for v in vals)}
            ff['operacao_media_seeds_base'] = ff['cenarios']['base']
            for key, v in ff['operacao_media_seeds_base'].items(): np.testing.assert_allclose(resumo[fase]['operacao_media_seeds_base'][key], v, rtol=1e-12, atol=1e-10)
            logs = np.array([np.diff(np.log(curvas[(fase, str(seed))])) for seed in SEEDS])
            ff['incerteza'] = incerteza(dados[(fase, 'erros')], logs)
            ff['sondas_ramos'] = {str(seed): ler_json(base/'observacoes'/f'seed_{seed}.json')['contribuicao_ramos'] for seed in SEEDS if (base/'observacoes'/f'seed_{seed}.json').exists()}
            ff['origens_ms'] = [int(origens_comuns[fase][0]), int(origens_comuns[fase][-1])]
            curvas_fig[(moeda, fase)] = np.array([curvas[(fase, str(seed))] for seed in SEEDS])
            linhas_csv.append({'moeda': moeda, 'fase': fase, **ff['previsao_media_seeds'], **{'operacao_'+k: v for k, v in ff['operacao_media_seeds_base'].items()}})
        del k, fnd, curvas
    for fase in ('validacao', 'teste'): assert len({tuple(x[fase]['origens_ms']) for x in resultados.values()}) == 1
    recibo = {'utc': agora(), 'situacao': 'conferido', 'referencias': referencias, 'arquivos_manifestados_conferidos': n_arquivos,
              'carteiras': 280, 'operacoes_conferidas': n_operacoes, 'residuo_maximo_usdt': residuo, 'resultados': resultados,
              'media_tres_seeds_controles_excluidos': True, 'fonte_sha256': sha256(__file__),
              'limites': 'Leitura independente, sem treinos/backtests novos. BTC herdado; quatro moedas distintas e mesmo calendário, não ablação entre moedas. Validação2024 seleciona; teste2025 retrospectivo já consultado. IC exploratório de seeds/blocos7/14/28 não corrige busca prévia. Drawdown confere envelope de risco publicado, não ticks reais nem liquidação certificada. Média de retornos é média de carteiras independentes, não ensemble ou portfólio combinado.'}
    salvar_json(dest/'comparacao.json', recibo)
    with (dest/'medias.csv').open('w', newline='', encoding='utf-8-sig') as arq:
        w = csv.DictWriter(arq, fieldnames=list(linhas_csv[0])); w.writeheader(); w.writerows(linhas_csv)
    (dest/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(2, 2, figsize=(12, 7), sharex=True)
    for ax, moeda in zip(axs.ravel(), receitas):
        vv = curvas_fig[(moeda, 'teste')]; eixo = np.arange(vv.shape[1]); ax.fill_between(eixo, vv.min(axis=0), vv.max(axis=0), color='#3975c6', alpha=.15, label='Faixa das 3 seeds')
        ax.plot(eixo, vv.mean(axis=0), color='#2563a6', lw=2, label='Média dos saldos (3 seeds)'); ax.axhline(10000, color='#777', ls='--', lw=1, label='Caixa / Naive')
        ax.set_title(moeda+' · teste retrospectivo 2025'); ax.grid(alpha=.2); ax.set_ylabel('Saldo diário (USDT)'); ax.set_xlabel('Previsões diárias avaliadas')
    axs[0, 0].legend(fontsize=8, frameon=False)
    fig.suptitle('Mesma receita diária padronizada · futuros bilateral · custos base\nFaixa entre seeds não é intervalo de confiança. Saldos diários não exibem todo o risco intradiário.', fontsize=11)
    fig.tight_layout(); fig.savefig(dest/'patrimonio_quatro_moedas.png', dpi=160); plt.close(fig)
    salvar_json(reg/'comparacao_quatro_moedas.json', {'arquivo': (dest/'comparacao.json').relative_to(RAIZ).as_posix(), 'sha256': sha256(dest/'comparacao.json')})
    print(dest); print('CONFERIDO', n_arquivos, n_operacoes, residuo)


if __name__ == '__main__': executar()
