"""Conferência posterior das previsões/ledgers; não treina ou reexecuta simuladores."""
import math
import json
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,sha256,conferir_arquivos,agora


def executar():
    reg=RAIZ/'registros/retomada_alvo_diario';ptr=ler_json(reg/'execucao.json');p=RAIZ/ptr['pasta']
    assert ler_json(reg/'estado.json')['situacao']=='concluido_conferido'
    assert not ler_json(p/'processo.json')['ativo']
    assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    f=ler_json(p/'congelamento.json');c=f['configuracao'];pub=p/'publicacao'
    fecho=ler_json(reg/'fechamento.json');assert sha256(RAIZ/fecho['arquivo'])==fecho['sha256']
    fechamento=ler_json(p/'fechamento.json');conferir_arquivos(p,fechamento['arquivos'])
    assert ler_json(p/'controle.json')['aprovado']
    np.testing.assert_array_equal(np.load(p/'ajustes/seed_42/validacao.npz')['previsoes'],np.load(p/'ajustes/controle_42/validacao.npz')['previsoes'])
    diagnosticos={};previsoes={};diarias={};linhas=ler_json(pub/'previsao.json')
    for fase in ('validacao','teste'):
        diagnosticos[fase]={};previsoes[fase]={};diarias[fase]={}
        for seed in c['seeds']:
            z=np.load(pub/'previsoes'/f'{fase}_{seed}.npz');v=z['previsoes'];y=z['y'];u=z['ultimo_close']
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
            for nome,vv in [('preco',za['previsoes']),('retorno',v)]:
                np.testing.assert_allclose(par[nome]['mse_retorno'],np.mean(((vv-y)/u)**2),rtol=1e-12)
            for nome in ('preco','retorno','operacao_preco','operacao_retorno'):
                for metrica,valor in comp['fases'][fase]['medias'][nome].items():
                    np.testing.assert_allclose(valor,np.mean([r[nome][metrica] for r in comp['fases'][fase]['seeds_pareadas']]),rtol=1e-12)

            bins=[]
            for a,b in [(0,.002),(.002,.005),(.005,.01),(.01,.02),(.02,np.inf)]:
                ix=(abs(prev)>a)&(abs(prev)<=b)
                bins.append({'min':a,'max':None if np.isinf(b) else b,'n':int(ix.sum()),'acerto':float(np.mean(np.sign(prev[ix])==np.sign(real[ix]))) if ix.any() else None})
            diagnosticos[fase][str(seed)]={'previsao_retorno_media':float(prev.mean()),'real_retorno_medio':float(real.mean()),
                'correlacao_retorno':float(np.corrcoef(prev,real)[0,1]),'fracao_dias_alta_real':float((real>0).mean()),
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
    salvar_json(dest/'conferencia.json',recibo)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axs=plt.subplots(1,2,figsize=(13,4.5),sharey=True)
    cores={'42':'#00836d','17':'#3975c6','2026':'#c45151','ensemble':'#8b5caa','naive':'#72777f'}
    for ax,fase in zip(axs,('validacao','teste')):
        t=pd.to_datetime(np.r_[diarias[fase]['origens'][0],diarias[fase]['origens']+86460000],unit='ms',utc=True)
        for nome,cor in cores.items():ax.plot(t,curvas[f'{fase}_{nome}'],label='Média das previsões' if nome=='ensemble' else ('Caixa / Naive' if nome=='naive' else f'Seed {nome}'),color=cor,lw=1.6)
        ax.set_title('2024 · validação' if fase=='validacao' else '2025 · teste retrospectivo');ax.grid(alpha=.18);ax.tick_params(axis='x',rotation=25)
    axs[0].set_ylabel('Patrimônio (USDT) · início em 10.000');axs[1].legend(frameon=False,fontsize=8)
    fig.suptitle('Alvo retorno diário · futuros bilateral · custos base\nCada curva é uma carteira independente; saldo diário não mostra todo o drawdown intradiário',fontsize=11)
    fig.tight_layout();fig.savefig(dest/'patrimonio.png',dpi=160);plt.close(fig)
    print(str(dest));print('AUDITORIA',operacoes,residuo)


if __name__=='__main__':executar()
