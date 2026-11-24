"""Médias individuais, controles, bootstrap temporal e figuras do ciclo fechado."""
import math
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,sha256,agora


def resumo(chaves,res):
    linhas=[res[k] for k in chaves];n=len(linhas)
    r={c:float(np.mean([l[c] for l in linhas])) for c in ('capital_final','retorno_liquido','drawdown_minuto_close','exposicao_media','ordens_executadas','compras','vendas','comissoes_usdt','slippage_usdt','giro_capital_inicial','valor_residual_usdt')}
    r.update(n_seeds=n,desvio_retorno_seeds=float(np.std([l['retorno_liquido'] for l in linhas],ddof=1)) if n>1 else None,seeds_lucrativas=sum(l['retorno_liquido']>0 for l in linhas),retornos_individuais={k.split('/')[-1]:res[k]['retorno_liquido'] for k in chaves})
    return r


def bootstrap(a,b,cfg):
    d=np.asarray(a,float)-np.asarray(b,float);n=len(d);tam=cfg['dias'];rng=np.random.default_rng(cfg['seed'])
    inicios=rng.integers(0,n,size=(cfg['replicas'],math.ceil(n/tam)));idx=((inicios[:,:,None]+np.arange(tam))%n).reshape(cfg['replicas'],-1)[:,:n]
    medias=d[idx].mean(axis=1)
    return {'diferenca_media_log_diaria':float(d.mean()),'ic95_log_diario':np.quantile(medias,[.025,.975]).tolist(),'dias':n,'bloco_dias':tam,'replicas':cfg['replicas'],'natureza':'Condicional aos checkpoints; retrospectivo; não corrige seleção histórica ou iguala exposição.'}


def publicar(p,congelado,res):
    c=congelado['contrato']['configuracao'];ss=c['seeds'];grupos={'mamba16_seis':[f'estado16_{s}' for s in ss],'mamba16_tres':[f'estado16_{s}' for s in ss[:3]],'lstm_tres':[f'lstm_{s}' for s in ss[:3]],'cryptomamba_seis':[f'cryptomamba_{s}' for s in ss],'cryptomamba_tres':[f'cryptomamba_{s}' for s in ss[:3]],'naive':['naive'],'arima':['arima']}
    medias={}
    for b in c['partes']:
        medias[b]={}
        for custo in c['custos']:
            medias[b][custo]={}
            politicas=c['politicas']+(['smart_constante'] if b=='teste' else [])
            for pol in politicas:medias[b][custo][pol]={nome:resumo([f'{b}/{custo}/{pol}/{k}' for k in ks],res) for nome,ks in grupos.items()}
            medias[b][custo]['benchmarks']={pol:resumo([f'{b}/{custo}/{pol}/benchmark'],res) for pol in ('caixa','comprar_manter')}
    diarios={}
    for k in res:diarios[k]=pd.read_parquet(p/'resultados'/k/'diarios.parquet')
    principal=np.mean([diarios[f'teste/base/smart/estado16_{s}'].retorno_log.to_numpy() for s in ss],axis=0)
    constante=np.mean([diarios[f'teste/base/smart_constante/estado16_{s}'].retorno_log.to_numpy() for s in ss],axis=0)
    bh=diarios['teste/base/comprar_manter/benchmark'].retorno_log.to_numpy()
    contrastes={'smart_mamba16_menos_vies_validacao':bootstrap(principal,constante,c['bootstrap']),'smart_mamba16_menos_comprar_manter':bootstrap(principal,bh,c['bootstrap']),'smart_mamba16_menos_caixa':bootstrap(principal,np.zeros_like(principal),c['bootstrap'])}
    r={'utc':agora(),'execucao':congelado['id'],'novos_treinamentos':0,'simulacoes':len(res),'medias':medias,'por_simulacao':res,'contrastes':contrastes,'calibracao_constantes':congelado['contrato']['medias_validacao_para_controle'],'periodos':{b:{k:res[f'{b}/base/comprar_manter/benchmark'][k] for k in ('inicio_utc','fim_utc','dias_decisao')} for b in c['partes']},'limites':['Custos/filtros/fills são cenários, não execução real certificada.','2024 seleção de checkpoints;2025 retrospectivo; não walk-forward/holdout novo.','Políticas fixadas antes desta simulação, após conhecer outros resultados de2025.','Curvas/métricas médias individuais, não ensemble ou carteira negociada.','Smart2% não é stop-loss ou faixa probabilística.','Controles constantes de validação apenas no teste; efeitos não igualam exposição.']}
    salvar_json(p/'resultados/comparacao.json',r)
    figs=figuras(p,r,grupos)
    salvar_json(p/'resultados/figuras.json',{'arquivos':figs,'resultado_sha256':sha256(p/'resultados/comparacao.json')})
    escrever(p,r,figs);return 'docs/resultados_backtest_carteira.md'


