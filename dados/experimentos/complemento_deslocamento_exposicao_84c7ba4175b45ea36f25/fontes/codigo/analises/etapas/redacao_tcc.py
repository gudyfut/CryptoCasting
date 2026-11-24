"""Materiais editoriais reproduzíveis; lê publicações encerradas, nunca executa modelos.

Executar na raiz: python -B -m analises.etapas.redacao_tcc
"""
import hashlib
import io
import json
import zipfile
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from infraestrutura.caminhos import RAIZ

BASE = RAIZ / 'escrita_tcc'
FONTES = {}


def ler(caminho, csv=False):
    p = RAIZ / caminho
    FONTES[p.relative_to(RAIZ).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return pd.read_csv(p) if csv else json.loads(p.read_text(encoding='utf-8'))


def numero(x, casas=3):
    return f'{float(x):.{casas}f}'.replace('.', ',')


def tabela(nome, cabecalho, linhas, colunas):
    destino = BASE / 'latex/tabelas'
    destino.mkdir(exist_ok=True)
    texto = '\\begin{tabular}{' + colunas + '}\n\\toprule\n'
    texto += cabecalho + ' \\\\\n\\midrule\n'
    texto += '\n'.join(' & '.join(l) + ' \\\\' for l in linhas)
    texto += '\n\\bottomrule\n\\end{tabular}\n'
    (destino / f'{nome}.tex').write_text(texto, encoding='utf-8')


def figura(fig, nome):
    fig.savefig(BASE / f'latex/figs/{nome}.pdf', bbox_inches='tight')
    revisao = BASE / 'build/figuras'
    revisao.mkdir(parents=True, exist_ok=True)
    fig.savefig(revisao / f'{nome}.png', dpi=160, bbox_inches='tight')
    plt.close(fig)


def figura_previsoes_operacoes(ponteiros):
    """Representa séries congeladas, conferindo origens, sinais e saldos publicados."""
    import matplotlib.dates as datas
    from matplotlib.ticker import FuncFormatter
    verificacoes = {}
    from matplotlib.lines import Line2D
    fig, eixos = plt.subplots(3, 2, figsize=(7.1, 5.4), sharex='col',
                             gridspec_kw={'height_ratios': [1.25, .55, 1.4]},
                             layout='constrained')
    cores = {'A': '#126782', 'L': '#b85a19'}
    fig.legend(handles=[Line2D([], [], color=cores['A'], lw=1.5, label='A: Mamba'),
                        Line2D([], [], color=cores['L'], lw=1.5, ls='--', label='L: ablação linear')],
               loc='outside upper center', ncol=2, fontsize=9, frameon=False)
    for coluna, ano in enumerate([2025, 2026]):
        base = Path(ponteiros[ano]['pasta'])
        publicacao = base / 'BTCUSDT/publicacao' if ano == 2025 else base
        operacoes = ler((publicacao / 'operacoes.json').as_posix())
        arquivo_zip = publicacao / 'carteiras.zip'
        FONTES[arquivo_zip.as_posix()] = hashlib.sha256((RAIZ / arquivo_zip).read_bytes()).hexdigest()
        for variante in ['A', 'L']:
            caminho = (publicacao / f'previsoes/teste_{variante}_ensemble.npz' if ano == 2025
                       else base / f'BTCUSDT/{variante}_ensemble.npz')
            conteudo = (RAIZ / caminho).read_bytes()
            FONTES[caminho.as_posix()] = hashlib.sha256(conteudo).hexdigest()
            with np.load(io.BytesIO(conteudo), allow_pickle=False) as pacote:
                previsao = {k: pacote[k].copy() for k in pacote.files}
            linha = [x for x in operacoes['carteiras'] if x['unidade'] == f'{variante}_ensemble'
                     and x['custo'] == 1 and x.get('fase', 'teste') == 'teste'
                     and x.get('moeda', 'BTCUSDT') == 'BTCUSDT']
            assert len(linha) == 1
            membro = linha[0]['membro']
            with zipfile.ZipFile(RAIZ / arquivo_zip) as z:
                resultado = json.loads(z.read(membro + '/resultado.json'))
                with np.load(io.BytesIO(z.read(membro + '/curva.npz')), allow_pickle=False) as pacote:
                    curva = {k: pacote[k].copy() for k in pacote.files}
            origens = previsao['origens_ms']
            np.testing.assert_array_equal(origens, curva['origens_ms'])
            np.testing.assert_array_equal(origens, [x['origem_ms'] for x in resultado['dias']])
            assert len(origens) == (350 if ano == 2025 else 314)
            assert np.all(np.diff(origens) == 86400000)
            sinais = np.where(previsao['previsoes_retorno'] > .002, 1,
                              np.where(previsao['previsoes_retorno'] < -.002, -1, 0))
            np.testing.assert_array_equal(sinais, [x['lado_sinal'] for x in resultado['dias']])
            posicoes = np.sign([x['quantidade'] for x in resultado['dias']])
            assert np.all(posicoes >= 0)  # A legenda descreve especificamente estes ensembles BTC.
            assert np.all((previsao['previsoes_retorno'] * 100 > -.25) &
                          (previsao['previsoes_retorno'] * 100 < .35))
            assert np.all((curva['saldos_diarios'] / 1000 > 9) &
                          (curva['saldos_diarios'] / 1000 < 14))
            metrica = linha[0]['metricas']
            assert np.count_nonzero(posicoes) == metrica['dias_posicionado']
            np.testing.assert_allclose(curva['saldos_diarios'][-1], metrica['capital_final'], rtol=0, atol=1e-8)
            np.testing.assert_allclose(curva['saldos_diarios'][-1] / 10000 - 1, metrica['retorno_liquido'], rtol=0, atol=1e-12)
            t = pd.to_datetime(origens, unit='ms', utc=True)
            limites = pd.to_datetime([resultado['dias'][0]['entrada_ms']] +
                                     [x['fim_ms'] for x in resultado['dias']], unit='ms', utc=True)
            if variante == 'A':
                alvo = previsao['alvo_retorno']
            else:
                np.testing.assert_array_equal(alvo, previsao['alvo_retorno'])
            eixos[0, coluna].plot(t, previsao['previsoes_retorno'] * 100,
                                  color=cores[variante], lw=1.1,
                                  ls='-' if variante == 'A' else '--', label=variante)
            altura = 1 if variante == 'A' else 0
            # Une apenas intervalos adjacentes com a mesma posição registrada.
            # Evita separadores diários que pareciam encerramentos e novas ordens.
            cortes = np.r_[0, np.flatnonzero(np.diff(posicoes)) + 1, len(posicoes)]
            dias_representados = 0
            for inicio, fim in zip(cortes[:-1], cortes[1:]):
                if posicoes[inicio]:
                    eixos[1, coluna].fill_between([limites[inicio], limites[fim]],
                                                 altura-.28, altura+.28,
                                                 color=cores[variante], lw=0)
                    dias_representados += fim - inicio
            assert dias_representados == np.count_nonzero(posicoes)
            eixos[2, coluna].plot(limites, (curva['saldos_diarios'] / 10000 - 1) * 100,
                                 color=cores[variante], lw=1.3,
                                 ls='-' if variante == 'A' else '--',
                                 label=f"{variante}: +{numero(metrica['retorno_liquido']*100,2)}%")
            verificacoes[f'{ano}_{variante}'] = dict(origens=len(origens),
                dias_comprados=int(np.count_nonzero(posicoes > 0)), dias_vendidos=int(np.count_nonzero(posicoes < 0)),
                capital_final=float(curva['saldos_diarios'][-1]), membro=membro,
                rmse_pp=float(np.sqrt(np.mean((previsao['previsoes_retorno']-alvo)**2))*100))
        eixos[0, coluna].set_title(f'BTC · {ano} · {len(origens)} decisões', fontsize=9.5, weight='bold')
        for limite in [-.2, .2]:
            eixos[0, coluna].axhline(limite, color='#555555', ls=':', lw=1)
        eixos[0, coluna].axhspan(-.2, .2, color='#eeeeee', zorder=0)
        eixos[0, coluna].set_ylim(-.25, .35)
        eixos[0, coluna].set_yticks([-.2, 0, .2])
        eixos[0, coluna].text(.5, .19, 'Faixa sem posição', transform=eixos[0, coluna].transAxes,
                             ha='center', fontsize=8, color='#505050')
        eixos[1, coluna].set_yticks([1, 0], [f"{v} ({verificacoes[f'{ano}_{v}']['dias_comprados']} d)" for v in ['A', 'L']])
        eixos[1, coluna].set_ylim(-.5, 1.5)
        eixos[1, coluna].grid(False)
        for altura in [0, 1]:
            eixos[1, coluna].axhspan(altura-.28, altura+.28, color='#eeeeee', zorder=0)
        eixos[2, coluna].axhline(0, color='#666666', ls=':', lw=.9)
        eixos[2, coluna].set_ylim(-10, 40)
        eixos[2, coluna].set_yticks([-10, 0, 10, 20, 30, 40])
        eixos[2, coluna].legend(loc='upper left', fontsize=8, frameon=False, labelspacing=.3)
        eixos[2, coluna].xaxis.set_major_locator(datas.MonthLocator(bymonth=[3, 6, 9, 12]))
        meses = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
        eixos[2, coluna].xaxis.set_major_formatter(FuncFormatter(lambda x, _: meses[datas.num2date(x).month-1]))
        eixos[2, coluna].set_xlabel('Data (UTC)', fontsize=8.5)
        for ax in eixos[:, coluna]:
            ax.set_xlim(t[0], limites[-1])
            ax.tick_params(labelsize=8.5)
            if ax != eixos[1, coluna]:
                ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:g}'.replace('.', ',')))
    for ax, texto in zip(eixos[:, 0], ['1. Previsão (%)', '2. Posição', '3. Retorno líquido (%)']):
        ax.set_ylabel(texto, fontsize=9)
    figura(fig, 'previsoes_operacoes_artigo')
    return verificacoes


