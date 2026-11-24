"""Leitura dos sete resultados diários e quatro referências lineares auxiliares."""
import json
import shutil
import traceback
from pathlib import Path
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256, identidade, conferir_arquivos
from entradas_modelo.padronizacao_diaria import preparar_com_escalas
from .medidas import medir, ridge


def executar():
    reg=RAIZ/'registros/taxa_diaria'; ponteiro=reg/'diagnostico.json'
    if ponteiro.exists(): raise RuntimeError('Diagnóstico já publicado; não repetir.')
    custos=ler_json(RAIZ/'registros/custos_vigentes/vigente.json'); cp=RAIZ/custos['pasta']
    assert sha256(cp/'publicacao_manifesto.json')==custos['manifesto_sha256']
    manifesto=ler_json(cp/'publicacao_manifesto.json')
    for nome in ('publicacao/diarias.json','publicacao/carteiras.json'):
        assert sha256(cp/nome)==manifesto['arquivos'][nome]
    diarias=ler_json(cp/'publicacao/diarias.json')
    fontes={}; entradas={}
    for pacote in ('analises/etapas/fechamento_diario','entradas_modelo','infraestrutura'):
        for p in (RAIZ/'codigo'/pacote).rglob('*.py'): fontes[p.relative_to(RAIZ).as_posix()]=sha256(p)
    fontes['docs/protocolo_taxa_diaria.md']=sha256(RAIZ/'docs/protocolo_taxa_diaria.md')
    itens={}; moedas={}
    for base in diarias:
        p=RAIZ/base; pai=p
        while not (pai/'congelamento.json').exists(): pai=pai.parent
        f=ler_json(pai/'congelamento.json')
        entradas[(pai/'congelamento.json').relative_to(RAIZ).as_posix()]=sha256(pai/'congelamento.json')
        if 'moedas' in f:
            moeda=next(m for m in f['moedas'] if m in p.parts); a=f['moedas'][moeda]
            c=a['configuracao']; diario=RAIZ/a['mercado']['pasta']/'diario.parquet'
            moedas[moeda]=(base,c,diario,a['escalas'])
        else:
            c=f['configuracao']; moeda='BTCUSDT'
            if 'padronizacao_diaria_' in base:
                moedas[moeda]=(base,c,RAIZ/f['diario']['pasta']/'diario.parquet',f['escalas'])
        itens[base]=(c,moeda)
        for fase in ('validacao','teste'):
            for seed in c['seeds']:
                arq=p/'publicacao/previsoes'/f'{fase}_{seed}.npz'
                fecho=ler_json(p/'fechamento.json')
                assert sha256(arq)==fecho['arquivos'][arq.relative_to(p).as_posix()]
                entradas[arq.relative_to(RAIZ).as_posix()]=sha256(arq)
    for _,_,diario,_ in moedas.values(): entradas[diario.relative_to(RAIZ).as_posix()]=sha256(diario)
    plano={'utc':agora(),'fontes':fontes,'entradas':entradas,'custos_vigentes':custos,
           'metodo':'Diagnóstico retrospectivo; mesmos sete estudos, três seeds; MSE decomposto, magnitude, lado e trimestre; quatro médias e Ridge treinados só emT, lambda escolhido emV.',
           'grade_ridge':[.01,.1,1.,10.,100.], 'faixas':[0,.002,.005,.01],
           'sem_novo_treino_neural':True,'sem_calibrar_filtro':True}
    codigo=identidade(plano)[:20]; p=RAIZ/'dados/diagnosticos'/f'fechamento_diario_{codigo}'
    p.mkdir(parents=True,exist_ok=False); salvar_json(p/'plano.json',plano)
    for nome in fontes:
        dst=p/'fontes'/nome; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(RAIZ/nome,dst)
    try:
        linhas=[]
        for base,(c,moeda) in itens.items():
            for fase in ('validacao','teste'):
                for seed in c['seeds']:
                    z=np.load(RAIZ/base/'publicacao/previsoes'/f'{fase}_{seed}.npz')
                    y=z['y']/z['ultimo_close']-1; prev=z['previsoes']/z['ultimo_close']-1
                    faixas=[]; limites=[0.,.002,.005,.01,float('inf')]
                    for a,b in zip(limites[:-1],limites[1:]):
                        ix=(abs(prev)>=a)&(abs(prev)<b)
                        faixas.append({'minimo':a,'maximo':b if np.isfinite(b) else None,'n':int(ix.sum()),
                                       'metricas':medir(y[ix],prev[ix]) if ix.any() else None})
                    datas=pd.to_datetime(z['origens_ms'],unit='ms',utc=True); trimestres={}
                    for t in range(1,5):
                        ix=datas.quarter==t
                        if ix.any():trimestres[str(t)]=medir(y[ix],prev[ix])
                    fin=next(x['metricas'] for x in diarias[base]['carteiras'] if x['fase']==fase and x['unidade']==str(seed) and x['cenario']=='base')
                    linhas.append({'estudo':base,'moeda':moeda,'fase':fase,'seed':seed,'metricas':medir(y,prev),
                                   'faixas':faixas,'trimestres':trimestres,'operacao_vigente':fin})
        auxiliares=[]; assert len(moedas)==4
        for moeda,(base,c,diario,esc) in moedas.items():
            d,escalas=preparar_com_escalas(pd.read_parquet(diario),c); assert escalas==esc
            (w,b),sel=ridge(d['treino']['x'],d['treino']['y'],d['validacao']['x'],d['validacao']['y'])
            media=float(np.mean(d['treino']['y'])); salvar_json(p/f'linear_{moeda}.json',{'selecao':sel,'pesos':w.tolist(),'intercepto':b,'media_treino':media,'escala':escalas})
            for fase in ('validacao','teste'):
                z=d[fase]; ref=np.load(RAIZ/base/'publicacao/previsoes'/f'{fase}_42.npz')
                for k in ('origens_ms','fim_alvo_ms','ultimo_close'):np.testing.assert_array_equal(z[k],ref[k])
                np.testing.assert_array_equal(z['preco_alvo'],ref['y'])
                preds={'naive':np.zeros(len(z['y'])),'media_treino':np.full(len(z['y']),media),
                       'ridge':z['x'].reshape(len(z['y']),-1).astype(float)@w+b}
                np.savez_compressed(p/f'auxiliares_{moeda}_{fase}.npz',**preds,alvo=z['y'],origens_ms=z['origens_ms'])
                for nome,prev in preds.items():auxiliares.append({'moeda':moeda,'fase':fase,'modelo':nome,'metricas':medir(z['y'],prev)})
        resumo={'utc':agora(),'linhas':linhas,'auxiliares':auxiliares,'cobertura':{'modelos_neurais_herdados':21,'linhas':len(linhas),
                'ajustes_medias':4,'candidatos_ridge':20,'ridge_selecionados':4,'novos_ajustes_neurais':0},
                'limites':'Diagnóstico retrospectivo; faixas e trimestres descritivos; Ridge não autoriza novos filtros nem representa nova arquitetura Mamba. Seeds não são mercados independentes.'}
        assert len(linhas)==42 and len(auxiliares)==24
        salvar_json(p/'resultados.json',resumo)
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig,axs=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
        for moeda in sorted(moedas):
            base=moedas[moeda][0]
            rr=[r for r in linhas if r['estudo']==base and r['fase']=='teste']
            valores=[np.mean([r['metricas']['habilidade_naive'] for r in rr])*100]
            valores += [next(r['metricas']['habilidade_naive'] for r in auxiliares if r['moeda']==moeda and r['fase']=='teste' and r['modelo']==nome)*100 for nome in ('media_treino','ridge')]
            axs[0].plot(['Mamba padronizado','Média do treino','Ridge'],valores,marker='o',label=moeda.replace('USDT',''))
        axs[0].axhline(0,color='black',lw=1);axs[0].set_ylabel('Redução do MSE versus Naive (%)')
        axs[0].set_title('Previsão em 2025 — retrospectivo');axs[0].legend()
        nomes=[];valores=[]
        for base,(c,moeda) in itens.items():
            if moeda!='BTCUSDT':continue
            nomes.append('Preço' if 'cryptomamba_reproducivel_' in base else 'Sem decay' if 'sem_penalizacao_' in base else 'Padronizado' if 'padronizacao_' in base else 'Retorno')
            valores.append(np.mean([r['metricas']['razao_desvios'] for r in linhas if r['estudo']==base and r['fase']=='teste']))
        axs[1].bar(nomes,valores,color='#366b91');axs[1].axhline(1,color='black',lw=1,ls='--')
        axs[1].set_ylabel('Desvio da previsão / desvio do retorno real')
        axs[1].set_title('BTC: dispersão dos sinais — média de 3 seeds')
        for ax in axs:ax.grid(axis='y',alpha=.2)
        fig.savefig(p/'diagnostico.png',dpi=180);plt.close(fig)
        conferir_arquivos(RAIZ,entradas); conferir_arquivos(RAIZ,fontes)
        salvar_json(p/'manifesto.json',{'utc':agora(),'id':codigo,'situacao':'concluido_conferido',
                   'arquivos':{a.relative_to(p).as_posix():sha256(a) for a in p.rglob('*') if a.is_file()}})
        salvar_json(ponteiro,{'id':codigo,'pasta':p.relative_to(RAIZ).as_posix(),'manifesto_sha256':sha256(p/'manifesto.json')})
        print(json.dumps({'diagnostico':str(p),'cobertura':resumo['cobertura']}),flush=True)
    except BaseException:
        salvar_json(p/'incidente.json',{'utc':agora(),'erro':traceback.format_exc()});raise


if __name__=='__main__': executar()
