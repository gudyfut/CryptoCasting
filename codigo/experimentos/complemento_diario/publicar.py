"""Tabelas integrais e figuras de resultados auditados, fora do artigo."""
from pathlib import Path
import shutil
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256, conferir_arquivos
from .comum import contexto, congelar, exclusividade, fechar, registrar_estado
from .inventario import REG, relativo


def salvar_figura(fig, pasta, nome):
    fig.savefig(pasta / (nome+'.png'), dpi=180, bbox_inches='tight')
    fig.savefig(pasta / (nome+'.pdf'), bbox_inches='tight')
    plt.close(fig)


def tabelas_previsoes(p, destino, prefixo):
    previsao = ler_json(p / 'publicacao/previsao.json')
    linhas, contrastes = [], []
    for bloco, q in previsao.items():
        for unidade, m in q['metricas'].items():
            linhas.append(dict(bloco=bloco, unidade=unidade, forma='ensemble' if unidade.endswith('_ensemble') else 'referencia' if unidade == 'naive' else 'individual', **m))
        for variante, medidas in q['medias'].items():
            linhas.append(dict(bloco=bloco, unidade=variante+'_media_seeds', forma='media_metricas_individuais', **{k: v['media'] for k, v in medidas.items()}))
        for nome, por_bloco in q['contrastes_mse'].items():
            for comprimento, ic in por_bloco.items():
                contrastes.append(dict(bloco=bloco, contraste=nome, tamanho_bloco=int(comprimento),
                    diferenca_media=ic['media'], ic95_inferior=ic['ic95'][0], ic95_superior=ic['ic95'][1], metrica='MSE'))
    ops = ler_json(p / 'publicacao/operacoes.json')
    op_linhas, semestres, episodios = [], [], []
    for x in ops['carteiras']:
        r = ler_json(p / 'carteiras' / x['membro'] / 'recibo.json')
        base = {k: x[k] for k in ('bloco', 'unidade', 'custo')}
        op_linhas.append(dict(**base, forma='ensemble' if x['unidade'].endswith('_ensemble') else 'individual', **x['metricas']))
        semestres.extend(dict(**base, **q) for q in r['descricao']['semestres'])
        episodios.extend(dict(**base, **q) for q in r['descricao']['episodios'])
    for chave, medidas in ops['medias_seeds'].items():
        if not medidas.get('incompleto'):
            op_linhas.append(dict(identidade=chave, forma='media_metricas_carteiras_individuais', **{k: v['media'] for k, v in medidas.items()}))
    for chave, cs in ops['contrastes_crescimento_log_diario'].items():
        if not cs.get('incompleto'):
            for nome, por_bloco in cs.items():
                for comprimento, ic in por_bloco.items():
                    contrastes.append(dict(bloco_custo=chave, contraste=nome, tamanho_bloco=int(comprimento),
                        diferenca_media=ic['media'], ic95_inferior=ic['ic95'][0], ic95_superior=ic['ic95'][1], metrica='crescimento_log_diario'))
    for nome, valores in [('previsoes', linhas), ('contrastes', contrastes), ('operacoes', op_linhas), ('semestres', semestres), ('episodios', episodios)]:
        pd.DataFrame(valores).to_csv(destino / f'{prefixo}_{nome}.csv', index=False)
    return previsao, pd.DataFrame(linhas)