def figura_trajetoria(historico):
    """Mostra o efeito funcional; zeros são zeros, sem piso artificial positivo."""
    fig, ax = plt.subplots(figsize=(3.45, 2.8), layout='constrained')
    estilos = [('#126782', 'o', '-'), ('#b85a19', 's', '--'), ('#487d44', '^', ':')]
    for (seed, sondas), (cor, marcador, linha) in zip(historico['trajetoria_padronizacao'].items(), estilos, strict=True):
        epocas = [0 if s['checkpoint'] == 'inicial' else int(s['checkpoint'].split('_')[-1]) for s in sondas]
        diferencas = np.array([s['max_delta_sem_ramos'] for s in sondas]) * 100
        ax.plot(epocas, diferencas, color=cor, marker=marcador, ls=linha,
                label=f'Seed {seed}', ms=3.5, lw=1.1)
        np.testing.assert_array_equal(ax.lines[-1].get_ydata(), diferencas)
    ax.set_yscale('symlog', linthresh=1e-6)
    ax.set_ylim(-2e-7, 25)
    ax.set_yticks([0, 1e-6, 1e-4, .01, 1, 10],
                  ['0', r'$10^{-6}$', r'$10^{-4}$', '0,01', '1', '10'])
    ax.set_xticks([0, 10, 20, 30, 40])
    ax.axhline(0, color='#555555', lw=.7)
    ax.set_xlabel('Época do checkpoint', fontsize=8.5)
    ax.set_ylabel('Efeito máximo na previsão (p.p.)', fontsize=8.5)
    ax.set_title('Efeito de desligar os ramos Mamba', fontsize=9)
    ax.tick_params(labelsize=8)
    ax.legend(fontsize=8, frameon=False, loc='upper right')
    figura(fig, 'trajetoria_artigo')


