"""Revisão posterior das53previsões: médias, estabilidade e apresentação; não treina."""
import math
import shutil
from uuid import uuid4
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,agora,ler_json,salvar_json,sha256,conferir_arquivos
from treinamento.preservacao import conferir
from avaliacao.publicacao import conferir_previsoes


def estatisticas(rows):
    ajustes=[ler_json(RAIZ/x['tentativa_origem']/'resultado.json') for x in rows]
    pred={}
    for b in ('validacao','teste'):
        ms=[x['metricas'][b] for x in rows]
        pred[b]={k:float(np.mean([m[k] for m in ms])) for k in ('mse','rmse','mae','habilidade_mse','acuracia_direcional','acerto_balanceado_direcional','vies')}
        pred[b]['mse_desvio_seeds']=float(np.std([m['mse'] for m in ms],ddof=1))
        pred[b]['seeds_melhores_naive']=sum(m['habilidade_mse']>0 for m in ms)
    spot={}
    for perfil in ('base','agravado','bruto_mesmos_sinais'):
        vs=[x['spot'][perfil] for x in rows]
        assert all(v['retorno_auditavel'] and v['risco_auditavel'] for v in vs)
        spot[perfil]={k:float(np.mean([v[k] for v in vs])) for k in ('retorno_liquido','drawdown','entradas_planejadas','custos_observados','minutos_expostos_planejados')}
        spot[perfil]['retorno_desvio_seeds']=float(np.std([v['retorno_liquido'] for v in vs],ddof=1));spot[perfil]['seeds_lucrativas']=sum(v['retorno_liquido']>0 for v in vs)
    treino={k:float(np.mean([x[k] for x in ajustes])) for k in ('epoca_selecionada','epocas_executadas','segundos')}
    return {'n_seeds':len(rows),'predicao':pred,'spot':spot,'treinamento':treino}


def figura(grupos,pasta):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    pasta.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(2,2,figsize=(12,8));x=np.arange(4);cores={'referencia':'#356C91','candidata':'#CF8C38'}
    paineis=[(axes[0,0],'Validação 2024: habilidade contra Naive (%)',lambda g:100*g['predicao']['validacao']['habilidade_mse'],(-.1,.4),2),
        (axes[0,1],'Teste 2025: habilidade contra Naive (%)',lambda g:100*g['predicao']['teste']['habilidade_mse'],(-2.1,.2),2),
        (axes[1,0],'Spot: retorno líquido médio (%)',lambda g:100*g['spot']['base']['retorno_liquido'],(-23,2),2),
        (axes[1,1],'Teste: dispersão do MSE entre seeds (×10⁻⁶)',lambda g:1e6*g['predicao']['teste']['mse_desvio_seeds'],(0,10),2)]
    for ax,titulo,extrair,limites,casas in paineis:
        for j,nome in enumerate(('referencia','candidata')):
            vals=[extrair(grupos[str(n)][nome]) for n in (8,16,32,64)]
            barras=ax.bar(x+(j-.5)*.36,vals,width=.34,color=cores[nome],zorder=3)
            for b,v in zip(barras,vals):
                ax.annotate(f'{v:.{casas}f}'.replace('.',','),(b.get_x()+b.get_width()/2,v),xytext=(0,4 if v>=0 else -12),textcoords='offset points',ha='center',fontsize=8.5)
        ax.set_title(titulo,loc='left',fontsize=11,pad=12);ax.set_xticks(x,[f'Estado {n}' for n in (8,16,32,64)]);ax.set_ylim(*limites)
        ax.axhline(0,color='#555',linewidth=.8);ax.grid(axis='y',color='#E3E7EA');ax.set_axisbelow(True)
    fig.suptitle('Reduzir a taxa mudou precisão, estabilidade e operação?',x=.06,y=.98,ha='left',fontsize=16,fontweight='bold')
    fig.legend(handles=[Patch(color=cores['referencia'],label='Taxa 0,0002 · referência'),Patch(color=cores['candidata'],label='Taxa 0,0001 · candidata')],loc='upper left',bbox_to_anchor=(.055,.93),ncol=2,frameon=False)
    fig.text(.06,.025,'Seis seeds por combinação · períodos retrospectivos · mesma política Spot · médias individuais, não ensemble · barras sem IC',fontsize=9,color='#555')
    fig.subplots_adjust(left=.07,right=.98,top=.82,bottom=.11,wspace=.21,hspace=.44)
    saidas={}
    for ext in ('png','pdf'):
        p=pasta/f'comparacao_taxas.{ext}';fig.savefig(p,dpi=170,bbox_inches='tight',facecolor='white');saidas[p.relative_to(RAIZ).as_posix()]=sha256(p)
    plt.close(fig);return saidas


