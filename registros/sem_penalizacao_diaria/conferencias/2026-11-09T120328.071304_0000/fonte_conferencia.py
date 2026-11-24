"""Conferência posterior das previsões/ledgers; não treina ou reexecuta simuladores."""
import math
import json
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,sha256,conferir_arquivos,agora


def executar():
    reg=RAIZ/'registros/sem_penalizacao_diaria';ptr=ler_json(reg/'execucao.json');p=RAIZ/ptr['pasta']
    assert ler_json(reg/'estado.json')['situacao']=='concluido_conferido'
    assert not ler_json(p/'processo.json')['ativo']
    assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    f=ler_json(p/'congelamento.json');c=f['configuracao'];pub=p/'publicacao'
    fecho=ler_json(reg/'fechamento.json');assert sha256(RAIZ/fecho['arquivo'])==fecho['sha256']
    fechamento=ler_json(p/'fechamento.json');conferir_arquivos(p,fechamento['arquivos'])
    assert ler_json(p/'controle.json')['aprovado']
    np.testing.assert_array_equal(np.load(p/'ajustes/seed_42/validacao.npz')['previsoes'],np.load(p/'ajustes/controle_42/validacao.npz')['previsoes'])
    from entradas_modelo.padronizacao_diaria import preparar_com_escalas
    dados,escalas=preparar_com_escalas(pd.read_parquet(RAIZ/f['diario']['pasta']/'diario.parquet'),c)
    assert escalas==f['escalas']==ler_json(p/'escalas.json')
    assert escalas['candles_unicos']==1459
    for nome in ('seed_42','controle_42'):
        assert ler_json(p/'ajustes'/nome/'conclusao.json')['vinculo']['escalas_sha256']==sha256(p/'escalas.json')
    assert ler_json(p/'ajustes/seed_42/selecao.json')['epoca']==ler_json(p/'ajustes/controle_42/selecao.json')['epoca']
    diagnosticos={};previsoes={};diarias={};linhas=ler_json(pub/'previsao.json')
    for fase in ('validacao','teste'):
        diagnosticos[fase]={};previsoes[fase]={};diarias[fase]={}
        for seed in c['seeds']:
            z=np.load(pub/'previsoes'/f'{fase}_{seed}.npz');v=z['previsoes'];y=z['y'];u=z['ultimo_close']
            np.testing.assert_array_equal(z['alvo_retorno'],dados[fase]['y'])
            previsoes[fase][str(seed)]=v;diarias[fase]['origens']=z['origens_ms']
            m=next(r['metricas'] for r in linhas if r['fase']==fase and r['seed']==seed)
            for k,valor in {'mse_usdt2':np.mean((v-y)**2),'rmse_usdt':np.sqrt(np.mean((v-y)**2)),
                            'mae_usdt':np.mean(abs(v-y)),'mape_pct':np.mean(abs(v-y)/y)*100}.items():
                np.testing.assert_allclose(m[k],valor,rtol=1e-12)
            prev=v/u-1;real=y/u-1;s=np.where(abs(prev)>.002,np.sign(prev),0)
            np.testing.assert_allclose(prev,z['previsoes_retorno'],atol=1e-14,rtol=1e-12)
            np.testing.assert_allclose(real,z['alvo_retorno'],atol=1e-14,rtol=1e-12)
            np.testing.assert_allclose(m['mse_retorno'],np.mean((prev-real)**2),rtol=1e-12)
            comp=ler_json(pub/'comparacao.json')
            ant=RAIZ/comp['referencia']['pasta'];za=np.load(ant/'publicacao/previsoes'/f'{fase}_{seed}.npz')
            for campo in ('y','ultimo_close','origens_ms','fim_alvo_ms'):np.testing.assert_array_equal(za[campo],z[campo])
            par=next(x for x in comp['fases'][fase]['seeds_pareadas'] if x['seed']==seed)
            for nome,vv in [('referencia',za['previsoes']),('sem_penalizacao',v)]:
                np.testing.assert_allclose(par[nome]['mse_retorno'],np.mean(((vv-y)/u)**2),rtol=1e-12)
            for nome in ('referencia','sem_penalizacao','operacao_referencia','operacao_sem_penalizacao'):
                for metrica,valor in comp['fases'][fase]['medias'][nome].items():
                    np.testing.assert_allclose(valor,np.mean([r[nome][metrica] for r in comp['fases'][fase]['seeds_pareadas']]),rtol=1e-12)

            bins=[]
            for a,b in [(0,.002),(.002,.005),(.005,.01),(.01,.02),(.02,np.inf)]:
                ix=(abs(prev)>a)&(abs(prev)<=b)
                bins.append({'min':a,'max':None if np.isinf(b) else b,'n':int(ix.sum()),'acerto':float(np.mean(np.sign(prev[ix])==np.sign(real[ix]))) if ix.any() else None})
            diagnosticos[fase][str(seed)]={'previsao_retorno_media':float(prev.mean()),'real_retorno_medio':float(real.mean()),
                'desvio_previsao':float(prev.std()),'previsao_min':float(prev.min()),'previsao_max':float(prev.max()),'fracao_preve_alta':float((prev>0).mean()),'correlacao_retorno':float(np.corrcoef(prev,real)[0,1]),'fracao_dias_alta_real':float((real>0).mean()),
                'compra':int((s>0).sum()),'venda':int((s<0).sum()),'caixa':int((s==0).sum()),'faixas_magnitude':bins,
                'acerto_quando_preve_alta':float(np.mean(real[prev>0]>0)) if (prev>0).any() else None,
                'acerto_quando_preve_queda':float(np.mean(real[prev<0]<0)) if (prev<0).any() else None}
        previsoes[fase].update(ensemble=np.mean(list(previsoes[fase].values()),axis=0),naive=u,sempre_comprado=u,sempre_vendido=u)
        diarias[fase]['ultimo']=u
    mercado=RAIZ/f['mercado_minuto']['pasta'];k=pd.read_parquet(mercado/'klines.parquet',columns=['open_time','open']).set_index('open_time')['open']
    funding=pd.read_parquet(mercado/'funding.parquet');ft=funding.fundingTime.to_numpy();fr=funding.fundingRate.to_numpy();fp=funding.markPrice.to_numpy()
    carteiras=ler_json(pub/'carteiras.json');assert len(carteiras)==70
    resumos=[];curvas={};operacoes=0;residuo=0.
    for linha in carteiras:
        fase,nome,cen=linha['fase'],linha['unidade'],linha['cenario'];d=RAIZ/linha['pasta'];r=ler_json(d/'resultado.json');z=np.load(d/'curva.npz')
        cfg=c['operacoes'];cc=c['cenarios'][cen];saldo=cfg['capital_inicial'];ps=previsoes[fase][nome];u=diarias[fase]['ultimo'];ts=diarias[fase]['origens']
        sinais=np.where(abs(ps/u-1)>cfg['filtro_retorno_absoluto'],np.sign(ps/u-1),0)
        if nome.startswith('sempre_'):sinais=np.full(len(ts),1 if nome=='sempre_comprado' else -1)
        if cc['lado']:sinais=np.where(sinais==cc['lado'],sinais,0)
        por_dia={o['origem_ms']:o for o in r['operacoes']};brutos=[];custos=[]
        for i,t in enumerate(ts):
            if int(t) not in por_dia:
                assert sinais[i]==0
                np.testing.assert_allclose(z['saldos_diarios'][i+1],saldo,atol=1e-7,rtol=0);continue
            o=por_dia[int(t)];lado=int(sinais[i]);q=o['quantidade'];operacoes+=1
            assert lado==o['lado'] and o['entrada_ms']==int(t)+60000 and o['saida_ms']==o['entrada_ms']+86400000
            slip=cfg['slippage_por_lado']*cc['slippage_multiplicador'];pe=float(k.loc[o['entrada_ms']])*(1+lado*slip);psa=float(k.loc[o['saida_ms']])*(1-lado*slip)
            pe=(math.ceil(pe/.1) if lado>0 else math.floor(pe/.1))*.1;psa=(math.floor(psa/.1) if lado>0 else math.ceil(psa/.1))*.1
            np.testing.assert_allclose([pe,psa],[o['preco_entrada'],o['preco_saida']],atol=1e-8,rtol=0)
            assert q==math.floor(saldo*.95/pe/.001)*.001
            ix=(ft>=o['entrada_ms'])&(ft<o['saida_ms']);fin=-lado*q*math.fsum(fr[ix]*fp[ix]);com=q*(pe+psa)*.0005
            bruto=lado*q*(psa-pe);liq=bruto-com+fin
            residuo=max(residuo,abs(liq-o['pnl_liquido']))
            np.testing.assert_allclose([saldo,liq,fin,com],[o['caixa_antes'],o['pnl_liquido'],o['funding'],o['comissao']],atol=1e-7,rtol=0)
            bruto_antes_custos=lado*q*(float(k.loc[o['saida_ms']])-float(k.loc[o['entrada_ms']]))
            brutos.append(bruto_antes_custos);custos.append(bruto_antes_custos-bruto)
            saldo+=liq;np.testing.assert_allclose(saldo,z['saldos_diarios'][i+1],atol=1e-7,rtol=0)
        env=z['patrimonio_envelope'];dd=float(np.max(1-env/np.maximum.accumulate(env)))
        np.testing.assert_allclose([saldo,dd],[r['metricas']['capital_final'],r['metricas']['drawdown_maximo']],atol=1e-7,rtol=0)
        rec={'fase':fase,'unidade':nome,'cenario':cen,**r['metricas'],
             'pnl_preco_minuto_mesmas_quantidades':sum(brutos),'impacto_slippage_tick_mesmas_quantidades':sum(custos)}
        resumos.append(rec)
        if cen=='base':curvas[f'{fase}_{nome}']=z['saldos_diarios'].copy()
    dest=reg/'conferencias'/agora().replace(':','').replace('+','_');dest.mkdir(parents=True)
    recibo={'utc':agora(),'execucao':ptr,'arquivos_conferidos':len(fechamento['arquivos']),'carteiras':len(carteiras),'operacoes_conferidas':operacoes,
        'residuo_maximo_usdt':residuo,'diagnosticos':diagnosticos,'carteiras_detalhadas':resumos,'fonte_sha256':sha256(__file__),
        'limites':'Leitura posterior exploratória; não treina, não cria políticas ou simula carteiras novas. Atribuição de custos mantém quantidades realizadas; não é carteira sem custos. Drawdown confere envelope publicado, não caminho de ticks real.'}
    # Conferência adicional do contraste e incerteza no MSE de retorno contra Naive.
    cis={}
    for fase in ('validacao','teste'):
        erros=[];deltas=[];logs=[]
        for seed in c['seeds']:
            b=np.load(pub/'previsoes'/f'{fase}_{seed}.npz');a=np.load(ant/'publicacao/previsoes'/f'{fase}_{seed}.npz')
            er=((b['previsoes']-b['y'])/b['ultimo_close'])**2
            ea=((a['previsoes']-a['y'])/a['ultimo_close'])**2
            en=(b['y']/b['ultimo_close']-1)**2
            erros.append(er-en);deltas.append(er-ea)
            ca=np.load(ant/'publicacao/carteiras'/fase/str(seed)/'base/curva.npz')['saldos_diarios']
            cb=np.load(pub/'carteiras'/fase/str(seed)/'base/curva.npz')['saldos_diarios']
            logs.append(np.diff(np.log(cb))-np.diff(np.log(ca)))
        erros=np.array(erros);deltas=np.array(deltas);logs=np.array(logs);n=erros.shape[1];cis[fase]={}
        for bloco in (7,14,28):
            rng=np.random.default_rng(3105);amostras=[]
            for _ in range(2000):
                si=rng.integers(0,3,3);ix=(rng.integers(0,n-bloco+1,int(np.ceil(n/bloco)))[:,None]+np.arange(bloco)).ravel()[:n]
                amostras.append([erros[si][:,ix].mean(),deltas[si][:,ix].mean(),logs[si][:,ix].mean()])
            limites=np.quantile(np.asarray(amostras),[.025,.975],axis=0)
            publicado=comp['fases'][fase]['incerteza'][str(bloco)]
            np.testing.assert_allclose(limites[:,1],publicado['delta_mse_retorno_ic95'],atol=1e-16,rtol=1e-12)
            np.testing.assert_allclose(limites[:,2],publicado['delta_crescimento_log_ic95'],atol=1e-16,rtol=1e-12)
            cis[fase][str(bloco)]={'delta_mse_retorno_vs_naive_ic95':limites[:,0].tolist(),'contraste_publicado_recalculado':True}
        for nome in ('naive','sempre_comprado','sempre_vendido'):
            for cen in c['cenarios']:
                np.testing.assert_array_equal(np.load(ant/'publicacao/carteiras'/fase/nome/cen/'curva.npz')['saldos_diarios'],np.load(pub/'carteiras'/fase/nome/cen/'curva.npz')['saldos_diarios'])
    recibo['incerteza_retorno_vs_naive']=cis
    recibo['escalas_recalculadas_exatas']=True
    salvar_json(dest/'conferencia.json',recibo)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axs=plt.subplots(1,2,figsize=(13,4.5),sharey=True)
    cores={'42':'#00836d','17':'#3975c6','2026':'#c45151','ensemble':'#8b5caa','naive':'#72777f'}
    for ax,fase in zip(axs,('validacao','teste')):
        t=pd.to_datetime(np.r_[diarias[fase]['origens'][0],diarias[fase]['origens']+86460000],unit='ms',utc=True)
        for nome,cor in cores.items():ax.plot(t,curvas[f'{fase}_{nome}'],label='Média das previsões' if nome=='ensemble' else ('Caixa / Naive' if nome=='naive' else f'Seed {nome}'),color=cor,lw=1.6)
        antigas=[np.load(ant/'publicacao/carteiras'/fase/str(seed)/'base/curva.npz')['saldos_diarios'] for seed in c['seeds']]
        ax.plot(t,np.mean(antigas,axis=0),color='#262626',ls='--',lw=2,label='Referência: média dos saldos')
        ax.set_title('2024 · validação' if fase=='validacao' else '2025 · teste retrospectivo');ax.grid(alpha=.18);ax.tick_params(axis='x',rotation=25)
    axs[0].set_ylabel('Patrimônio (USDT) · início em 10.000');axs[1].legend(frameon=False,fontsize=8)
    fig.suptitle('Adam sem penalização · alvo retorno diário · futuros bilateral · custos base\nCada curva é uma carteira independente; saldo diário não mostra todo o drawdown intradiário',fontsize=11)
    fig.tight_layout();fig.savefig(dest/'patrimonio.png',dpi=160);plt.close(fig)
    print(str(dest));print('AUDITORIA',operacoes,residuo)


if __name__=='__main__':executar()