def conferir_exploracao():
    """Conserva a proveniência dos marcos, sem unir populações distintas."""
    marcos = {}
    for nome in ['docs/protocolo_taxa_aprendizado.md', 'docs/protocolo_huber_blocos.md', 'docs/protocolo_crua_huber.md']:
        FONTES[nome] = hashlib.sha256((RAIZ/nome).read_bytes()).hexdigest()

    def conferir(nome, observado, publicado, atol=5e-11):
        np.testing.assert_allclose(observado, publicado, rtol=0, atol=atol)
        marcos[nome] = observado

    taxa = ler('dados/experimentos/taxa_aprendizado_1af0a64e83d472ac533e/publicacoes/tentativa_001/resultados.json')
    conferir('estados_horarios_mse', [taxa['medias']['teste'][f'referencia_estado{s}']['metricas']['mse'] for s in [8,16,32,64]],
             [.000498745, .000496570, .000499044, .000503767], atol=5e-10)
    assert not any(v['evidencia_favoravel_procedimento'] for v in taxa['criterio_validacao'].values())
    marcos['estados_horarios_excesso_naive_pct'] = [-100*taxa['medias']['teste'][f'referencia_estado{s}']['metricas']['habilidade_mse'] for s in [8,16,32,64]]
    crua = ler('dados/experimentos/crua_huber_1781f557fdf2b45a3ae2/publicacoes/tentativa_001/resultados.json')
    conferir('fatorial_entradas_perda_mse', [crua['medias_globais']['teste'][c]['mse'] for c in ['relativa_mse','relativa_huber','crua_mse','crua_huber']],
             [.0006185446,.0006167505,.0006146982,.0006116980])
    for c in crua['medias_globais']['teste'].values():
        assert c['blocos'] == 4 and c['seeds_por_bloco'] == 8
    marcos['entradas_perda_naive'] = crua['medias_globais']['teste']['relativa_mse']['mse_naive']
    for c in crua['contrastes']['teste'].values():
        lo, hi = c['intervalos']['14']['ic_bonferroni_98_75']
        assert lo < 0 < hi
    astra = ler('dados/experimentos/busca_astra_b34bad73d6cef1d10a97/publicacoes/tentativa_001/resultados.json')
    conferir('busca_astra_mse', [astra['medias_globais'][c]['mse'] for c in ['referencia','candidata','naive']],
             [.0006212452,.0006122753,.0006092954])
    for c in astra['contrastes'].values():
        lo, hi = c['intervalos']['14']['ic95']; assert lo < 0 < hi
    justa = ler('dados/experimentos/comparacao_astra_crua_ce284eb4a489f604fb9c/publicacoes/tentativa_001/resultados.json')
    conferir('comparacao_astra_crua_mse', [justa['medias_globais'][c]['mse'] for c in ['astra','crua']], [.0006122753,.0006114371])
    for pasta, campo, n in [('busca_astra','candidatas',11),('busca_astra_002','candidatas',12),('operacional_futuros','receitas',8)]:
        estado = ler(f'registros/{pasta}/estado.json')
        assert estado[campo] == n and estado['situacao'].startswith('concluido')
        marcos[pasta] = {campo:n, 'situacao':estado['situacao']}
    hist = ler('dados/experimentos/historico_treino_5ae264d75324c1093b39/publicacao/resumo.json')
    conferir('historico_mse', [hist['resumos'][c]['mse_media_seeds_recortes'] for c in ['acumulado','movel12']], [.0002528294,.0002552105])
    lo, hi = hist['incerteza_delta_mse_movel_menos_acumulado']['14']['ic95']; assert lo < 0 < hi
    ciclos = [('retomada_alvo_diario_de09c2193737c2581261',['preco','retorno'],[.0006257232,.0004829358]),
              ('padronizacao_diaria_f3f8772670f244779ad7',['referencia','padronizado'],[.0004829358,.0004776667]),
              ('sem_penalizacao_diaria_8a0aeee4d78503b7f50d',['referencia','sem_penalizacao'],[.0004776667,.0005025832]),
              ('taxa_diaria_64c5a9532894252c7b88',['referencia','candidata'],[.0005025832,.0010278287])]
    for ciclo, nomes, valores in ciclos:
        q = ler(f'dados/experimentos/{ciclo}/publicacao/comparacao.json')
        conferir(ciclo+'_mse', [q['fases']['teste']['medias'][c]['mse_retorno'] for c in nomes], valores)
        if ciclo.startswith('retomada_alvo'):
            marcos['diario_naive'] = q['fases']['teste']['medias']['preco']['mse_naive_retorno']
    selecao = ler('registros/generalizacao_moedas/preparacao/selecao_referencia.json')
    marcos['selecao_retrospectiva'] = selecao
    ler('registros/ensemble_2026/modelos_utilizados.json')
    comparacao = ler('dados/reavaliacoes/comparacao_cryptomamba_175055b4a72106f2588b/comparacao_base.csv', True)
    for receita, valores in [('preco_sem_padronizacao',[54.88,27.66]),('retorno_padronizado',[12.83,8.36])]:
        linha = comparacao[(comparacao.fase=='teste') & (comparacao.receita==receita)].iloc[0]
        conferir(receita+'_continuidade_pct', [linha.retorno_liquido*100, linha.drawdown*100], valores, atol=.005)
    return marcos


