"""Conferência posterior independente e apresentação; não altera a execução."""
import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256, conferir_arquivos

REG=RAIZ/'registros/ablacao_linear_2026'


def reamostrar(dados,bloco,cfg,pares):
    """Implementação independente da conferência dos ICs, em matriz."""
    a=np.atleast_2d(dados);k,n=a.shape
    rng=np.random.default_rng(cfg['seed']);total=cfg['replicas']
    amostras=np.empty((total,n),dtype=np.int64);sementes=np.empty((total,k),dtype=np.int64)
    for i in range(total):
        inicios=rng.integers(0,n-bloco+1,(n+bloco-1)//bloco)
        amostras[i]=np.concatenate([np.arange(t,t+bloco) for t in inicios])[:n]
        sementes[i]=rng.integers(0,k,k) if pares else np.arange(k)
    valores=a[sementes[:,:,None],amostras[:,None,:]].mean(axis=(1,2))
    return float(a.mean()),np.quantile(valores,[.025,.975])


def conferir_ic(matrizes,refs,guardados,cfg,pares):
    contrastes={'L_menos_A':matrizes['L']-matrizes['A']}
    contrastes.update({f'{v}_menos_{r}':a-b for v,a in matrizes.items() for r,b in refs.items()})
    total=0
    for nome,a in contrastes.items():
        for bloco in cfg['blocos']:
            media,ic=reamostrar(a,bloco,cfg,pares);q=guardados[nome][str(bloco)]
            np.testing.assert_allclose(media,q['media'],atol=1e-15,rtol=1e-11)
            np.testing.assert_allclose(ic,q['ic95'],atol=1e-15,rtol=1e-11);total+=1
    return total


def executar():
    ptr=ler_json(REG/'execucao.json');p=RAIZ/ptr['pasta']
    assert not (REG/'conferencia_posterior.json').exists(), 'Não sobrescrever conferência.'
    assert ler_json(p/'fechamento.json')['situacao']=='concluido_controles_aprovados'
    assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    f=ler_json(p/'congelamento.json');c=f['configuracao']
    conferir_arquivos(RAIZ,f['fontes']);conferir_arquivos(RAIZ,f['pais'])
    assert sha256(p/'manifesto.json')==ler_json(p/'fechamento.json')['manifesto_sha256']
    conferir_arquivos(p,ler_json(p/'manifesto.json')['arquivos'])
    previsto=ler_json(p/'previsao.json');operacoes=ler_json(p/'operacoes.json')
    linhas=[];financeiras=[];curvas={};resumo={};intervalos=0;maxerro=0.;transicoes=0
    for moeda in c['moedas']:
        z=np.load(p/moeda/'entradas.npz',allow_pickle=False);y=z['alvo_retorno'];prev={}
        for nome,m in previsto[moeda]['metricas'].items():
            q=np.load(p/moeda/f'{nome}.npz',allow_pickle=False)
            np.testing.assert_array_equal(q['origens_ms'],z['origens_ms'])
            np.testing.assert_array_equal(q['alvo_retorno'],y)
            a=q['previsoes_retorno'];prev[nome]=a;erro=a-y
            metricas=dict(mse_retorno=float(np.dot(erro,erro)/len(y)),rmse_retorno=float(np.linalg.norm(erro)/np.sqrt(len(y))),
                mae_retorno=float(np.sum(abs(erro))/len(y)),vies_retorno=float(np.sum(erro)/len(y)),
                desvio_previsao=float(np.std(a)),habilidade_mse_retorno_naive=float(1-np.dot(erro,erro)/np.dot(y,y)))
            if np.any(a):
                metricas.update(acerto_sinal=float(np.mean(np.sign(a)==np.sign(y))),
                    acerto_balanceado=float((np.mean(a[y>0]>0)+np.mean(a[y<0]<0))/2))
            for k,v in metricas.items():
                maxerro=max(maxerro,abs(v-m[k]));np.testing.assert_allclose(v,m[k],atol=1e-14,rtol=1e-12)
            linhas.append(dict(moeda=moeda,unidade=nome,**m))
        for v in c['variantes']:
            media_preco=np.mean([np.load(p/moeda/f'{v}_{s}.npz')['previsoes'] for s in c['seeds']],axis=0)
            np.testing.assert_array_equal(prev[f'{v}_ensemble'],media_preco/z['ultimo_close']-1)
            medias={}
            for k,item in previsto[moeda]['medias_seeds'][v].items():
                valores=[previsto[moeda]['metricas'][f'{v}_{s}'][k] for s in c['seeds']]
                if all(isinstance(a,(int,float)) for a in valores):
                    np.testing.assert_allclose(item['media'],np.mean(valores),rtol=1e-12,atol=1e-14)
                    np.testing.assert_allclose(item['desvio_seeds'],np.std(valores,ddof=1),rtol=1e-12,atol=1e-14)
                medias[k]=item['media']
            linhas.append(dict(moeda=moeda,unidade=f'{v}_media_seeds',**medias))
        refs={r:(prev[r]-y)**2 for r in ('naive','linear')}
        for conjunto,pares in (('medias_individuais',True),('ensemble',False)):
            matrizes={v:np.array([(prev[f'{v}_{s}']-y)**2 for s in c['seeds']]) if pares else (prev[f'{v}_ensemble']-y)**2 for v in c['variantes']}
            intervalos+=conferir_ic(matrizes,refs,previsto[moeda]['contrastes_mse'][conjunto],c['bootstrap'],pares)
        resumo[moeda]=dict(n=len(y),mse_naive=float(np.mean(y*y)),
            mse_ensemble={v:previsto[moeda]['metricas'][f'{v}_ensemble']['mse_retorno'] for v in c['variantes']},
            mse_media={v:previsto[moeda]['medias_seeds'][v]['mse_retorno']['media'] for v in c['variantes']},
            mse_ic_L_menos_A={s:previsto[moeda]['contrastes_mse'][s]['L_menos_A']['14'] for s in ('medias_individuais','ensemble')})
        print('PREVISOES_CONFERIDAS',moeda,flush=True)
    with zipfile.ZipFile(p/'carteiras.zip') as pacote:
        assert len(pacote.namelist())==264
        for l in operacoes['carteiras']:
            m=l['metricas'];r=json.loads(pacote.read(l['membro']+'/resultado.json'))
            cv=dict(np.load(io.BytesIO(pacote.read(l['membro']+'/curva.npz')),allow_pickle=False))
            saldo=cv['saldos_diarios'];assert len(saldo)==315 and (saldo>0).all()
            taxa=saldo[-1]/saldo[0]-1;np.testing.assert_allclose(taxa,m['retorno_liquido'],atol=1e-12)
            np.testing.assert_allclose(np.mean(np.diff(np.log(saldo))),m['crescimento_log_diario'],atol=1e-12)
            dias=r['dias'];ordens=r['ordens']
            comissao=sum(o['comissao'] for o in ordens);slip=sum(o['custo_slippage_ticks'] for o in ordens)
            funding=sum(d['funding'] for d in dias);pnl=sum(d['pnl_movimento_contrato'] for d in dias)
            np.testing.assert_allclose(saldo[0]+pnl+funding-comissao-slip,saldo[-1],atol=1e-7,rtol=1e-10)
            for k,v in dict(comissoes=comissao,custo_slippage_ticks=slip,funding=funding,pnl_movimento_contrato=pnl).items():
                np.testing.assert_allclose(m[k],v,atol=1e-7,rtol=1e-10)
            for i in range(1,len(dias)):
                if dias[i-1]['quantidade']*dias[i]['alvo_lotes']>0:
                    atuais=[o for o in ordens if o['tempo_ms']==dias[i]['entrada_ms']]
                    assert len(atuais)<=1, 'Mesmo lado deve negociar somente o delta.'
                    transicoes+=1
            np.testing.assert_allclose(np.max(cv['drawdown_acumulado']),m['drawdown_maximo'],atol=1e-10)
            curvas[(l['moeda'],l['unidade'],l['custo'])]=cv
            financeiras.append(dict(moeda=l['moeda'],unidade=l['unidade'],custo=l['custo'],**m))
    for moeda in c['moedas']:
        for custo in range(1,4):
            crescimentos={nome:np.diff(np.log(cv['saldos_diarios'])) for (s,nome,k),cv in curvas.items() if s==moeda and k==custo}
            refs={r:crescimentos[r] for r in ('naive','linear','comprar_manter')}
            for conjunto,pares in (('medias_individuais',True),('ensemble',False)):
                matrizes={v:np.array([crescimentos[f'{v}_{s}'] for s in c['seeds']]) if pares else crescimentos[f'{v}_ensemble'] for v in c['variantes']}
                intervalos+=conferir_ic(matrizes,refs,operacoes['comparacoes'][moeda][str(custo)]['contrastes'][conjunto],c['bootstrap'],pares)
            for v in c['variantes']:
                for k,item in operacoes['comparacoes'][moeda][str(custo)]['medias_seeds'][v].items():
                    valores=[next(l[k] for l in financeiras if l['moeda']==moeda and l['unidade']==f'{v}_{s}' and l['custo']==custo) for s in c['seeds']]
                    if all(isinstance(x,(int,float)) for x in valores):
                        np.testing.assert_allclose(item['media'],np.mean(valores),atol=1e-10,rtol=1e-12)
            print('CARTEIRAS_E_IC_CONFERIDOS',moeda,custo,flush=True)
        resumo[moeda]['operacoes_base']={l['unidade']:l['metricas'] for l in operacoes['carteiras'] if l['moeda']==moeda and l['custo']==1}
        resumo[moeda]['medias_operacoes_base']=operacoes['comparacoes'][moeda]['1']['medias_seeds']
        resumo[moeda]['ic_operacoes_L_menos_A']={s:operacoes['comparacoes'][moeda]['1']['contrastes'][s]['L_menos_A']['14'] for s in ('medias_individuais','ensemble')}
    destino=REG/'publicacao';destino.mkdir(exist_ok=False)
    pd.DataFrame(linhas).to_csv(destino/'previsoes.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(financeiras).to_csv(destino/'carteiras.csv',index=False,encoding='utf-8-sig')
    salvar_json(destino/'resumo.json',dict(execucao=ptr,moedas=resumo,atividade_ramos=ler_json(p/'inferencia.json')['atividade_ramos']))
    desenhar(destino,c,previsto,operacoes,curvas)
    salvar_json(destino/'manifesto.json',dict(utc=agora(),execucao=ptr,fonte={__file__:sha256(__file__)},
        arquivos={q.name:sha256(q) for q in destino.iterdir() if q.is_file()},inspecao_visual='pendente'))
    salvar_json(REG/'conferencia_posterior.json',dict(utc=agora(),execucao=ptr,situacao='aprovada',
        modelos=24,series=40,carteiras=132,intervalos_recalculados=intervalos,
        max_diferenca_metricas=maxerro,transicoes_mesmo_lado_conferidas=transicoes,
        fontes_pais_preservados=True,novos_treinamentos=0,publicacao=destino.relative_to(RAIZ).as_posix(),
        manifesto_sha256=sha256(destino/'manifesto.json')))


def desenhar(destino,c,previsoes,operacoes,curvas):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
                         'axes.spines.right':False,'figure.facecolor':'white'})
    cores={'A_ensemble':'#2563eb','L_ensemble':'#d97706','comprar_manter':'#64748b'}
    fig,eixos=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    for ax,moeda in zip(eixos.flat,c['moedas']):
        for nome in cores:
            cv=curvas[(moeda,nome,1)];datas=pd.to_datetime(np.r_[cv['origens_ms'],cv['origens_ms'][-1]+86400000],unit='ms',utc=True)
            ax.plot(datas,cv['saldos_diarios']/10000-1,color=cores[nome],label=nome.replace('_ensemble',' — ensemble').replace('comprar_manter','Comprar e manter'),lw=1.7)
        ax.axhline(0,color='#cbd5e1',lw=.8);ax.set_title(moeda.removesuffix('USDT'),loc='left',weight='bold')
        ax.yaxis.set_major_formatter(PercentFormatter(1));ax.grid(alpha=.15);ax.tick_params(axis='x',rotation=20)
        ax.set_ylabel('Retorno líquido acumulado')
    eixos.flat[0].legend(loc='best',fontsize=9)
    fig.suptitle('A versus L em 2026: quatro carteiras independentes\nEnsembles fixos de três seeds • futuros com continuidade • 01/jan–10/nov',fontsize=14)
    fig.savefig(destino/'carteiras_2026.png',dpi=180);fig.savefig(destino/'carteiras_2026.pdf');plt.close(fig)
    fig,eixos=plt.subplots(1,2,figsize=(12,5),layout='constrained')
    x=np.arange(4);largura=.23
    for deslocamento,(nome,cor) in enumerate((('A_ensemble','#2563eb'),('L_ensemble','#d97706'),('naive','#64748b'))):
        valores=[100*previsoes[m]['metricas'][nome]['rmse_retorno'] for m in c['moedas']]
        eixos[0].bar(x+(deslocamento-1)*largura,valores,largura,label=nome.replace('_ensemble',' ensemble'),color=cor)
    eixos[0].set(ylabel='RMSE do retorno diário (pontos percentuais)',title='Erro preditivo • menor é melhor')
    for deslocamento,nome in enumerate(('A_ensemble','L_ensemble')):
        valores=[100*next(q['metricas']['drawdown_maximo'] for q in operacoes['carteiras'] if q['moeda']==m and q['unidade']==nome and q['custo']==1) for m in c['moedas']]
        eixos[1].bar(x+(deslocamento-.5)*.3,valores,.3,color=cores[nome],label=nome.replace('_ensemble',' ensemble'))
    eixos[1].set(ylabel='Maior queda do patrimônio (%)',title='Risco operacional • menor é melhor')
    for ax in eixos:
        ax.set_xticks(x,[m.removesuffix('USDT') for m in c['moedas']]);ax.legend(fontsize=9);ax.grid(axis='y',alpha=.15)
    fig.suptitle('Erro parecido pode acompanhar resultados operacionais diferentes',fontsize=14)
    fig.savefig(destino/'erro_e_risco_2026.png',dpi=180);fig.savefig(destino/'erro_e_risco_2026.pdf');plt.close(fig)


if __name__=='__main__': executar()
