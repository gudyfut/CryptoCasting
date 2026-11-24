"""Leitura posterior: calibração, magnitude, sinais e custos; nunca treina/simula.

MSE = viés² + variância prevista + variância real - 2 covariância.
Custos são atribuídos às quantidades realmente publicadas, sem recompor capital.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, ler_json, salvar_json, sha256, conferir_arquivos, agora

SEEDS = (42, 17, 2026)
FAIXAS = (0, .002, .005, .01, .02, float('inf'))
REGISTROS = {'preco': 'cryptomamba_reproducivel', 'retorno': 'retomada_alvo_diario'}


def correlacao(a, b):
    return float(np.corrcoef(a, b)[0, 1]) if np.std(a) > 0 and np.std(b) > 0 else None


def descrever(p, y):
    vp, vy = float(np.var(p)), float(np.var(y))
    cov = float(np.mean((p-p.mean())*(y-y.mean())))
    vies = float(np.mean(p-y)); mse = float(np.mean((p-y)**2))
    np.testing.assert_allclose(mse, vies**2+vp+vy-2*cov, atol=1e-16)
    rho = correlacao(p, y)
    return dict(n=len(y), previsao_media=float(p.mean()), realizado_medio=float(y.mean()),
                desvio_previsao=float(p.std()), desvio_real=float(y.std()), vies=vies,
                mse=mse, mae=float(np.mean(abs(p-y))), mse_naive=float(np.mean(y*y)),
                correlacao=rho, correlacao_ordem=correlacao(pd.Series(p).rank(), pd.Series(y).rank()),
                intercepto_descritivo=float(y.mean()-cov/vp*p.mean()) if vp else None,
                inclinacao_descritiva=cov/vp if vp else None,
                vies_quadrado=vies*vies, variancia_previsao=vp, variancia_real=vy,
                menos_duas_covariancias=-2*cov,
                fracao_preve_alta=float(np.mean(p>0)), acerto_direcao=float(np.mean(np.sign(p)==np.sign(y))))


def grupo(p, y, execucao, indices, operacoes, origens):
    ids=np.flatnonzero(indices)
    if len(ids)==0: return {'n': 0, 'operacoes': 0}
    ops=[operacoes[int(origens[i])] for i in ids if int(origens[i]) in operacoes]
    s=np.sign(p[ids]); z=y[ids]; e=execucao[ids]
    return {'n':len(ids), 'operacoes':len(ops),
            'previsao_abs_media':float(np.mean(abs(p[ids]))),
            'retorno_alinhado_fechamento_medio':float(np.mean(s*z)),
            'retorno_alinhado_execucao_medio':float(np.mean(s*e)),
            'acerto_direcao':float(np.mean(s==np.sign(z))),
            'pnl_liquido_usdt':sum(o['pnl_liquido'] for o in ops),
            'acerto_liquido':float(np.mean([o['pnl_liquido']>0 for o in ops])) if ops else None}


def executar():
    entradas={}; fontes={}; pastas={}; congelados={}
    def registrar(caminho):
        caminho=Path(caminho);entradas[caminho.relative_to(RAIZ).as_posix()]=sha256(caminho)
        return caminho
    for versao, reg in REGISTROS.items():
        reg=RAIZ/'registros'/reg; ptr=ler_json(registrar(reg/'execucao.json'))
        p=RAIZ/ptr['pasta'];pastas[versao]=p
        assert ler_json(reg/'estado.json')['situacao']=='concluido_conferido'
        assert not ler_json(p/'processo.json')['ativo']
        assert sha256(registrar(p/'congelamento.json'))==ptr['congelamento_sha256']
        f=ler_json(p/'congelamento.json');congelados[versao]=f
        fecho=ler_json(registrar(p/'fechamento.json'));conferir_arquivos(p,fecho['arquivos'])
        assert ler_json(registrar(p/'controle.json'))['aprovado']
    mercado=RAIZ/congelados['retorno']['mercado_minuto']['pasta']
    k=pd.read_parquet(registrar(mercado/'klines.parquet'),columns=['open_time','open']).set_index('open_time')['open']
    resultados={}; arrays={}; transicoes={}
    for fase in ('validacao','teste'):
        resultados[fase]={};arrays[fase]={};transicoes[fase]={}
        for versao,pasta in pastas.items():
            resultados[fase][versao]={};arrays[fase][versao]={}
            for seed in SEEDS:
                z=np.load(registrar(pasta/'publicacao/previsoes'/f'{fase}_{seed}.npz'))
                t=z['origens_ms'];p=z['previsoes']/z['ultimo_close']-1;y=z['y']/z['ultimo_close']-1
                if versao=='retorno':
                    a=arrays[fase]['preco'][seed]
                    np.testing.assert_array_equal(t,a['t']);np.testing.assert_array_equal(y,a['y'])
                pe=k.loc[t+60000].to_numpy();ps=k.loc[t+86460000].to_numpy();re=ps/pe-1
                sinal=np.where(abs(p)>.002,np.sign(p),0).astype(int)
                r=ler_json(registrar(pasta/'publicacao/carteiras'/fase/str(seed)/'base/resultado.json'))
                ops={o['origem_ms']:o for o in r['operacoes']}
                assert len(ops)==len(r['operacoes'])==int((sinal!=0).sum())
                bruto=friccao=comissao=funding=liquido=0.; custos_bps=[];ret_op=[]; ganhos=[];perdas=[]
                diario_liq=np.zeros(len(t));diario_bruto=np.zeros(len(t));diario_unit=np.zeros(len(t))
                for i,ti in enumerate(t):
                    if not sinal[i]:continue
                    o=ops[int(ti)];assert o['lado']==sinal[i]
                    raw=sinal[i]*o['quantidade']*(ps[i]-pe[i]);slip=raw-o['pnl_bruto']
                    np.testing.assert_allclose(raw-slip-o['comissao']+o['funding'],o['pnl_liquido'],atol=1e-8)
                    bruto+=raw;friccao+=slip;comissao+=o['comissao'];funding+=o['funding'];liquido+=o['pnl_liquido']
                    nocional=o['quantidade']*pe[i]
                    custos_bps.append((slip+o['comissao']-o['funding'])/nocional*10000)
                    ret_op.append(o['pnl_liquido']/nocional)
                    diario_liq[i]=o['pnl_liquido'];diario_bruto[i]=raw;diario_unit[i]=o['pnl_liquido']/nocional
                    (ganhos if o['pnl_liquido']>0 else perdas).append(o['pnl_liquido'])
                np.testing.assert_allclose(10000+liquido,r['metricas']['capital_final'],atol=1e-7)
                d=descrever(p,y)
                d['operacao']={'n':len(ops),'compras':int((sinal>0).sum()),'vendas':int((sinal<0).sum()),
                              'pnl_sem_friccoes_quantidades_realizadas':bruto,'slippage_tick':friccao,
                              'comissao':comissao,'funding':funding,'pnl_liquido':liquido,
                              'custo_medio_bps_nocional':float(np.mean(custos_bps)),
                              'retorno_medio_liquido_por_nocional':float(np.mean(ret_op)),
                              'acerto_bruto_execucao':float(np.mean((sinal*re)[sinal!=0]>0)),
                              'acerto_liquido':len(ganhos)/len(ops),'ganho_medio_usdt':float(np.mean(ganhos)),
                              'perda_media_usdt':float(np.mean(perdas)),
                              'acerto_equilibrio_payoff_observado':abs(np.mean(perdas))/(np.mean(ganhos)+abs(np.mean(perdas)))}
                d['relacao_alvo_execucao']={'mae_retorno':float(np.mean(abs(y-re))), 'correlacao':correlacao(y,re),
                                          'sinais_diferentes':int((np.sign(y)!=np.sign(re)).sum())}
                d['faixas']={}
                for a,b in zip(FAIXAS[:-1],FAIXAS[1:]):
                    nome=f'{a:g}_{b:g}';ix=(abs(p)>a)&(abs(p)<=b)
                    d['faixas'][nome]=grupo(p,y,re,ix,ops,t)
                d['lados']={nome:grupo(p,y,re,sinal==lado,ops,t) for nome,lado in [('compras',1),('vendas',-1)]}
                d['trimestres']={}
                meses=pd.to_datetime(t,unit='ms',utc=True).month.to_numpy()
                for tri in range(4):
                    ix=(meses>3*tri)&(meses<=3*(tri+1))
                    d['trimestres'][str(tri+1)]={**descrever(p[ix],y[ix]),'pnl_liquido':float(diario_liq[ix].sum())}
                resultados[fase][versao][str(seed)]=d
                arrays[fase][versao][seed]=dict(p=p,y=y,t=t,sinal=sinal,re=re,liq=diario_liq,bruto=diario_bruto,unit=diario_unit)
        for seed in SEEDS:
            a=arrays[fase]['preco'][seed];b=arrays[fase]['retorno'][seed];grupos={}
            for sa in (-1,0,1):
                for sb in (-1,0,1):
                    ix=(a['sinal']==sa)&(b['sinal']==sb)
                    grupos[f'{sa}_para_{sb}']={'dias':int(ix.sum()),'delta_pnl_quantidades_realizadas':float((b['liq']-a['liq'])[ix].sum()),
                                             'delta_payoff_sem_custos_exposicao_unitaria_media':float(((b['sinal']-a['sinal'])*b['re'])[ix].mean()) if ix.any() else None}
            np.testing.assert_allclose(sum(v['delta_pnl_quantidades_realizadas'] for v in grupos.values()), b['liq'].sum()-a['liq'].sum(),atol=1e-7)
            transicoes[fase][str(seed)]=grupos
    # Sonda estatística somente: compensação constante estimada em V, não política promovida.
    sondas={}
    for versao in pastas:
        sondas[versao]={}
        for seed in SEEDS:
            v=arrays['validacao'][versao][seed];s=arrays['teste'][versao][seed]
            bias=float(np.mean(v['p']-v['y']))
            sondas[versao][str(seed)]={'vies_estimado_validacao':bias,
                'mse_teste_original':float(np.mean((s['p']-s['y'])**2)),
                'mse_teste_apos_subtrair_vies_validacao':float(np.mean((s['p']-bias-s['y'])**2))}
    destino=RAIZ/'dados/diagnosticos'/('calibracao_diaria_'+agora().replace(':','').replace('+','_'))
    destino.mkdir(parents=True,exist_ok=False)
    fonte=Path(__file__).resolve();fontes[fonte.relative_to(RAIZ).as_posix()]=sha256(fonte)
    saida={'utc':agora(),'natureza':'diagnostico_exploratorio_posterior_sem_treinos_ou_novas_carteiras',
           'execucoes':{k:v.relative_to(RAIZ).as_posix() for k,v in pastas.items()},
           'seeds':list(SEEDS),'faixas_absolutas_decimais':[0,.002,.005,.01,.02,None],
           'resultados':resultados,'transicoes':transicoes,'sonda_compensacao_constante':sondas,
           'limites':'2024 selecionou checkpoints; 2025 já consultado. Regressões/bins descrevem, não ajustam modelo ou filtro. Custos/PnL mantêm quantidades realizadas: não são backtest sem custos ou decomposição causal da seleção. Seeds compartilham mercado. Sem seleção de corte pelo lucro.',
           'entradas_sha256':entradas,'fontes_sha256':fontes}
    salvar_json(destino/'diagnostico.json',saida)
    desenhar(resultados,destino)
    for caminho,h in entradas.items():assert sha256(RAIZ/caminho)==h
    reg=RAIZ/'registros/retomada_alvo_diario/diagnosticos';reg.mkdir(exist_ok=True)
    salvar_json(reg/(destino.name+'.json'),{'utc':agora(),'pasta':destino.relative_to(RAIZ).as_posix(),
                'diagnostico_sha256':sha256(destino/'diagnostico.json'),'figura_sha256':sha256(destino/'calibracao_custos.png'),
                'fontes_sha256':fontes,'entradas_preservadas':True})
    print(destino)


def desenhar(resultados,destino):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axs=plt.subplots(2,2,figsize=(12,8))
    cores={'preco':'#3769ab','retorno':'#168272'}
    for col,fase in enumerate(('validacao','teste')):
        ax=axs[0,col]
        for versao,cor in cores.items():
            for j,seed in enumerate(SEEDS):
                d=resultados[fase][versao][str(seed)]
                bins=[d['faixas'][f'{a:g}_{b:g}'] for a,b in zip(FAIXAS[:-1],FAIXAS[1:])]
                bins=[v for v in bins if v['operacoes']>=10]
                ax.plot([v['previsao_abs_media']*100 for v in bins],
                        [v['retorno_alinhado_execucao_medio']*100 for v in bins],
                        marker='o',alpha=.75,color=cor,linestyle=['-','--',':'][j],label=f'{versao} / {seed}')
        ax.axhline(.2,color='#af7134',ls='--',lw=1,label='Fricção base ≈ 0,20% sem funding')
        ax.axhline(0,color='gray',lw=.7);ax.grid(alpha=.2)
        ax.set_title(('2024 · validação' if col==0 else '2025 · retrospectivo'))
        ax.set_xlabel('Magnitude prevista média (%)');ax.set_ylabel('Retorno bruto alinhado ao sinal (%)')
        ax=axs[1,col];nomes=['Sem fricções¹','Slippage/tick','Comissão','Funding','Líquido']
        for j,(versao,cor) in enumerate(cores.items()):
            ops=[resultados[fase][versao][str(seed)]['operacao'] for seed in SEEDS]
            vals=[np.mean([o[k] for o in ops])*s for k,s in [('pnl_sem_friccoes_quantidades_realizadas',1),('slippage_tick',-1),('comissao',-1),('funding',1),('pnl_liquido',1)]]
            ax.bar(np.arange(5)+(j-.5)*.35,vals,width=.35,color=cor,label=versao)
        ax.axhline(0,color='gray',lw=.7);ax.set_xticks(range(5),nomes,rotation=20);ax.set_ylabel('USDT · média das três seeds');ax.grid(axis='y',alpha=.2);ax.legend()
    axs[0,0].legend(fontsize=7,ncol=2)
    fig.suptitle('Diagnóstico: força dos sinais e atribuição de custos',fontsize=14)
    fig.text(.5,.012,'Faixas fixas; pontos com ≥10 operações por seed. ¹ Quantidades realizadas: não é nova carteira sem custos.\nLinhas conectam faixas para leitura; não são curva de calibração ajustada. Nenhum limiar foi selecionado.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.065,1,.95));fig.savefig(destino/'calibracao_custos.png',dpi=160);plt.close(fig)


if __name__=='__main__': executar()