def executar():
    marcos_exploratorios = conferir_exploracao()
    moedas = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT']
    ponteiros = {ano: ler(f'registros/{pasta}/execucao.json') for ano, pasta in
                [(2025, 'fechamento_ramos_diarios'), (2026, 'ablacao_linear_2026')]}
    for ptr in ponteiros.values():
        p = RAIZ / ptr['pasta'] / 'congelamento.json'
        assert hashlib.sha256(p.read_bytes()).hexdigest() == ptr['congelamento_sha256']
    ler('registros/fechamento_ramos_diarios/conferencia_posterior.json')
    ler('registros/ablacao_linear_2026/conferencia_posterior.json')
    integridade = {}
    for ano, nome in [(2025, 'fechamento.json'), (2026, 'manifesto.json')]:
        base = ponteiros[ano]['pasta']
        manifesto = ler(f'{base}/{nome}')
        for arquivo, esperado in manifesto['arquivos'].items():
            with (RAIZ/base/arquivo).open('rb') as f:
                assert hashlib.file_digest(f, 'sha256').hexdigest() == esperado, arquivo
        integridade[ano] = len(manifesto['arquivos'])
    p25 = ler('registros/fechamento_ramos_diarios/publicacao_final/comparacao.csv', True)
    p25 = p25[p25.fase == 'teste']
    p26 = ler('registros/ablacao_linear_2026/publicacao/previsoes.csv', True)
    f25 = ler('registros/fechamento_ramos_diarios/publicacao_final/carteiras.csv', True)
    f25 = f25[(f25.fase == 'teste') & (f25.custo == 1)].rename(columns={'simbolo': 'moeda'})
    f26 = ler('registros/ablacao_linear_2026/publicacao/carteiras.csv', True)
    f26 = f26[f26.custo == 1]
    pv25 = {m: ler(f"{ponteiros[2025]['pasta']}/{m}/publicacao/previsao.json") for m in moedas}
    pv26 = ler(f"{ponteiros[2026]['pasta']}/previsao.json")

    def pred(ano, moeda, variante, forma):
        if ano == 2025:
            z = p25[(p25.simbolo == moeda) & (p25.variante == variante) & (p25.forma == forma)]
            assert len(z) == 1
            return z.iloc[0]
        unidade = variante if forma == 'referencia' else f'{variante}_{forma}'
        z = p26[(p26.moeda == moeda) & (p26.unidade == unidade)]
        assert len(z) == 1
        r = z.iloc[0]
        return dict(mse=r.mse_retorno, rmse_pp=r.rmse_retorno*100,
                    mae_pp=r.mae_retorno*100, acerto_balanceado_pct=r.acerto_balanceado*100)

    def fin(ano, moeda, v, forma):
        df = f25 if ano == 2025 else f26
        unidades = [f'{v}_{s}' for s in [42, 17, 2026]] if forma == 'media_seeds' else [f'{v}_ensemble' if forma == 'ensemble' else v]
        z = df[(df.moeda == moeda) & df.unidade.isin(unidades)]
        assert len(z) == len(unidades), (ano, moeda, unidades)
        return z.select_dtypes(include='number').mean()

    linhas = []
    for v, wd, par in [('A','0,001','136.952'),('B','0','136.952'),('L','0,001','824'),('L0','0','824')]:
        a, e = (pred(2025,'BTCUSDT',v,x) for x in ['media_seeds','ensemble'])
        linhas.append([v,wd,par,numero(a['mse']*1e4,4),numero(e['mse']*1e4,4),
                       numero(a['retorno_liquido_pct'],2),numero(e['retorno_liquido_pct'],2)])
    tabela('fatorial',r'Modelo & $\lambda$ & Parâmetros & MSE médio & MSE ensemble & Retorno médio & Retorno ensemble',linhas,'lrrrrrr')
    linhas = []
    for ano in [2025,2026]:
        for m in moedas:
            a,l,ae,le,n,r = [pred(ano,m,v,f) for v,f in [('A','media_seeds'),('L','media_seeds'),('A','ensemble'),('L','ensemble'),('naive','referencia'),('linear','referencia')]]
            linhas.append([str(ano),m[:-4],*[numero(x['rmse_pp'],4) for x in [a,l,ae,le,n,r]],*[numero(x['mae_pp'],4) for x in [ae,le]],*[numero(x['acerto_balanceado_pct'],2) for x in [ae,le]]])
    tabela('previsoes',r'& & \multicolumn{6}{c}{RMSE (pontos percentuais)} & \multicolumn{2}{c}{MAE (p.p.)} & \multicolumn{2}{c}{BA (\%)} \\'+'\n'+r'\cmidrule(lr){3-8}\cmidrule(lr){9-10}\cmidrule(lr){11-12}'+'\n'+r'Ano & Ativo & $\overline{A}$ & $\overline{L}$ & $A_e$ & $L_e$ & Naive & Ridge & $A_e$ & $L_e$ & $A_e$ & $L_e$',linhas,'llrrrrrrrrrr')
    linhas = []
    for ano in [2025,2026]:
        for m in moedas:
            a,l,ae,le = [fin(ano,m,v,f) for v,f in [('A','media_seeds'),('L','media_seeds'),('A','ensemble'),('L','ensemble')]]
            linhas.append([str(ano),m[:-4],*[numero(x.retorno_liquido*100,2) for x in [a,l,ae,le]],*[numero(x.drawdown_maximo*100,2) for x in [ae,le]],*[str(int(x.dias_posicionado)) for x in [ae,le]]])
    tabela('operacoes',r'& & \multicolumn{4}{c}{Retorno líquido (\%)} & \multicolumn{2}{c}{Drawdown (\%)} & \multicolumn{2}{c}{Dias expostos} \\'+'\n'+r'\cmidrule(lr){3-6}\cmidrule(lr){7-8}\cmidrule(lr){9-10}'+'\n'+r'Ano & Ativo & $\overline{A}$ & $\overline{L}$ & $A_e$ & $L_e$ & $A_e$ & $L_e$ & $A_e$ & $L_e$',linhas,'llrrrrrrrr')

    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.18,'pdf.fonttype':42})
    fig, axs = plt.subplots(1,3,figsize=(10,3.4),layout='constrained')
    paines = [
        ('Capacidade horária\n6 seeds · divisão única', ['8 estados','16 estados','32 estados','64 estados'],
         marcos_exploratorios['estados_horarios_excesso_naive_pct']),
        ('Entradas e perda horárias\n8 seeds · 4 blocos', ['Relativa + MSE','Relativa + Huber','Níveis + MSE','Níveis + Huber'],
         100*(np.array(marcos_exploratorios['fatorial_entradas_perda_mse'])/marcos_exploratorios['entradas_perda_naive']-1)),
        ('Alvo e escala diários\n3 seeds · divisão fixa', ['Preço','Retorno','Retorno + z-score'],
         100*(np.array([*marcos_exploratorios['retomada_alvo_diario_de09c2193737c2581261_mse'],marcos_exploratorios['padronizacao_diaria_f3f8772670f244779ad7_mse'][1]])/marcos_exploratorios['diario_naive']-1))]
    for ax,(titulo,rotulos,valores) in zip(axs,paines):
        ys=np.arange(len(rotulos));ax.barh(ys,valores,height=.55,color='#176080')
        ax.set_yticks(ys,rotulos,fontsize=8.5);ax.invert_yaxis();ax.set_title(titulo,fontsize=10)
        ax.axvline(0,color='black',lw=.7);ax.set_xlim(0,max(valores)*1.4)
        for y,v in zip(ys,valores):ax.text(v+max(valores)*.04,y,numero(v,2)+'%',va='center',fontsize=9)
        ax.set_xlabel('Excesso de MSE sobre Naive (%)\nZero = erro do Naive',fontsize=9)
    figura(fig,'exploracao_artigo')
    fig,axs=plt.subplots(1,2,figsize=(10,4.3),layout='constrained')
    for ax,forma,titulo in zip(axs,['medias_individuais','ensemble'],['Média dos erros individuais','Erro do ensemble']):
        for i,m in enumerate(moedas):
            for ano,dy,cor in [(2025,-.12,'#176080'),(2026,.12,'#b45a25')]:
                if ano==2025:
                    nome='A_menos_L' if m=='BTCUSDT' else 'L_menos_A'
                    q=pv25[m]['contrastes_mse']['teste'][forma][nome]['14'];sinal=-1 if m=='BTCUSDT' else 1
                else:
                    q=pv26[m]['contrastes_mse'][forma]['L_menos_A']['14'];sinal=1
                base=pred(ano,m,'A','media_seeds' if forma=='medias_individuais' else 'ensemble')['mse']
                limites=sorted(sinal*100*x/base for x in q['ic95'])
                ax.plot(limites,[i+dy]*2,color=cor,lw=2)
                ax.plot(sinal*100*q['media']/base,i+dy,'o',color=cor,label=str(ano) if i==0 else None,ms=5)
        ax.axvline(0,color='black',lw=.8);ax.set_yticks(range(4),[m[:-4] for m in moedas]);ax.invert_yaxis()
        ax.set_title(titulo);ax.set_xlabel('Diferença de MSE L − A (% do MSE de A)\nNegativo: menor erro em L');ax.legend(loc='best')
    figura(fig,'contrastes_artigo')
    historico=ler('registros/fechamento_ramos_diarios/diagnostico_previo.json')
    figura_trajetoria(historico)

    from matplotlib.patches import FancyBboxPatch
    fig,ax=plt.subplots(figsize=(10,5.1));ax.set(xlim=(0,10),ylim=(0,5.1));ax.axis('off')
    def caixa(x,y,w,h,t,cor):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.03',fc=cor,ec='#394954',lw=.7))
        ax.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=9.5)
    ax.text(5,4.85,'Um sistema por moeda: BTC, ETH, BNB e XRP · avaliação offline',ha='center',fontsize=11,weight='bold')
    caixa(.05,3.15,1.75,1.35,'Binance USD-M\nCandles diários\nOHLCV + tempo\nDados verificados','#e5eef2')
    caixa(2.1,3.15,2.05,1.35,'Janela de 14 dias\nz-score do treino\nTensor [lote, 6, 14]\nAlvo: retorno diário','#e5eef2')
    caixa(4.45,3.15,3.0,1.35,'Rede A · scan dos canais\n3 estágios × 4 blocos\nLarguras 14 → 16 → 32 → 1\nCabeça 6 → 1; estado 64\n136.952 parâmetros','#dcecf5')
    caixa(7.75,3.15,2.1,1.35,'Três redes A\nSeeds 42 / 17 / 2026\nMédia das previsões\nEnsemble por moeda','#dcecf5')
    for x in [1.85,4.2,7.5]:ax.annotate('',(x+.22,3.8),(x,3.8),arrowprops={'arrowstyle':'->','color':'#394954'})
    caixa(6.6,1.45,3.25,1.1,'Política separada\nFiltro ±0,2%; manter o lado\nCustos, funding e restrições','#f3ecd9')
    ax.annotate('',(8.8,2.6),(8.8,3.1),arrowprops={'arrowstyle':'->','color':'#394954'})
    caixa(3.3,1.45,2.95,1.1,'Avaliação e rastreabilidade\nErro e direção; lucro e risco\nIndividuais ≠ ensemble','#dfeadc')
    ax.annotate('',(6.3,2),(6.55,2),arrowprops={'arrowstyle':'->','color':'#394954'})
    caixa(.05,1.45,2.9,1.1,'Comparações diagnósticas\nNaive, Ridge e L (824 par.)\nL: projeções, sem blocos','#f4e8da')
    ax.annotate('',(3.25,2),(3.0,2),arrowprops={'arrowstyle':'->','color':'#394954'})
    caixa(.05,.2,3.0,.8,'2020–2023\nTreino e escalas','#dfeadc')
    caixa(3.35,.2,2.05,.8,'2024\nValidação','#f3ecd9')
    caixa(5.7,.2,1.85,.8,'2025\nRetrospectiva','#ebdfe8')
    caixa(7.85,.2,2.0,.8,'2026 (até 10/11)\nPesos congelados','#ebdfe8')
    figura(fig,'estrutura_artigo')

    series_operacionais = figura_previsoes_operacoes(ponteiros)

    # Conferência cruzada das tabelas com os JSONs originais, sem nova inferência.
    n_conferencias=0
    mapeamento = {'mse': ('mse_retorno',1), 'rmse_pp': ('rmse_retorno',100),
                 'mae_pp': ('mae_retorno',100), 'acerto_balanceado_pct': ('acerto_balanceado',100)}
    for ano in [2025,2026]:
        for m in moedas:
            for v in ['A','L']:
                for forma in ['media_seeds','ensemble']:
                    if ano==2025:
                        original=pv25[m]['medias_seeds']['teste'][v] if forma=='media_seeds' else pv25[m]['ensemble']['teste'][v]
                    else:
                        original=pv26[m]['medias_seeds'][v] if forma=='media_seeds' else pv26[m]['metricas'][f'{v}_ensemble']
                    for campo,(chave,escala) in mapeamento.items():
                        esperado=(original[chave]['media'] if forma=='media_seeds' else original[chave])*escala
                        np.testing.assert_allclose(pred(ano,m,v,forma)[campo],esperado,rtol=1e-12,atol=1e-14);n_conferencias+=1
    n_financeiras=0
    for ano in [2025,2026]:
        for m in moedas:
            documento=ler(f"{ponteiros[ano]['pasta']}/{m}/publicacao/operacoes.json") if ano==2025 else ler(f"{ponteiros[ano]['pasta']}/operacoes.json")
            df=f25 if ano==2025 else f26
            for linha in documento['carteiras']:
                if linha['custo']!=1 or (ano==2025 and linha['fase']!='teste') or (ano==2026 and linha['moeda']!=m):continue
                item=df[(df.moeda==m)&(df.unidade==linha['unidade'])].iloc[0]
                for campo in ['retorno_liquido','drawdown_maximo','dias_posicionado','dias_comprado','dias_vendido','comissoes','custo_slippage_ticks','funding']:
                    np.testing.assert_allclose(item[campo],linha['metricas'][campo],rtol=1e-12,atol=1e-12);n_financeiras+=1
    for nome,h in FONTES.items():assert hashlib.sha256((RAIZ/nome).read_bytes()).hexdigest()==h
    saidas={p.relative_to(BASE).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for pasta,ext in [('latex/tabelas','*.tex'),('latex/figs','*_artigo.pdf')] for p in (BASE/pasta).glob(ext)}
    recibo=dict(escopo='Materiais editoriais derivados; sem treino, inferência ou novo backtest',fontes=FONTES,saidas=saidas,marcos_exploratorios=marcos_exploratorios,conferencias_metricas=n_conferencias,conferencias_financeiras=n_financeiras,integridade=integridade,receitas=ponteiros,series_operacionais=series_operacionais)
    (BASE/'materiais/evidencias_artigo.json').write_text(json.dumps(recibo,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Materiais gerados; {n_conferencias} métricas e {n_financeiras} valores financeiros conferidos; {len(FONTES)} fontes preservadas.')


if __name__=='__main__':executar()
