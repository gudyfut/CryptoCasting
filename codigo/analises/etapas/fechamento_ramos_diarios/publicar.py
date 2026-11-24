"""Tabelas e figuras do fechamento; somente a partir de artefatos conferidos."""
import csv
import io
import json
import math
import zipfile
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,sha256,agora

REG=RAIZ/'registros/fechamento_ramos_diarios'
CORES={'A':'#7B3294','B':'#E69F00','L':'#0072B2','L0':'#009E73','naive':'#666666','linear':'#BB5566'}


def gravar_csv(p,linhas):
    with p.open('w',encoding='utf-8-sig',newline='') as ar:
        w=csv.DictWriter(ar,fieldnames=list(linhas[0]));w.writeheader();w.writerows(linhas)


def semestres(dias):
    saida=[]
    for semestre in (1,2):
        lista=[(i,d) for i,d in enumerate(dias) if ((pd.to_datetime(d['origem_ms'],unit='ms',utc=True).month-1)//6+1)==semestre]
        if lista:saida.append((semestre,lista))
    return saida


def publicar():
    conf=ler_json(REG/'conferencia_posterior.json');assert conf['situacao']=='aprovado'
    ptr=ler_json(REG/'execucao.json');assert conf['execucao']==ptr
    p=RAIZ/ptr['pasta'];f=ler_json(p/'congelamento.json')
    destino=REG/'publicacao_final';destino.mkdir(exist_ok=False)
    linhas=[];por_seed=[];financeiro=[];dados={};concentracao=[];subperiodos=[];fontes={};ramos=[];coeficientes=[];contribuicoes=[];decomposicoes_ensemble=[]
    for simbolo in f['configuracao']['moedas']:
        base=p/simbolo;pub=base/'publicacao';cfg=ler_json(base/'configuracao.json')
        prev=ler_json(pub/'previsao.json');ops=ler_json(pub/'operacoes.json');diag=ler_json(pub/'diagnostico_afim.json')
        dados[simbolo]=dict(previsao=prev,operacoes=ops,diagnostico=diag,configuracao=cfg,base=base)
        for nome in ('previsao.json','operacoes.json','diagnostico_afim.json','carteiras.zip'):
            fontes[(pub/nome).relative_to(RAIZ).as_posix()]=sha256(pub/nome)
        for nome,m in diag['modelos'].items():
            variante,seed=nome.split('_')
            for fase,z in m['fases'].items():
                vetores=dict(np.load(pub/'diagnostico'/f'{fase}_{nome}.npz'))
                ultimo=dict(np.load(base/'dados'/f'{fase}.npz'))['ultimo_close']
                def sinal(previsao):
                    preco=ultimo*(1+previsao);retorno=preco/ultimo-1
                    return np.where((preco>0)&(abs(retorno)>cfg['operacoes']['filtro_retorno_absoluto']),np.sign(retorno),0)
                ramos.append(dict(simbolo=simbolo,variante=variante,seed=int(seed),fase=fase,
                    exemplos=z['exemplos'],max_delta=z['max_diferenca_sem_ramos'],rms_delta=z['rms_diferenca_sem_ramos'],
                    mse_completo=z['mse_completo'],mse_sem_ramos=z['mse_sem_ramos'],
                    decisoes_alteradas_sem_ramos=int(np.sum(sinal(vetores['previsao'])!=sinal(vetores['previsao_sem_ramos']))),
                    efeito_mse_retirada=z['mse_sem_ramos']-z['mse_completo']))
                for canal,a in dict(z['contribuicoes'],OHLC_conjunto=z['contribuicao_ohlc_conjunta']).items():
                    contribuicoes.append(dict(simbolo=simbolo,variante=variante,seed=int(seed),fase=fase,canal=canal,**a))
            for i,canal in enumerate(cfg['canais']):
                for dia,valor in enumerate(m['coeficientes_canal_dia'][i]):
                    coeficientes.append(dict(simbolo=simbolo,variante=variante,seed=int(seed),canal=canal,
                        defasagem_dias=13-dia,coeficiente=valor,intercepto=m['intercepto']))
        for fase in ('validacao','teste'):
            for v in cfg['variantes']:
                sondas=[dict(np.load(pub/'diagnostico'/f'{fase}_{v}_{s}.npz')) for s in cfg['seeds']]
                canais=np.mean([z['contribuicoes_canais'] for z in sondas],axis=0)
                previsto=dict(np.load(pub/'previsoes'/f'{fase}_{v}_ensemble.npz'))['previsoes_retorno']
                coef_medio=np.mean([np.asarray(diag['modelos'][f'{v}_{s}']['coeficientes_canal_dia']) for s in cfg['seeds']],axis=0)
                grupos=dict(timestamp=canais[:,0],ohlc_conjunto=canais[:,1:5].sum(axis=1),volume=canais[:,5],
                    ramos=np.mean([z['previsao']-z['previsao_sem_ramos'] for z in sondas],axis=0))
                decomposicoes_ensemble.append(dict(simbolo=simbolo,fase=fase,variante=v,
                    media_previsao=float(previsto.mean()),desvio_previsao=float(previsto.std()),
                    rank_coeficientes_residuais=int(np.linalg.matrix_rank(coef_medio)),
                    dias_sinal_compra=int(np.sum(previsto>cfg['operacoes']['filtro_retorno_absoluto'])),
                    dias_sinal_venda=int(np.sum((previsto<-cfg['operacoes']['filtro_retorno_absoluto'])&(previsto>-1))),
                    **{f'desvio_{k}':float(z.std()) for k,z in grupos.items()},
                    limite='Desvios das contribuicoes algebricas medias; nao sao parcelas independentes da variancia nem importancia causal.'))
                for forma in ('media_seeds','ensemble'):
                    m={k:z['media'] for k,z in prev['medias_seeds'][fase][v].items()} if forma=='media_seeds' else prev['ensemble'][fase][v]
                    o={k:z['media'] for k,z in ops['medias_seeds'][fase]['1'][v].items()} if forma=='media_seeds' and not ops['medias_seeds'][fase]['1'][v].get('incompleto') else ops['ensemble'][fase]['1'][v] if forma=='ensemble' else None
                    linhas.append(dict(simbolo=simbolo,fase=fase,variante=v,forma=forma,
                        mse=m['mse_retorno'],rmse_pp=100*m['rmse_retorno'],mae_pp=100*m['mae_retorno'],
                        habilidade_mse_pct=100*m['habilidade_mse_retorno_naive'],
                        acerto_balanceado_pct=100*m['acerto_balanceado'] if m['acerto_balanceado'] is not None else None,
                        retorno_liquido_pct=100*o['retorno_liquido'] if o else None,
                        drawdown_pct=100*o['drawdown_maximo'] if o else None,
                        capital_final=o['capital_final'] if o else None,dias_posicionado=o['dias_posicionado'] if o else None))
                for s in cfg['seeds']:
                    m=prev['individuais_e_referencias'][fase][f'{v}_{s}']
                    o=next((q['metricas'] for q in ops['carteiras'] if q['fase']==fase and q['unidade']==f'{v}_{s}' and q['custo']==1),None)
                    por_seed.append(dict(simbolo=simbolo,fase=fase,variante=v,seed=s,mse=m['mse_retorno'],
                        retorno_liquido_pct=100*o['retorno_liquido'] if o else None,
                        drawdown_pct=100*o['drawdown_maximo'] if o else None,
                        rms_contribuicao_ramos=diag['modelos'][f'{v}_{s}']['fases'][fase]['rms_diferenca_sem_ramos']))
            for ref in ('naive','linear'):
                m=prev['individuais_e_referencias'][fase][ref]
                o=next((q['metricas'] for q in ops['carteiras'] if q['fase']==fase and q['unidade']==ref and q['custo']==1),None)
                linhas.append(dict(simbolo=simbolo,fase=fase,variante=ref,forma='referencia',mse=m['mse_retorno'],
                    rmse_pp=100*m['rmse_retorno'],mae_pp=100*m['mae_retorno'],habilidade_mse_pct=100*m['habilidade_mse_retorno_naive'],
                    acerto_balanceado_pct=100*m['acerto_balanceado'] if m['acerto_balanceado'] is not None else None,
                    retorno_liquido_pct=100*o['retorno_liquido'] if o else None,drawdown_pct=100*o['drawdown_maximo'] if o else None,
                    capital_final=o['capital_final'] if o else None,dias_posicionado=o['dias_posicionado'] if o else None))
        for o in ops['carteiras']:
            financeiro.append(dict(simbolo=simbolo,fase=o['fase'],unidade=o['unidade'],custo=o['custo'],**o['metricas']))
        # Atribuição de PnL aos dias/episódios já executados; não cria outra política.
        with zipfile.ZipFile(pub/'carteiras.zip') as z:
            for v in cfg['variantes']:
                for fase in ('validacao','teste'):
                    nome=f'{fase}/{v}_ensemble/custo_1/resultado.json'
                    if nome not in z.namelist():continue
                    r=json.loads(z.read(nome));episodios=[];atual=[];lado_anterior=0
                    curva=dict(np.load(io.BytesIO(z.read(nome.replace('resultado.json','curva.npz')))))
                    eq=curva['saldos_diarios']
                    assert len(eq)==len(r['dias'])+1
                    for semestre,pares in semestres(r['dias']):
                        i0,i1=pares[0][0],pares[-1][0]+1
                        a,b=pares[0][1]['entrada_ms'],pares[-1][1]['fim_ms']
                        segmento=eq[i0:i1+1];dias=[d for _,d in pares]
                        ordens=[o for o in r['ordens'] if a<=o['tempo_ms']<b or (i1==len(r['dias']) and o['tempo_ms']==b)]
                        subperiodos.append(dict(simbolo=simbolo,fase=fase,variante=v,semestre=semestre,
                            primeiro_dia_ms=dias[0]['origem_ms'],ultimo_dia_ms=dias[-1]['origem_ms'],dias=len(dias),
                            retorno_segmento=float(segmento[-1]/segmento[0]-1),
                            drawdown_fechamentos=float(np.max(1-segmento/np.maximum.accumulate(segmento))),
                            dias_compra=sum(d['quantidade']>0 for d in dias),dias_venda=sum(d['quantidade']<0 for d in dias),
                            pnl_movimento=math.fsum(d['pnl_movimento_contrato'] for d in dias),
                            funding=math.fsum(d['funding'] for d in dias),
                            comissoes=math.fsum(o['comissao'] for o in ordens),
                            slippage_ticks=math.fsum(o['custo_slippage_ticks'] for o in ordens),
                            limite='Recorte da mesma carteira, sem reinício ou realocação; drawdown somente dos fechamentos diários, não intraminuto.'))
                    for dia in r['dias']:
                        lado=int(np.sign(dia['quantidade']))
                        if lado!=lado_anterior and atual:
                            episodios.append(atual);atual=[]
                        if lado:atual.append(dia)
                        lado_anterior=lado
                    if atual:episodios.append(atual)
                    # Ganho por movimento do contrato, sem atribuir taxas/funding a um lado artificialmente.
                    valores=[math.fsum(d['pnl_movimento_contrato'] for d in e) for e in episodios]
                    positivos=sorted([x for x in valores if x>0],reverse=True)
                    soma=math.fsum(positivos)
                    concentracao.append(dict(simbolo=simbolo,fase=fase,variante=v,episodios=len(episodios),
                        episodios_positivos=len(positivos),pnl_por_episodio=valores,
                        fracao_ganhos_positivos_maior=positivos[0]/soma if soma else None,
                        fracao_ganhos_positivos_top3=math.fsum(positivos[:3])/soma if soma else None,
                        dias_compra=sum(d['quantidade']>0 for d in r['dias']),dias_venda=sum(d['quantidade']<0 for d in r['dias']),
                        limite='Episódios por lado persistente; PnL de movimento, não retorno líquido de operações independentes.'))
    gravar_csv(destino/'comparacao.csv',linhas);gravar_csv(destino/'seeds.csv',por_seed)
    gravar_csv(destino/'carteiras.csv',financeiro)
    gravar_csv(destino/'semestres.csv',subperiodos)
    gravar_csv(destino/'contribuicao_ramos.csv',ramos)
    gravar_csv(destino/'coeficientes_afins.csv',coeficientes)
    gravar_csv(destino/'contribuicoes_canais.csv',contribuicoes)
    gravar_csv(destino/'decomposicao_ensembles.csv',decomposicoes_ensemble)
    tempos=[];gradientes=[]
    for j in ler_json(p/'ajustes.json'):
        q=p/j['simbolo']/'ajustes'/j['id'];s=ler_json(q/'selecao.json');co=ler_json(q/'conclusao.json')
        tempos.append(dict(simbolo=j['simbolo'],ajuste=j['id'],controle=j['controle'],epocas=200,
            parametros=ler_json(q/'grupos_penalizacao.json')['elementos_totais'],
            epoca_selecionada=s['epoca'],segundos=co['segundos']))
        for ar in sorted((q/'observacoes').glob('*.json')):
            ob=ler_json(ar);gr=ob.get('gradiente_ultimo_lote_antes_atualizacao')
            if gr is None:continue
            fontes[ar.relative_to(RAIZ).as_posix()]=sha256(ar)
            for grupo,valores in gr.items():
                gradientes.append(dict(simbolo=j['simbolo'],ajuste=j['id'],controle=j['controle'],epoca=ob['epoca'],
                    grupo=grupo,**valores,limite='Ultimo lote, antes da atualizacao; nao mede o passo efetivo do Adam ou todos os lotes.'))
    gravar_csv(destino/'eficiencia.csv',tempos)
    gravar_csv(destino/'gradientes_observados.csv',gradientes)
    salvar_json(destino/'atribuicao_operacional.json',dict(concentracao=concentracao,semestres=subperiodos,
        limite='Análise descritiva posterior; não seleciona filtro, ativos, épocas ou política.'))
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,
                         'axes.titleweight':'bold','figure.dpi':130,'savefig.dpi':180,'axes.grid':True,'grid.alpha':.18})
    def figura(fig,nome):
        fig.savefig(destino/f'{nome}.png',bbox_inches='tight');fig.savefig(destino/f'{nome}.pdf',bbox_inches='tight');plt.close(fig)
    btc=dados['BTCUSDT'];pv=btc['previsao'];fig,axs=plt.subplots(1,2,figsize=(12,4.6),layout='constrained')
    for ax,forma,titulo in zip(axs,('medias_individuais','ensemble'),('Média das três redes','Ensemble das três redes')):
        variantes=list(btc['configuracao']['variantes']);base=pv['individuais_e_referencias']['teste']['naive']['mse_retorno']
        for i,v in enumerate(variantes):
            x=pv['contrastes_mse']['teste'][forma][f'{v}_menos_naive']['14']
            valor=-100*x['media']/base;lo,hi=[-100*q/base for q in reversed(x['ic95'])]
            ax.bar(i,valor,color=CORES[v],alpha=.85);ax.plot([i,i],[lo,hi],color='black',lw=1.5)
            ax.scatter([i,i],[lo,hi],marker='_',color='black')
        ax.axhline(0,color='black',lw=.8);ax.set_xticks(range(len(variantes)),variantes)
        ax.set_title(titulo);ax.set_ylabel('Redução de MSE contra Naive (%)\nMaior é melhor')
    fig.suptitle('BTC · fatorial ramos × penalização · retrospectiva 2025')
    fig.supxlabel('A: Mamba/L2 · B: Mamba/sem L2 · L: linear/L2 · L0: linear/sem L2\nIC95% da diferença de MSE: blocos de 14 dias; escala relativa usa MSE Naive observado fixo',fontsize=9)
    figura(fig,'fatorial_btc')
    fig,axs=plt.subplots(1,2,figsize=(12,5.2),layout='constrained')
    moedas=list(dados)
    for ax,forma,titulo in zip(axs,('medias_individuais','ensemble'),('Média das três redes','Ensemble')):
        for i,moeda in enumerate(moedas):
            pv=dados[moeda]['previsao'];nome='A_menos_L' if moeda=='BTCUSDT' else 'L_menos_A'
            q=pv['contrastes_mse']['teste'][forma][nome]['14'];sinal=1 if moeda=='BTCUSDT' else -1
            base=pv['medias_seeds']['teste']['A']['mse_retorno']['media'] if forma=='medias_individuais' else pv['ensemble']['teste']['A']['mse_retorno']
            vals=sorted([sinal*100*x/base for x in q['ic95']]);v=sinal*100*q['media']/base
            ax.plot(vals,[i,i],color=CORES['L'],lw=2);ax.scatter(v,i,color=CORES['L'],s=45)
        ax.axvline(0,color='black',lw=.8);ax.set_yticks(range(4),[x.removesuffix('USDT') for x in moedas]);ax.invert_yaxis()
        ax.set_title(titulo);ax.set_xlabel('Redução de MSE ao remover os ramos (%)\nÀ direita: menor erro em L')
    fig.suptitle('A versus L · mesma penalização 0,001 · retrospectiva 2025')
    fig.supxlabel('IC95% da diferença de MSE, blocos de 14 dias; escala relativa usa MSE de A observado fixo\nTrês seeds; ativos correlacionados; não é teste formal de equivalência',fontsize=9)
    figura(fig,'comparacao_ativos')
    fig,axs=plt.subplots(2,2,figsize=(12,7.6),layout='constrained')
    for ax,simbolo in zip(axs.ravel(),moedas):
        base=dados[simbolo]['base'];ops=dados[simbolo]['operacoes']
        with zipfile.ZipFile(base/'publicacao/carteiras.zip') as z:
            for v in dados[simbolo]['configuracao']['variantes']:
                nome=f'teste/{v}_ensemble/custo_1/curva.npz'
                if nome not in z.namelist():continue
                cv=dict(np.load(io.BytesIO(z.read(nome))));eq=cv['saldos_diarios']
                ledger=json.loads(z.read(nome.replace('curva.npz','resultado.json')))
                assert len(eq)==len(ledger['dias'])+1
                # O simulador executa com latência de1min; usar timestamps reais do ledger.
                ts=pd.to_datetime([ledger['dias'][0]['entrada_ms'],*[d['fim_ms'] for d in ledger['dias']]],unit='ms',utc=True)
                ax.plot(ts,eq/10000,label=v,color=CORES[v],lw=1.5)
        ax.axhline(1,color=CORES['naive'],lw=.8,ls='--',label='Naive / caixa')
        ax.set_title(simbolo.removesuffix('USDT'));ax.set_ylabel('Patrimônio / capital inicial');ax.legend(ncol=3,fontsize=8)
        ax.tick_params(axis='x',rotation=20)
    fig.suptitle('Ensembles · futuros com continuidade · retrospectiva 2025')
    fig.supxlabel('Comissão 0,05% + slippage provisório 0,01% por lado; funding histórico; filtro ±0,2%; exposição alvo 95%',fontsize=9)
    figura(fig,'carteiras_ensemble')
    historico=ler_json(REG/'diagnostico_previo.json');fig,axs=plt.subplots(1,2,figsize=(12,4.6),layout='constrained')
    for seed,sondas in historico['trajetoria_padronizacao'].items():
        ep=[0 if s['checkpoint']=='inicial' else int(s['checkpoint'].split('_')[-1]) for s in sondas]
        delta=[s['max_delta_sem_ramos'] for s in sondas]
        axs[0].plot(ep,[max(x,1e-10) for x in delta],marker='o',label=f'Seed {seed}')
        axs[1].plot(ep,[s['norma_layernorm'] for s in sondas],marker='o',label=f'Seed {seed}')
    axs[0].set_ylabel('Maior alteração da previsão ao retirar ramos');axs[1].set_ylabel('Norma dos parâmetros LayerNorm')
    for ax in axs:ax.set_yscale('log');ax.set_xlabel('Época do checkpoint disponível');ax.legend(fontsize=8)
    fig.suptitle('Referência A em BTC · trajetória observada anteriormente')
    fig.supxlabel('Sondas de 32 janelas de treino; zero numérico desenhado em 10⁻¹⁰; linhas apenas ligam observações salvas',fontsize=9)
    figura(fig,'trajetoria_ramos')
    from matplotlib.patches import FancyBboxPatch
    fig,axs=plt.subplots(2,1,figsize=(12,6.3),layout='constrained',height_ratios=[1,1.3])
    for ax in axs:ax.set_xlim(0,12);ax.set_ylim(0,3);ax.axis('off')
    def caixa(ax,x,y,w,h,rotulo,cor):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.06',facecolor=cor,alpha=.15,edgecolor=cor))
        ax.text(x+w/2,y+h/2,rotulo,ha='center',va='center',fontsize=10)
    def seta(ax,a,b):ax.annotate('',xy=b,xytext=a,arrowprops=dict(arrowstyle='->',color='#333333',lw=1.4))
    ax=axs[0]
    caixas=[(.15,1.4,'Entrada\n6 canais × 14 dias'),(2.35,1.75,'4 blocos residuais\nLinear 14 → 16'),
            (4.95,1.75,'4 blocos residuais\nLinear 16 → 32'),(7.55,1.75,'4 blocos residuais\nLinear 32 → 1'),
            (10.05,1.6,'Combinar canais\nLinear 6 → 1')]
    for x,w,t in caixas:caixa(ax,x,1,w,1.1,t,CORES['A'])
    for (x,w,_),(x2,_,_) in zip(caixas,caixas[1:]):seta(ax,(x+w+.07,1.55),(x2-.07,1.55))
    ax.text(6,2.55,'Estrutura derivada do CryptoMamba · retorno simples diário',ha='center',weight='bold')
    ax.text(6,.35,'Mamba percorre os 6 canais; os 14 dias ocupam a dimensão dos atributos.',ha='center',fontsize=10)
    ax=axs[1];caixa(ax,.5,1.2,1,.65,'x','#444444');caixa(ax,3,1.2,1.6,.65,'LayerNorm',CORES['A'])
    caixa(ax,6,1.2,1.7,.65,'Mamba-1',CORES['A']);caixa(ax,9.3,1.2,.65,.65,'+',CORES['A']);caixa(ax,10.65,1.2,.95,.65,'saída','#444444')
    for a,b in [((1.55,1.525),(2.94,1.525)),((4.66,1.525),(5.94,1.525)),((7.76,1.525),(9.24,1.525)),((10.01,1.525),(10.59,1.525))]:seta(ax,a,b)
    ax.plot([2,2,9.625],[1.525,2.5,2.5],color='#333333',lw=1.4);seta(ax,(9.625,2.5),(9.625,1.92))
    ax.text(5.8,2.65,'Caminho direto: preserva a entrada',ha='center',fontsize=10)
    ax.text(6,.6,'L e L0 removem LayerNorm + Mamba antes de treinar; cada bloco passa a devolver x.',ha='center',fontsize=10)
    ax.text(6,.15,'A/B: 136.952 parâmetros · L/L0: 824 parâmetros · A/L: penalização 0,001 · B/L0: penalização zero',ha='center',fontsize=9)
    fig.suptitle('O que a ablação remove e o que permanece')
    figura(fig,'estrutura_ablacao')
    salvar_json(destino/'resumo.json',dict(utc=agora(),execucao=ptr,comparacao=linhas,seeds=por_seed,
        fontes=fontes,conferencia_sha256=sha256(REG/'conferencia_posterior.json'),
        limite='2024 seleção;2025 retrospectivo;2026 excluído. ICs exploratórios. Média de carteiras não é carteira do ensemble.'))
    salvar_json(destino/'manifesto.json',dict(utc=agora(),fonte_sha256=sha256(__file__),
        arquivos={q.name:sha256(q) for q in destino.iterdir() if q.is_file()},inspecao_visual='pendente'))
    print('PUBLICADO_PENDENTE_INSPECAO',destino,flush=True)


if __name__=='__main__':publicar()
