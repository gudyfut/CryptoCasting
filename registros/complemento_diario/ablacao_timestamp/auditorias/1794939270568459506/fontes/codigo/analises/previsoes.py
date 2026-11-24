"""Diagnóstico das séries preservadas: zero treinamento e zero inferência nova."""
import shutil
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,agora,identidade,ler_json,salvar_json,sha256,conferir_arquivos,fontes
from experimentos.comum import estudo_anterior
from .metricas import analisar


def executar():
    ptr,pub,r,refs=estudo_anterior()
    fs=fontes('analises');fs['codigo/experimentos/comum.py']=sha256(RAIZ/'codigo/experimentos/comum.py')
    insumos={}
    for k,t in refs.items():
        for b in ('validacao','teste'):insumos[(t/f'previsoes_{b}.parquet').relative_to(RAIZ).as_posix()]=sha256(t/f'previsoes_{b}.parquet')
    assinatura={'fontes':fs,'insumos':insumos,'populacao':'53séries anteriores ao CryptoMamba; mesmas origens por partição',
        'metodo':'MSE/MAE/mediana/p95; vitórias e empates vs Naive; Pearson/Spearman descritivos; trimestres por calendário; faixas diárias derivadas só de validação',
        'criterio_selecao':'nenhum; diagnóstico retrospectivo de previsões já publicadas'}
    codigo=identidade(assinatura)[:20];dest=RAIZ/'registros/diagnosticos_previsoes'/codigo
    if dest.exists():
        conferir_arquivos(dest,ler_json(dest/'manifesto.json')['arquivos']);return dest/'resultado.json'
    dest.mkdir(parents=True)
    for n in fs:
        q=dest/'fontes'/n;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(RAIZ/n,q)
    salvar_json(dest/'congelamento.json',{'utc':agora(),'id':codigo,'assinatura':assinatura})
    naive={b:pd.read_parquet(refs['naive']/f'previsoes_{b}.parquet') for b in ('validacao','teste')}
    res={}
    for k,t in refs.items():
        val=pd.read_parquet(t/'previsoes_validacao.parquet')
        res[k]={b:analisar(pd.read_parquet(t/f'previsoes_{b}.parquet'),val,naive[b]) for b in naive}
    grupos={'mamba16_seis':[f'estado16_{s}' for s in (17,42,2026,7,123,31415)],
        'mamba16_tres':[f'estado16_{s}' for s in (17,42,2026)],'lstm_tres':[f'lstm_{s}' for s in (17,42,2026)],'naive':['naive'],'arima':['arima']}
    medias={}
    for b in naive:
        medias[b]={}
        for nome,ks in grupos.items():
            medias[b][nome]={}
            for horario in ('todas_origens','origens00utc'):
                campos=res[ks[0]][b][horario]
                medias[b][nome][horario]={campo:float(np.mean([res[k][b][horario][campo] for k in ks]))
                    if all(res[k][b][horario][campo] is not None for k in ks) else None for campo in campos}
    resultado={'utc':agora(),'id':codigo,'series':53,'novos_treinamentos':0,'medias':medias,'por_serie':res,
        'limites':['Correlações descritivas, sem p-valor IID.','Horas sobrepostas não são replicações independentes.',
                   'Médias das métricas de modelos individuais, não ensemble.','Faixas não criam política operacional e não foram escolhidas pelo teste.',
                   'Todos os períodos já conhecidos: diagnóstico retrospectivo.']}
    salvar_json(dest/'resultado.json',resultado)
    conferir_arquivos(RAIZ,insumos);conferir_arquivos(RAIZ,fs)
    figuras=figura(dest,resultado,grupos['mamba16_seis'])
    relatorio(resultado,figuras)
    salvar_json(dest/'manifesto.json',{'arquivos':{q.relative_to(dest).as_posix():sha256(q) for q in dest.rglob('*') if q.is_file()}})
    salvar_json(RAIZ/'registros/diagnosticos_previsoes/atual.json',{'arquivo':(dest/'resultado.json').relative_to(RAIZ).as_posix(),
                'sha256':sha256(dest/'resultado.json'),'manifesto_sha256':sha256(dest/'manifesto.json'),
                'relatorio':'docs/diagnostico_previsoes.md','figuras':figuras})
    return dest/'resultado.json'