def executar():
    etapas = ['lstm_walkforward', 'sensibilidade_filtro', 'deslocamento_exposicao', 'referencias_exposicao']
    decisao = ler_json(REG / 'ablacao_timestamp/decisao.json')
    if decisao['executar']:
        etapas.append('ablacao_timestamp')
    deps, pastas = [], {}
    for etapa in etapas:
        q = ler_json(REG / etapa / 'conferencia_posterior.json')
        assert q['situacao'] == 'aprovada' and sha256(RAIZ / q['arquivo']) == q['sha256']
        ptr, p, f = contexto(etapa)
        pastas[etapa] = p
        conferir_arquivos(p, ler_json(p / 'fechamento.json')['arquivos'])
        deps += [REG / etapa / 'conferencia_posterior.json', RAIZ / q['arquivo'], p / 'fechamento.json']
        deps += [x for x in (p / 'publicacao').rglob('*') if x.is_file()]
    qp = ler_json(REG / 'qualificacao_operacional.json')
    etapa = 'sintese_complemento'
    with exclusividade(etapa):
        ptr, p, f = congelar(etapa, deps, RAIZ / qp['arquivo'], dict(etapas=etapas, decisao_timestamp=decisao))
        pub = p / 'publicacao'
        pub.mkdir()
        plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False})
        previsao, tabela = tabelas_previsoes(pastas['lstm_walkforward'], pub, 'lstm_walkforward')
        fig, eixos = plt.subplots(2, 2, figsize=(10, 6), constrained_layout=True)
        cores = {'A': '#2979a8', 'L': '#f0a030', 'LSTM': '#5b8b45'}
        for ax, (bloco, q) in zip(eixos.flat, previsao.items()):
            for i, v in enumerate(cores):
                seeds = [q['metricas'][f'{v}_{s}']['habilidade_mse_retorno_naive'] for s in (42, 17, 2026)]
                ax.scatter([i-.13]*3, seeds, color=cores[v], marker='o', alpha=.65, s=22)
                ax.scatter(i, q['medias'][v]['habilidade_mse_retorno_naive']['media'], color=cores[v], marker='s', s=45)
                ax.scatter(i+.13, q['metricas'][v+'_ensemble']['habilidade_mse_retorno_naive'], color=cores[v], marker='D', s=40)
            ax.axhline(0, color='gray', lw=.8)
            ax.set(xticks=range(3), xticklabels=list(cores), title=bloco, ylabel='Habilidade MSE frente ao Naive')
            ax.grid(axis='y', alpha=.2)
        fig.suptitle('Walk-forward BTC: círculos = seeds; quadrado = média; losango = ensemble\nComparação retrospectiva de receitas; valores maiores indicam menor MSE')
        salvar_figura(fig, pub, 'lstm_habilidade_por_bloco')
        linhas_ic = pd.read_csv(pub / 'lstm_walkforward_contrastes.csv')
        figura_ic(linhas_ic, pub, 'lstm_contrastes_mse', 'LSTM menos referência: IC pareado em blocos de 14 dias')
        sens = pastas['sensibilidade_filtro']
        df = pd.read_csv(sens / 'publicacao/carteiras.csv')
        shutil.copyfile(sens / 'publicacao/carteiras.csv', pub / 'sensibilidade_carteiras.csv')
        extras = {k: [] for k in ('semestres', 'episodios', 'exposicao')}
        for x in df.to_dict('records'):
            r = ler_json(sens / 'carteiras' / x['membro'] / 'recibo.json')
            if r['situacao'] != 'concluida_conferida':
                continue
            base = {k: x[k] for k in ('populacao', 'moeda', 'variante', 'filtro', 'custo', 'membro')}
            for campo in ('semestres', 'episodios'):
                extras[campo].extend(dict(**base, **q) for q in r['descricao'][campo])
            extras['exposicao'].append(dict(**base,
                **{'decisoes_'+k: v for k, v in r['descricao']['decisoes'].items()},
                **{'dias_'+k: v for k, v in r['descricao']['exposicao_executada'].items()},
                reversoes_diretas=r['descricao']['reversoes_diretas'], episodios=r['descricao']['quantidade_episodios']))
        for campo, valores in extras.items():
            pd.DataFrame(valores).to_csv(pub / f'sensibilidade_{campo}.csv', index=False)
        df['caso'] = df['populacao']+' / '+df['moeda'].str.replace('USDT', '')+' / '+df['variante']
        for campo, titulo in [('retorno_liquido', 'Retorno líquido (%)'), ('drawdown_maximo', 'Drawdown máximo (%)'), ('fracao_tempo_posicionado', 'Dias com exposição (%)')]:
            matriz = df.pivot(index='caso', columns=['filtro', 'custo'], values=campo).sort_index(axis=1)*100
            fig, ax = plt.subplots(figsize=(10, 12), constrained_layout=True)
            im = ax.imshow(matriz.to_numpy(), aspect='auto', cmap='RdYlBu' if campo == 'retorno_liquido' else 'YlOrBr')
            ax.set(yticks=np.arange(len(matriz)), yticklabels=matriz.index,
                xticks=range(len(matriz.columns)), xticklabels=[f'{filtro*100:.2f}%\nC{custo}' for filtro, custo in matriz.columns],
                title=titulo+' — matriz completa de sensibilidade')
            fig.colorbar(im, ax=ax, shrink=.65, label=titulo)
            fig.supxlabel('Filtro / custo: C1, C2, C3 = slippage 0,01%, 0,02%, 0,03% por lado\nCarteiras independentes; nenhum cenário selecionado')
            salvar_figura(fig, pub, 'sensibilidade_'+campo)
        desloc = pastas['deslocamento_exposicao']
        df = pd.read_csv(desloc / 'publicacao/carteiras.csv')
        resumo = ler_json(desloc / 'publicacao/resultados.json')
        shutil.copyfile(desloc / 'publicacao/carteiras.csv', pub / 'deslocamentos_carteiras.csv')
        percentis = []
        ids = list(resumo['resumos'])
        fig, eixos = plt.subplots(1, 3, figsize=(15, 12), constrained_layout=True)
        for ax, campo, escala, rotulo in zip(eixos, ['retorno_liquido', 'crescimento_log_diario', 'drawdown_maximo'], [100, 10000, 100], ['Retorno líquido (%)', 'Crescimento log diário (pb)', 'Drawdown máximo (%)']):
            for i, caso in enumerate(ids):
                locais = df[df['membro'].str.startswith(caso+'/')]
                validas = locais[locais.situacao == 'concluida_conferida']
                info = resumo['resumos'][caso]
                met = info['metricas'][campo]
                if len(validas):
                    ax.boxplot([validas[campo].to_numpy()*escala], positions=[i], vert=False, widths=.55, showfliers=True,
                        flierprops={'markersize': 2, 'alpha': .35})
                ax.plot(met['original']*escala, i, 'D', color='#bb302b', markersize=4)
                percentis.append(dict(caso=caso, metrica=campo, original=met['original'], percentil=met['percentil_descritivo'],
                    validas=info['validas'], falhas=info['falhas_prudenciais'], sequencias_distintas=info['sequencias_distintas'], constante=info['sequencia_original_constante']))
            ax.set(yticks=range(24), yticklabels=[x.replace('fixa_', '').replace('USDT', '') for x in ids], xlabel=rotulo)
            ax.invert_yaxis()
            ax.grid(axis='x', alpha=.2)
        fig.suptitle('99 deslocamentos circulares por caso; losango vermelho = carteira original\nDistribuições condicionais retrospectivas, sem interpretação como p-valor; multiplicidades mantidas')
        salvar_figura(fig, pub, 'deslocamentos_distribuicoes')
        pd.DataFrame(percentis).to_csv(pub / 'deslocamentos_percentis.csv', index=False)
        shutil.copyfile(pastas['referencias_exposicao'] / 'publicacao/referencias.csv', pub / 'referencias_exposicao.csv')
        if 'ablacao_timestamp' in pastas:
            t, tab = tabelas_previsoes(pastas['ablacao_timestamp'], pub, 'timestamp')
            figura_ic(pd.read_csv(pub / 'timestamp_contrastes.csv'), pub, 'timestamp_contrastes_mse', 'Retirada do timestamp: diferença de MSE e IC de 14 dias')
            ramos = ler_json(pastas['ablacao_timestamp'] / 'publicacao/ramos.json')['populacoes']
            pd.DataFrame([dict(identidade=k, **v) for k, v in ramos.items()]).to_csv(pub / 'timestamp_ramos.csv', index=False)
            fig, ax = plt.subplots(figsize=(10, 5), constrained_layout=True)
            chaves = [f'{b}/{s}' for b in ('B1', 'B2', 'B3', 'B4') for s in (42, 17, 2026)]
            for deslocamento, fase in zip([-.16, 0, .16], ['treino', 'validacao', 'teste']):
                ax.scatter(np.arange(12)+deslocamento, [ramos[k+'/'+fase]['max_abs'] for k in chaves], label=fase, s=25)
            ax.set(xticks=range(12), xticklabels=chaves, ylabel='Máxima diferença absoluta no retorno previsto',
                title='Novos checkpoints A: intervenção nos ramos em todas as janelas')
            ax.set_yscale('symlog', linthresh=1e-12)
            ax.tick_params(axis='x', rotation=45)
            ax.legend()
            ax.grid(axis='y', alpha=.2)
            salvar_figura(fig, pub, 'timestamp_ramos')
        salvar_json(pub / 'consulta.json', dict(utc=agora(), etapas={k: relativo(v) for k, v in pastas.items()},
            natureza='Publicação analítica fora do artigo; valores sem anualização para os recortes.',
            limites=['Retrospectivo, sem confirmação intocada.', 'Receitas e períodos não estabelecem vencedor global.',
                'Média individual distinta de ensemble.', 'Intervalos financeiros medem crescimento log diário, não retorno acumulado.',
                'Deslocamentos não são estratégias causais nem testes exatos.', 'Drawdown semestral usa fechamentos diários; principal usa envelope intraminuto.']))
        fechar(etapa, dict(tabelas=len(list(pub.glob('*.csv'))), figuras=len(list(pub.glob('*.png'))), inspecao_visual='pendente'))
        registrar_estado(etapa, 'publicado_inspecao_pendente', publicacao=relativo(pub))


def figura_ic(tabela, pasta, nome, titulo):
    dados = tabela[(tabela.metrica == 'MSE') & (tabela.tamanho_bloco == 14)]
    fig, ax = plt.subplots(figsize=(10, max(5, len(dados)*.25)), constrained_layout=True)
    for i, x in enumerate(dados.to_dict('records')):
        cor = '#2979a8' if x['contraste'].endswith('individuais') else '#b35c27'
        ax.plot([x['ic95_inferior'], x['ic95_superior']], [i, i], color=cor, lw=1.5)
        ax.plot(x['diferenca_media'], i, 'o', color=cor, markersize=3)
    ax.axvline(0, color='gray', lw=1)
    ax.set(yticks=range(len(dados)), yticklabels=[x['bloco']+' / '+x['contraste'] for x in dados.to_dict('records')],
        xlabel='Diferença de MSE (retorno decimal ao quadrado); menor favorece o termo à esquerda', title=titulo)
    ax.invert_yaxis()
    ax.grid(axis='x', alpha=.2)
    salvar_figura(fig, pasta, nome)


if __name__ == '__main__':
    executar()
