"""Conferência posterior F03: leitura de carteiras, sem reexecutar simulação/treino."""
import math
import shutil
from pathlib import Path
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,agora,ler_json,salvar_json,sha256,conferir_arquivos
from simulacao_operacoes.smart.mercado import carregar
from simulacao_operacoes.revisada.auditoria import conferir


def conferir_risco(resumo,ordens,mercado,cfg):
    """Reconstrói minuto a minuto a trajetória a partir do ledger validado."""
    futuro=resumo['braco']!='spot';pico=float(cfg['capital']);dd=0.;exp=0.;vend=0.;n=0
    def acumular(valores):
        nonlocal pico,dd
        a=np.atleast_1d(valores);pk=np.maximum.accumulate(np.r_[pico,a])[1:]
        dd=max(dd,float(np.max(1-a/pk)));pico=max(pico,float(a.max()))
    grupos={}
    for o in ordens:grupos.setdefault(o['minuto'],[]).append(o)
    tempos=list(grupos)
    for i,t in enumerate(tempos):
        k=mercado.indice(t);grupo=grupos[t]
        for o in grupo:
            for a in [o['antes'],o['depois']]:
                caixa=a['saldo']-a['quantidade']*a['preco_medio'] if futuro else a['saldo']
                acumular(caixa+a['quantidade']*mercado.marca[k,0])
        if i==len(tempos)-1:break
        fim=tempos[i+1];z=mercado.indice(fim);a=grupo[-1]['depois'];q=a['quantidade']
        caixa=a['saldo']-q*a['preco_medio'] if futuro else a['saldo']
        fund=np.zeros(z-k+1)
        if futuro:
            f=mercado.funding;f=f[(f[:,0]>t*60000)&(f[:,0]<=fim*60000)]
            np.add.at(fund,(f[:,0]//60000).astype(np.int64)-t,-q*f[:,1]*f[:,2])
        valores=caixa+q*mercado.marca[k:z,3]+np.cumsum(fund)[:-1]
        acumular(valores);exp+=float(np.sum(abs(q)*mercado.marca[k:z,3]/valores));vend+=float(np.sum(max(-q,0.)*mercado.marca[k:z,3]/valores));n+=len(valores)
    for a,b in [(dd,resumo['drawdown']),(exp/n,resumo['exposicao_media']),(vend/n,resumo['exposicao_vendida'])]:
        assert math.isclose(a,b,abs_tol=1e-10),(a,b)
    return {'drawdown':dd,'minutos_reconstruidos':n}


def figuras(q,destino):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    cores={'spot':'#167d9a','futuro':'#cf9c2d','futuro_bilateral':'#a44461'}
    rotulos={'spot':'Spot comprado','futuro':'Futuro comprado','futuro_bilateral':'Futuro bilateral'}
    politicas=['smart','direcional','direcional_filtrada']
    fig,axes=plt.subplots(1,2,figsize=(13,5),sharey=True,layout='constrained')
    for ax,modelo in zip(axes,['astra','crua']):
        a=q[(q.modelo==modelo)&(q.cenario=='base')]
        for j,(braco,cor) in enumerate(cores.items()):
            v=a[a.braco==braco].groupby(['politica','seed']).retorno_liquido.mean().unstack('seed').reindex(politicas)*100
            media=v.mean(axis=1).to_numpy();baixo=v.min(axis=1).to_numpy();alto=v.max(axis=1).to_numpy();x=np.arange(3)+(j-1)*.24
            ax.bar(x,media,width=.23,color=cor,label=rotulos[braco])
            ax.errorbar(x,media,yerr=np.array([media-baixo,alto-media]),fmt='none',ecolor='#333333',capsize=3,lw=1)
        ax.axhline(0,color='#444444',lw=.8);ax.set_xticks(range(3),['Smart\nrevisada','Saída no\nsinal contrário','Saída + filtro\nde entrada'])
        ax.set_title('Candidata Astra' if modelo=='astra' else 'OHLCV cru + Huber');ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
    axes[0].set_ylabel('Retorno líquido médio por bloco (%)');axes[1].legend(fontsize=8)
    fig.suptitle('F03 — Mesmas previsões, execução e políticas diferentes',fontsize=15)
    fig.supxlabel('Barras: média de 4 blocos × 8 seeds. Hastes: mínimo/máximo das médias por seed; não são IC.\n2024–2025 retrospectivos; carteiras independentes, sem composição entre blocos.',fontsize=9)
    fig.savefig(destino/'comparacao.png',dpi=160);plt.close(fig)


def executar():
    reg=RAIZ/'registros/revisao_operacional';ptr=ler_json(reg/'execucao.json');p=RAIZ/ptr['pasta']
    assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    fim=ler_json(p/'fechamento.json');assert fim['situacao']=='concluido_conferido'
    assert sha256(p/'publicacao/manifesto.json')==fim['publicacao_sha256']
    f=ler_json(p/'congelamento.json')['assinatura'];conferir_arquivos(RAIZ,f['fontes']);conferir_arquivos(p/'fontes',f['fontes'])
    pub=ler_json(p/'publicacao/manifesto.json');conferir_arquivos(p/'publicacao',pub['arquivos']);conferir_arquivos(p,pub['carteiras'])
    mercados=carregar(f['spot'],f['futuros']);resultados=ler_json(p/'publicacao/resultados.json');linhas=[];maior_diferenca=0.
    # Diagnóstico posterior de tamanho, sem usar volume futuro na decisão/fill.
    spot=pd.concat([pd.read_parquet(RAIZ/f['spot']['pasta']/n,columns=['inicio_utc','volume']) for n in sorted(f['spot']['arquivos'])])
    volumes_spot=pd.Series(spot.volume.to_numpy(),index=pd.DatetimeIndex(spot.inicio_utc).as_unit('ms').asi8//60000)
    contexto=ler_json(RAIZ/f['futuros']['pasta']/'manifesto.json')
    futuros=pd.read_parquet(RAIZ/contexto['contrato']['pai']['pasta']/'klines.parquet',columns=['open_time','volume'])
    volumes_futuros=pd.Series(futuros.volume.to_numpy(),index=futuros.open_time.to_numpy()//60000)
    participacoes={'spot':[],'futuro':[]};maiores={}
    dest=reg/'conferencias'/agora().replace(':','').replace('+','_');dest.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(Path(__file__),dest/'fonte.py')
    for i,g in enumerate(f['grade']):
        d=p/'carteiras'/g['chave'];m=ler_json(d/'manifesto.json');assert m['grade']==g;conferir_arquivos(d,m['arquivos'])
        r=ler_json(d/'resumo.json');o=ler_json(d/'ordens.json');e=ler_json(d/'funding.json');dias=ler_json(d/'diarios.json')
        mercado=mercados['spot' if g['braco']=='spot' else 'futuro']
        a=conferir(r,o,e,mercado,f['configuracao']);risco=conferir_risco(r,o,mercado,f['configuracao'])
        retorno=a['capital_final_independente']/f['configuracao']['capital']-1
        assert math.isclose(sum(v['retorno_log'] for v in dias),math.log1p(retorno),abs_tol=1e-10)
        assert len(dias)==f['cobertura'][g['bloco']]['dias']
        assert r['ordens']==sum(x['status']=='executada' for x in o)
        lado='spot' if g['braco']=='spot' else 'futuro';volumes=volumes_spot if lado=='spot' else volumes_futuros
        quantidades={}
        for ordem in o:
            if ordem['delta_executado']:quantidades[ordem['minuto']]=quantidades.get(ordem['minuto'],0.)+abs(ordem['delta_executado'])
        for t,quantidade in quantidades.items():
            volume=float(volumes.loc[t]);assert volume>0 and math.isfinite(volume)
            proporcao=quantidade/volume;participacoes[lado].append(proporcao)
            if lado not in maiores or proporcao>maiores[lado]['fracao_volume_minuto']:
                maiores[lado]={'carteira':g['chave'],'minuto':t,'quantidade_btc':quantidade,'volume_btc':volume,'fracao_volume_minuto':proporcao}
        maior_diferenca=max(maior_diferenca,abs(retorno-r['retorno_liquido']))
        linhas.append(dict(g,**r,componentes=a['decomposicao_futuros']))
        if (i+1)%200==0:print('CONFERIDAS',i+1,flush=True)
    q=pd.DataFrame(linhas);grupos=['modelo','politica','braco','cenario'];metricas=['retorno_liquido','drawdown','exposicao_media','exposicao_vendida','comissoes','slippage','funding','ordens','recusas','giro','abaixo_minimo','residuo_usdt']
    medias=q.groupby(['bloco']+grupos)[metricas].mean().groupby(grupos).mean().sort_index()
    original=pd.DataFrame(resultados['medias_globais']).set_index(grupos)[metricas].sort_index()
    np.testing.assert_allclose(medias,original,atol=1e-10,rtol=0)
    antes=ler_json(reg/'preservacao_antes.json');conferir_arquivos(RAIZ,antes['arquivos'])
    figuras(q,dest)
    recibo={'utc':agora(),'execucao':ptr,'carteiras_conferidas':len(linhas),'cobertura_exata':set(q.chave)=={x['chave'] for x in f['grade']},
        'maior_diferenca_retorno':maior_diferenca,'metricas_risco_recalculadas_minuto_a_minuto':True,'arquivos_anteriores_integros':len(antes['arquivos']),
        'publicacao_sha256':fim['publicacao_sha256'],'fonte_sha256':sha256(dest/'fonte.py'),'medias':medias.reset_index().to_dict('records'),
        'liquidez_posterior':{lado:{'maximo':maiores[lado],'p95_fracao':float(np.quantile(v,.95)),'ordens_minuto_acima_5pct':sum(x>.05 for x in v),'ordens_minuto_acima_100pct':sum(x>1 for x in v),'amostras':len(v)} for lado,v in participacoes.items()},
        'limite_liquidez':'Volume do minuto completo e diagnostico posterior; nao prova profundidade no instante do fill, nem certifica slippage.'}
    salvar_json(dest/'conferencia.json',recibo)
    salvar_json(dest/'manifesto.json',{'arquivos':{x.name:sha256(x) for x in dest.iterdir() if x.is_file()}})
    salvar_json(reg/'conferencia_atual.json',{'pasta':dest.relative_to(RAIZ).as_posix(),'manifesto_sha256':sha256(dest/'manifesto.json')})
    print('CONFERENCIA',dest,flush=True)
    print(medias[['retorno_liquido','drawdown','ordens']].to_string(),flush=True)

if __name__=='__main__':executar()