def figura(dest,r,chaves):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axs=plt.subplots(1,2,figsize=(11,4.3))
    for ax,b,titulo in zip(axs,['validacao','teste'],['2024: desenvolvimento','2025: retrospectivo']):
        conjuntos=[r['por_serie'][k][b]['faixas00utc']['faixas'] for k in chaves]
        for campo,label,cor in [('previsao_media','Alta/queda prevista','#27688D'),('retorno_observado_medio','Retorno observado','#AF7A32')]:
            ys=[]
            for i in range(5):
                vs=[v[i][campo] for v in conjuntos if len(v)==5 and v[i][campo] is not None]
                ys.append(np.mean(vs)*100 if vs else np.nan)
            ax.plot(range(1,6),ys,marker='o',label=label,color=cor)
        ax.axhline(0,color='#888',lw=.8);ax.set_title(titulo,loc='left');ax.set_xticks(range(1,6))
        ax.set_xlabel('Faixa de previsão: menor → maior');ax.grid(axis='y',alpha=.2);ax.spines[['top','right']].set_visible(False)
        ax.legend(frameon=False,fontsize=8)
    axs[0].set_ylabel('Log-retorno × 100 (aprox. pontos percentuais)')
    fig.suptitle('Mamba16: prever uma alta maior identificou retornos maiores?',fontsize=13,x=.08,ha='left')
    fig.text(.08,.015,'Decisões 00UTC · limites definidos em validação · médias de estratos de seis modelos individuais · sem inferência causal',fontsize=8,color='#555')
    fig.subplots_adjust(top=.78,bottom=.22,left=.08,right=.98,wspace=.25)
    pasta=RAIZ/f'docs/figuras/diagnostico_{r["id"]}';pasta.mkdir(parents=True)
    arqs={}
    for ext in ('png','svg'):
        q=pasta/f'faixas_previsao.{ext}';fig.savefig(q,dpi=170,bbox_inches='tight',facecolor='white');arqs[q.relative_to(RAIZ).as_posix()]=sha256(q)
    plt.close(fig);return arqs


def relatorio(r,figuras):
    linhas=['# Informação nas previsões já treinadas','',f'Diagnóstico `{r["id"]}`:53séries preservadas, sem novos ajustes ou inferência. As estatísticas são descrições retrospectivas e não mudam o critério de seleção dos estudos anteriores.',
        '', '## Médias dos modelos nas origens diárias','',
        'MSE continua avaliando precisão. Correlações medem associação, não amplitude correta ou lucro. Vitórias contam erros absolutos menores que Naive; empates aparecem separados. P95 é o percentil95 do erro absoluto, não risco financeiro. Grupos de seis e três seeds não são equivalentes; usar Mamba16/três para comparar com LSTM.',
        '', '| Parte | Grupo | MSE | MAE×100 | P95×100 | Vitória vs Naive | Empates | Pearson | Spearman |','|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for b,grupos in r['medias'].items():
        for nome,horarios in grupos.items():
            m=horarios['origens00utc'];fmt=lambda x:'indefinida' if x is None else f'{x:.4f}'
            linhas.append(f'| {b} | {nome} | {m["mse"]:.9f} | {m["mae"]*100:.4f} | {m["p95_erro_absoluto"]*100:.4f} | {m["vitorias_referencia"]*100:.2f}% | {m["empates_referencia"]*100:.2f}% | {fmt(m["pearson"])} | {fmt(m["spearman"])} |')
    linhas+=['','## Como interpretar as faixas','',
        'Para cada seed, os cortes20/40/60/80% vêm somente de suas previsões diárias na validação. Aplicam-se os mesmos cortes ao teste; faixas podem ter tamanhos diferentes ou ficar vazias. Previsão constante forma uma faixa. A figura média não é uma carteira, ensemble ou previsão negociável. Uma curva observada crescente seria evidência descritiva de ordenação; é preciso avaliar estabilidade e incerteza, sem escolher cortes pelo lucro.',
        '',f'![Faixas](figuras/diagnostico_{r["id"]}/faixas_previsao.png)',
        '', '## Limites e uso','',
        'Resultados completos por seed, trimestre, todas as origens e00UTC estão no [registro](../registros/diagnosticos_previsoes/atual.json). Sem p-valores de correlação que presumam independência; previsões horárias24h se sobrepõem. Não filtrar treinamento pela magnitude do retorno futuro. Cortes aqui são diagnósticos, sem nova regra operacional. A escolha da hipótese de scheduler antecede este diagnóstico; não se muda o protocolo após ver estas curvas.2024/2025 já foram consultados; não são holdout novo. Os estudos CryptoMamba permanecem no histórico, fora desta comparação de53séries.']
    p=RAIZ/'docs/diagnostico_previsoes.md'
    if p.exists():raise FileExistsError('Relatório existente; preservar e revisar com recibo próprio.')
    p.write_text('\n'.join(linhas)+'\n',encoding='utf-8')