def analisar():
    reg=RAIZ/'registros/taxa_aprendizado';ptr=ler_json(reg/'execucao.json');base=RAIZ/ptr['pasta'];fim=ler_json(reg/'fechamento.json')
    assert fim['situacao']=='concluido_conferido' and not ler_json(base/'processo.json')['ativo']
    conferir_arquivos(base,{'congelamento.json':ptr['congelamento_sha256']});f=ler_json(base/'congelamento.json');cfg=f['contrato']['configuracoes']['8']
    conferir_arquivos(RAIZ,f['contrato']['fontes']);conferir_arquivos(base/'fontes',f['contrato']['fontes'])
    for p in (fim['auditoria'],fim['comparacao']):conferir_arquivos(RAIZ,{p['arquivo']:p['sha256']})
    pp=ler_json(base/'publicacao.json');pub=base/pp['pasta'];conferir_arquivos(pub,{'manifesto.json':pp['manifesto_sha256']});conferir_arquivos(pub,ler_json(pub/'manifesto.json')['arquivos'])
    r=ler_json(pub/'resultados.json');assert r['novos']==24 and r['herdados']==29 and len(r['por_ajuste'])==53
    partes={b:pd.read_parquet(RAIZ/cfg['entradas_pasta']/f'{b}.parquet') for b in ('validacao','teste','operacional')}
    conferencias={}
    for chave,item in r['por_ajuste'].items():
        t=RAIZ/item['tentativa_origem'];conferir(t);rr=ler_json(t/'resultado.json');assert rr['metricas']==item['metricas']
        conferencias[chave]={b:conferir_previsoes(pd.read_parquet(t/f'previsoes_{b}.parquet'),partes[b],rr['metricas'].get(b)) for b in partes}
    grupos={};efeitos={}
    for nome,seeds in [('tres_seeds',[17,42,2026]),('seis_seeds',[17,42,2026,7,123,31415])]:
        grupos[nome]={}
        for n in (8,16,32,64):
            a=[r['por_ajuste'][f'estado{n}_{s}'] for s in seeds];b=[r['por_ajuste'][f'taxa0001_estado{n}_{s}'] for s in seeds]
            grupos[nome][str(n)]={'referencia':estatisticas(a),'candidata':estatisticas(b)}
            if nome=='seis_seeds':
                efeitos[str(n)]={p:{'seeds_melhoraram':sum(v['metricas'][p]['mse']<o['metricas'][p]['mse'] for o,v in zip(a,b)),
                    'diferencas_por_seed':{str(s):v['metricas'][p]['mse']-o['metricas'][p]['mse'] for s,o,v in zip(seeds,a,b)}} for p in ('validacao','teste')}
                for parte in ('validacao','teste'):
                    for rotulo in ('referencia','candidata'):
                        m=grupos[nome][str(n)][rotulo]['predicao'][parte];publicado=r['medias'][parte][f'{rotulo}_estado{n}']['metricas']
                        assert math.isclose(m['mse'],publicado['mse'],rel_tol=1e-13)
    antes=ler_json(reg/'preservacao_antes.json');conferir_arquivos(RAIZ,antes['arquivos'])
    destino=reg/'revisoes'/uuid4().hex;destino.mkdir(parents=True)
    relatorio=RAIZ/'docs/resultados_taxa_aprendizado.md';shutil.copy2(relatorio,destino/'relatorio_automatico.md')
    ref=RAIZ/'dados/experimentos/ohlcv_modular_ab5baf3eab3a2e66d8b2/publicacoes/tentativa_001';conferir_arquivos(ref,ler_json(ref/'manifesto.json')['arquivos']);bench=ler_json(ref/'resultados.json')['referencias_economicas']
    resultado={'utc':agora(),'execucao':ptr['id'],'natureza':'análise posterior; sem treino, nova seleção, recarga CUDA ou alteração de publicação','fonte_publicacao':pub.relative_to(RAIZ).as_posix(),'manifesto_sha256':pp['manifesto_sha256'],'grupos':grupos,'efeitos':efeitos,'contrastes':r['contrastes'],'referencias_economicas_herdadas':bench,'verificacao_metricas':conferencias,'fontes_anteriores_inalteradas':len(antes['arquivos']),'limites':['Checkpoint/capacidade/recarga atestados pelo fechamento anterior; aqui hashes e métricas por origem conferidos.','Redução da dispersão observada não é teste formal de variâncias.','Médias de retorno/drawdown não são carteira; sem IC financeiro.','Recorte de três seeds e diagnóstico de concentração são posteriores; não substituem critério de seis seeds.']}
    salvar_json(destino/'analise.json',resultado);shutil.copy2(__file__,destino/'verificador.py')
    figs=figura(grupos['seis_seeds'],RAIZ/f'docs/figuras/taxa_aprendizado_{ptr["id"]}')
    salvar_json(destino/'figuras.json',{'fonte_sha256':sha256(destino/'analise.json'),'arquivos':figs})
    salvar_json(destino/'manifesto.json',{'arquivos':{p.name:sha256(p) for p in destino.iterdir() if p.is_file()}})
    pointer={'arquivo':(destino/'analise.json').relative_to(RAIZ).as_posix(),'sha256':sha256(destino/'analise.json')};salvar_json(reg/'analise_interpretativa_atual.json',pointer)
    return pointer


if __name__=='__main__':print(analisar())
