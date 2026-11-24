"""Conferência posterior e figura de2026; sem nova inferência ou backtest."""
import csv
from decimal import Decimal
import io
from pathlib import Path
import zipfile
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as datas
from matplotlib.ticker import PercentFormatter
from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256, conferir_arquivos
from .ciclo import contexto


def main():
    ptr,p,f=contexto()
    fechamento=ler_json(p/'fechamento.json')
    assert fechamento['situacao']=='concluido_conferido'
    assert sha256(p/'manifesto.json')==fechamento['manifesto_sha256']
    conferir_arquivos(p,ler_json(p/'manifesto.json')['arquivos'])
    r=ler_json(p/'resultados.json')
    esperado={(m,u,c) for m in f['configuracao']['moedas'] for u in ['ensemble','comprar_manter'] for c in [.0001,.0002,.0003]}
    assert len(r['carteiras'])==24
    assert {(a['simbolo'],a['unidade'],a['slippage_por_lado']) for a in r['carteiras']}==esperado
    curvas={};tempos={};max_residuo=0.;ordens=fundings=0
    with zipfile.ZipFile(p/'carteiras.zip') as pacote:
        assert pacote.testzip() is None
        assert len(pacote.namelist())==len(set(pacote.namelist()))==48
        for linha in r['carteiras']:
            a=ler_json_zip(pacote,linha['membro']+'/resultado.json')
            cv=dict(np.load(io.BytesIO(pacote.read(linha['membro']+'/curva.npz')),allow_pickle=False))
            assert a['metricas']==linha['metricas']
            saldo=Decimal(str(a['regras']['capital_inicial']))
            for o in a['ordens']:
                saldo-=Decimal(str(o['delta']))*Decimal(str(o['preenchimento']))+Decimal(str(o['comissao']))
            for e in a['funding']:
                saldo+=Decimal(str(e['valor']))
            erro=abs(float(saldo)-cv['saldos_diarios'][-1]);max_residuo=max(max_residuo,erro)
            assert erro<1e-7
            met=linha['metricas'];capital=a['regras']['capital_inicial']
            np.testing.assert_allclose(met['retorno_liquido'],float(saldo)/capital-1,atol=1e-12)
            np.testing.assert_allclose(met['drawdown_maximo'],cv['drawdown_acumulado'][-1],atol=1e-12)
            assert len(a['dias'])==314
            assert cv['origens_ms'][0]==1767225600000
            assert str(cv['origens_ms'][-1].astype('datetime64[ms]'))=='2026-11-10T00:00:00.000'
            curvas[(linha['simbolo'],linha['unidade'],linha['slippage_por_lado'])]=cv['saldos_diarios']
            tempos[linha['simbolo']]=cv['origens_ms']
            ordens+=len(a['ordens']);fundings+=len(a['funding'])
    for simbolo in f['configuracao']['moedas']:
        d=p/'previsoes'/simbolo
        z=dict(np.load(d/'ensemble.npz',allow_pickle=False))
        seeds=[dict(np.load(d/f'seed_{s}.npz',allow_pickle=False)) for s in f['configuracao']['seeds']]
        np.testing.assert_array_equal(z['previsoes'],np.mean([s['previsoes'] for s in seeds],axis=0))
        for s in seeds:
            np.testing.assert_array_equal(s['origens_ms'],z['origens_ms'])
        pred=z['previsoes']/z['ultimo_close']-1;real=z['y']/z['ultimo_close']-1
        oficial=next(a for a in r['metricas_previsoes'] if a['simbolo']==simbolo)
        np.testing.assert_allclose(np.mean((pred-real)**2),oficial['mse_retorno'],atol=1e-15)
        for custo in [.0001,.0002,.0003]:
            delta=np.diff(np.log(curvas[(simbolo,'ensemble',custo)]))-np.diff(np.log(curvas[(simbolo,'comprar_manter',custo)]))
            for bloco in [7,14,28]:
                rng=np.random.default_rng(11112026);n=len(delta);v=[]
                for _ in range(2000):
                    inicios=rng.integers(0,n-bloco+1,int(np.ceil(n/bloco)))
                    ix=np.concatenate([np.arange(i,i+bloco) for i in inicios])[:n]
                    v.append(delta[ix].mean())
                ic=np.quantile(v,[.025,.975])
                np.testing.assert_allclose(ic,r['intervalos_ensemble_menos_comprar_manter'][simbolo][str(custo)][str(bloco)]['ic95'],atol=1e-15)
    entrega=p/'publicacao'
    entrega.mkdir(exist_ok=False)
    linhas=[]
    for simbolo in f['configuracao']['moedas']:
        ens=next(a['metricas'] for a in r['carteiras'] if a['simbolo']==simbolo and a['unidade']=='ensemble' and a['slippage_por_lado']==.0001)
        bh=next(a['metricas'] for a in r['carteiras'] if a['simbolo']==simbolo and a['unidade']=='comprar_manter' and a['slippage_por_lado']==.0001)
        ic=r['intervalos_ensemble_menos_comprar_manter'][simbolo]['0.0001']['14']['ic95']
        linhas.append(dict(simbolo=simbolo,retorno_ensemble=ens['retorno_liquido'],retorno_comprar_manter=bh['retorno_liquido'],
                           diferenca_pontos_percentuais=100*(ens['retorno_liquido']-bh['retorno_liquido']),dd_ensemble=ens['drawdown_maximo'],
                           dd_comprar_manter=bh['drawdown_maximo'],dias_comprado=ens['dias_comprado'],dias_vendido=ens['dias_vendido'],
                           blocos_posicao=ens['blocos_posicao'],ordens=ens['ordens'],comissoes=ens['comissoes'],funding=ens['funding'],
                           ic_log_diario_inferior=ic[0],ic_log_diario_superior=ic[1]))
    with (entrega/'comparacao_base.csv').open('w',encoding='utf-8-sig',newline='') as arquivo:
        escritor=csv.DictWriter(arquivo,fieldnames=list(linhas[0]));escritor.writeheader();escritor.writerows(linhas)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    figura,eixos=plt.subplots(2,2,figsize=(12.5,8),sharex=True)
    for linha,eixo in zip(linhas,eixos.flat):
        simbolo=linha['simbolo'];t=tempos[simbolo]
        tempo=np.r_[t[0]+60000,t+86460000].astype('datetime64[ms]')
        for unidade,cor,nome in [('ensemble','#1268a8','Ensemble congelado'),('comprar_manter','#b36e21','Comprar/manter no futuro')]:
            curva=curvas[(simbolo,unidade,.0001)]/10000-1
            eixo.plot(tempo,curva,color=cor,label=nome,linewidth=1.8)
        eixo.axhline(0,color='#46525c',linewidth=.8,linestyle=':')
        eixo.set_title(simbolo.replace('USDT',''),loc='left',fontweight='bold')
        eixo.yaxis.set_major_formatter(PercentFormatter(1))
        eixo.xaxis.set_major_locator(datas.MonthLocator(interval=2))
        eixo.xaxis.set_major_formatter(datas.DateFormatter('%b'))
        eixo.grid(axis='y',alpha=.25);eixo.set_ylabel('Retorno líquido acumulado')
        texto=f"Ensemble: {linha['retorno_ensemble']:+.1%}   |   Comprar/manter: {linha['retorno_comprar_manter']:+.1%}\nDD ensemble: {linha['dd_ensemble']:.1%}"
        eixo.text(.02,.97,texto,transform=eixo.transAxes,va='top',fontsize=9,
                  bbox=dict(facecolor='white',alpha=.85,edgecolor='none'))
    figura.suptitle('Ensemble preservado: avaliação temporal em 2026',x=.08,y=.98,ha='left',fontsize=16,fontweight='bold')
    figura.text(.08,.932,'01/jan a 10/nov • 314 decisões por moeda • Mesmos checkpoints e escalas, sem novos treinos',color='#4b5865')
    h,l=eixos.flat[0].get_legend_handles_labels();figura.legend(h,l,loc='lower center',bbox_to_anchor=(.5,.05),ncol=2,frameon=False)
    figura.text(.08,.015,'Comissão: 0,05%/lado; slippage provisório: 0,01%/lado; funding incluído. Capital inicial: 10.000 USDT por carteira.\n'
                       'Comprar/manter usa quantidade fixa no mesmo futuro. Drawdown é envelope conservador; período parcial, não retorno anual.',fontsize=9,color='#4b5865')
    figura.subplots_adjust(top=.87,bottom=.18,left=.08,right=.98,hspace=.27,wspace=.23)
    figura.savefig(entrega/'comparacao_2026.png',dpi=160);figura.savefig(entrega/'comparacao_2026.pdf');plt.close(figura)
    salvar_json(entrega/'conferencia_posterior.json',dict(utc=agora(),execucao=ptr['id'],carteiras=24,modelos=12,
                 ensemble_recalculado=True,medidas_previsao_recalculadas=4,intervalos_recalculados=36,
                 ordens=ordens,fundings=fundings,residuo_decimal_usdt=max_residuo,novas_simulacoes=0,novas_inferencias=0,
                 limite='Reconcilia ledgers e curvas; auditoria de eventos, preços e risco está no executor publicado.'))
    salvar_json(p/'entrega_manifesto.json',dict(utc=agora(),manifesto_cientifico_sha256=sha256(p/'manifesto.json'),
                 leitor_sha256=sha256(Path(__file__)),arquivos={q.relative_to(p).as_posix():sha256(q) for q in entrega.iterdir()}))
    print(linhas,flush=True)


def ler_json_zip(pacote,nome):
    import json
    return json.loads(pacote.read(nome))


if __name__=='__main__':
    main()