def figuras(p,r,grupos):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axs=plt.subplots(2,2,figsize=(14,9));cores={'mamba16_seis':'#28658C','cryptomamba_seis':'#198475','lstm_tres':'#AD7B30'}
    for ax,b,titulo in [(axs[0,0],'validacao','2024: desenvolvimento, com seleção de checkpoint'),(axs[0,1],'teste','2025: comparação retrospectiva')]:
        for nome,label in [('mamba16_seis','Mamba16 · 6 seeds'),('cryptomamba_seis','CryptoMamba adaptado · 6'),('lstm_tres','LSTM · 3')]:
            ds=[pd.read_parquet(p/f'resultados/{b}/base/smart/{k}/diarios.parquet') for k in grupos[nome]];times=pd.to_datetime(ds[0].origem_utc)+pd.Timedelta(days=1)
            ax.plot(times,np.mean([d.capital_fim.to_numpy() for d in ds],axis=0),label=label,color=cores[nome],linewidth=1.6)
        d=pd.read_parquet(p/f'resultados/{b}/base/comprar_manter/benchmark/diarios.parquet');ax.plot(pd.to_datetime(d.origem_utc)+pd.Timedelta(days=1),d.capital_fim,color='#444',linestyle='--',label='Comprar/manter')
        ax.axhline(10000,color='#888',linewidth=.9,label='Caixa');ax.set_title(titulo,loc='left',pad=12);ax.set_ylabel('Capital (USDT)');ax.legend(frameon=False,fontsize=8);ax.tick_params(axis='x',labelrotation=20)
    ax=axs[1,0];nomes=['diaria24','vanilla','smart'];labels=['Saída diária24h','Vanilla1%','Smart2%'];x=np.arange(3)
    for j,(perfil,cor) in enumerate([('ideal','#AAB8C2'),('base','#28658C'),('agravado','#BC7F36')]):
        vs=[100*r['medias']['teste'][perfil][n]['mamba16_seis']['retorno_liquido'] for n in nomes];ax.bar(x+(j-1)*.25,vs,.23,color=cor,label=perfil)
    ax.axhline(0,color='#555',linewidth=.8);ax.set_xticks(x,labels);ax.set_title('Mamba16: retorno médio por regra e custos',loc='left',pad=12);ax.set_ylabel('Retorno (%)');ax.legend(frameon=False,fontsize=8)
    ax=axs[1,1];ss=[17,42,2026,7,123,31415];x=np.arange(6)
    for j,(pol,label,cor) in enumerate([('smart','Previsões variáveis','#28658C'),('smart_constante','Viés fixado em2024','#AD7B30')]):
        vals=[100*r['por_simulacao'][f'teste/base/{pol}/estado16_{s}']['retorno_liquido'] for s in ss];ax.bar(x+(j-.5)*.36,vals,.34,label=label,color=cor)
    ax.axhline(0,color='#555',linewidth=.8);ax.set_xticks(x,[str(s) for s in ss]);ax.set_title('Smart: sinal variável versus previsão constante',loc='left',pad=12);ax.set_ylabel('Retorno líquido (%)');ax.legend(frameon=False,fontsize=8)
    for ax in axs.flat:ax.grid(axis='y',color='#E0E6EA');ax.set_axisbelow(True)
    fig.suptitle('Manter posição melhora o aproveitamento das previsões?',x=.065,y=.98,ha='left',fontsize=17,fontweight='bold')
    fig.text(.065,.025,'Spot · decisões00UTC / execução00:01 · carteiras individuais médias · histórico conhecido · sem garantia de lucro futuro',fontsize=9,color='#555')
    fig.subplots_adjust(left=.08,right=.98,bottom=.12,top=.89,hspace=.42,wspace=.24)
    pasta=RAIZ/f'docs/figuras/backtest_carteira_{r["execucao"]}';pasta.mkdir(parents=True)
    arquivos={}
    for ext in ('png','svg'):
        dest=pasta/f'carteiras.{ext}';fig.savefig(dest,dpi=170,bbox_inches='tight',facecolor='white');arquivos[dest.relative_to(RAIZ).as_posix()]=sha256(dest)
    plt.close(fig);return arquivos


def escrever(p,r,figs):
    m=r['medias'];s=m['teste']['base']['smart']['mamba16_seis'];mu=m['teste']['base']['smart_constante']['mamba16_seis'];ag=m['teste']['agravado']['smart']['mamba16_seis']
    def pct(x):return f'{100*x:+.2f}%'.replace('.',',')
    def n(x):return f'{x:.2f}'.replace('.',',')
    linhas=['# Backtest de carteiras Spot com previsões já treinadas','',f'Execução `{r["execucao"]}`.369simulações, zero novos treinamentos,17séries de previsão preservadas. [Protocolo](protocolo_backtest_carteira.md), [decisão](adr/0015-backtest-carteira.md), [estado/recibos](../registros/backtest_carteira/estado.json).',
        '', '## Resultado principal e interpretação','',f'Smart2% no Mamba16 terminou o teste com retorno líquido médio de **{pct(s["retorno_liquido"])}**, drawdown médio por minuto-close de {pct(s["drawdown_minuto_close"])}, exposição média de {n(100*s["exposicao_media"])}% e {n(s["ordens_executadas"])} ordens. {s["seeds_lucrativas"]}/6seeds terminaram com lucro. Com custos agravados: {pct(ag["retorno_liquido"])}.',
        '', 'Houve lucro médio neste cenário histórico.' if s['retorno_liquido']>0 else 'Este cenário não produziu lucro médio. Uma regra mais cuidadosa não cria sinal preditivo automaticamente.',
        '',f'O controle Smart com previsão constante calibrada em2024 retornou {pct(mu["retorno_liquido"])}. Comparar com esse controle ajuda a investigar se a variação das previsões acrescentou algo ao viés médio. As exposições diferem: não é isolamento causal perfeito. Comprar/manter e caixa completam a comparação.',
        '', '## Como a estratégia usa o modelo','', 'A previsão continua sendo do retorno em24h. Smart transforma a alta prevista numa fração do caixa a comprar, e a queda numa fração do BTC a vender. Repete a decisão no próximo dia, mantendo o restante da posição. Uma previsão positiva pequena repetida pode acumular BTC até quase investir todo o caixa. Isso é diferente de manter uma pequena porcentagem fixa investida.',
        '', 'Vanilla1% compra/vende tudo apenas quando a variação prevista ultrapassa1%; caso contrário mantém a carteira. O controle diária24 vende a cada dia e decide se recompra. Nenhuma dessas regras foi ajustada para obter lucro em2025. Os2% da Smart são parâmetro de alocação, não stop-loss, garantia de risco ou intervalo calibrado.',
        '', 'O código público do CryptoMamba utiliza o fechamento anterior como execução e não debita custos explicitamente. Aqui há atraso de1min, preços de minutos Binance, comissão,slippage,filtros e risco até o saldo terminal. É adaptação da política, não reprodução dos lucros publicados. Short exige dados de financiamento/margem que não fazem parte deste estudo Spot.',
        '', '## Calendário e custos','']
    for b,d in r['periodos'].items():linhas.append(f'- {b}: {d["inicio_utc"]} → {d["fim_utc"]}; {d["dias_decisao"]} decisões diárias, mesmas origens em todos os modelos.')
    linhas+=['','Base: comissão0,10% e slippage0,05% por lado; agravado0,20%/0,10%; ideal0/0. Quantidades arredondadas para baixo em0,00001BTC e mínimo5USDT assumido. Filtros e taxas históricas reais da conta não foram certificados. Comissões de compra debitadas no BTC recebido e de venda noUSDT recebido. Resíduo sem tamanho de ordem permanece marcado e é mostrado nos arquivos de cada simulação.',
        '', '## Médias por modelo, regra e período','', 'Seis seeds no Mamba16/CryptoMamba; três na LSTM. Para comparação pareada com LSTM usar os grupos de três da tabela seguinte. Médias individuais, não carteira formada por ensemble.','', '| Período | Regra | Modelo | N | Retorno base | Drawdown médio | Exposição média | Ordens médias |','|---|---|---|---:|---:|---:|---:|---:|']
    for b in ('validacao','teste'):
        for pol in ('diaria24','vanilla','smart'):
            for nome in ('mamba16_seis','lstm_tres','cryptomamba_seis','naive','arima'):
                d=m[b]['base'][pol][nome];linhas.append(f'| {b} | {pol} | {nome} | {d["n_seeds"]} | {pct(d["retorno_liquido"])} | {pct(d["drawdown_minuto_close"])} | {n(100*d["exposicao_media"])}% | {n(d["ordens_executadas"])} |')
        for nome in ('caixa','comprar_manter'):
            d=m[b]['base']['benchmarks'][nome];linhas.append(f'| {b} | benchmark | {nome} | 1 | {pct(d["retorno_liquido"])} | {pct(d["drawdown_minuto_close"])} | {n(100*d["exposicao_media"])}% | {n(d["ordens_executadas"])} |')
    linhas+=['','## Smart no teste: comparação pareada nas três seeds comuns','','| Modelo | Seeds | Retorno base | Desvio entre seeds |','|---|---:|---:|---:|']
    for nome in ('mamba16_tres','lstm_tres','cryptomamba_tres'):
        d=m['teste']['base']['smart'][nome];linhas.append(f'| {nome} | 3 | {pct(d["retorno_liquido"])} | {pct(d["desvio_retorno_seeds"])} |')
    linhas+=['','## Sensibilidade a custos no teste','','| Regra | Modelo | Ideal | Base | Agravado |','|---|---|---:|---:|---:|']
    for pol in ('diaria24','vanilla','smart','smart_constante'):
        for nome in ('mamba16_seis','lstm_tres','cryptomamba_seis'):
            vals=[pct(m['teste'][co][pol][nome]['retorno_liquido']) for co in ('ideal','base','agravado')];linhas.append(f'| {pol} | {nome} | '+ ' | '.join(vals)+' |')
    linhas+=['','## Cada seed do Mamba16 no teste','','| Seed | Diária24 | Vanilla | Smart | Smart com viés fixo |','|---|---:|---:|---:|---:|']
    for seed in (17,42,2026,7,123,31415):linhas.append(f'| {seed} | '+' | '.join(pct(r['por_simulacao'][f'teste/base/{pol}/estado16_{seed}']['retorno_liquido']) for pol in ('diaria24','vanilla','smart','smart_constante'))+' |')
    linhas+=['','## Incerteza temporal do contraste principal','', 'Média entre seeds de retornos log diários; bootstrap circular14dias,2000réplicas. O intervalo é condicional aos checkpoints e ao histórico. Não corrige a escolha retrospectiva das políticas ou toda investigação anterior.','', '| Contraste Smart/Mamba16 | Diferença log diária | IC95% |','|---|---:|---|']
    for nome,d in r['contrastes'].items():
        a,b=d['ic95_log_diario'];linhas.append(f'| {nome} | {d["diferenca_media_log_diaria"]:.8g} | [{a:.8g};{b:.8g}] |')
    linhas+=['', 'Intervalo que inclui zero é inconclusivo quanto ao efeito. Um saldo positivo isolado não demonstra vantagem futura. Os controles de viés usam apenas previsões de2024 e nunca média futura de2025.', '',f'![Curvas e comparações](figuras/backtest_carteira_{r["execucao"]}/carteiras.png)',
        '', '## Auditoria e limites','', 'Todas as369simulações têm ordens,recusas,saldos,curva horária,retornos diários e verificador independente. Caixa,BTC,comissão,slippage,quantidades e drawdown foram reconstituídos do livro de lançamentos. O drawdown considera closes de todos os minutos, saldos de execução e liquidação final; a curva ilustrada é amostrada. Não há stop-loss ou garantia de execução real. Dados/previsões/modelos anteriores não foram alterados.',
        '', '2024participou da seleção dos checkpoints.2025já foi consultado antes desta decisão. Trata-se de backtest retrospectivo, sem novo holdout ou walk-forward. A receita do modelo, parâmetros das políticas e todas as seeds foram preservados; nenhum vencedor foi escolhido automaticamente e não houve busca até lucrar. Resultados devem ser confirmados por outros períodos e condições antes de qualquer alegação operacional.',
        '', '[CryptoMamba](https://arxiv.org/html/2501.01010v2), [código público das políticas](https://github.com/MShahabSepehri/CryptoMamba/blob/fef42727861a9c3a32241283ab981ef21a49e291/utils/trade.py), [comissões Binance](https://developers.binance.com/en/docs/products/spot/faqs/commission_faq).',
        '', f'[Resultados estruturados](../{(p/"resultados/comparacao.json").relative_to(RAIZ).as_posix()}) e [estado verificável](../registros/backtest_carteira/estado.json).']
    dest=RAIZ/'docs/resultados_backtest_carteira.md'
    if dest.exists():raise FileExistsError('Relatório existente; preservar.')
    dest.write_text('\n'.join(linhas)+'\n',encoding='utf-8')
