"""Diagnóstico posterior: sinal de queda versus PnL das posições, sem backtest novo."""
import math
from pathlib import Path
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,agora,ler_json,salvar_json,sha256,conferir_arquivos


def sinais(q):
    r=q.previsao.to_numpy(float);y=q.alvo.to_numpy(float)
    negativo=r<0;positivo=r>0;queda=y<0;alta=y>0
    def prop(a,b):return float(a[b].mean()) if b.any() else None
    return {'n':len(q),'previsoes_queda':int(negativo.sum()),'previsoes_alta':int(positivo.sum()),
        'quedas_reais':int(queda.sum()),'altas_reais':int(alta.sum()),
        'precisao_queda':prop(queda,negativo),'precisao_alta':prop(alta,positivo),
        'recall_queda':prop(negativo,queda),'recall_alta':prop(positivo,alta),
        'retorno_real_medio_quando_preve_queda':float(np.expm1(y[negativo]).mean()) if negativo.any() else None,
        'retorno_real_medio_quando_preve_alta':float(np.expm1(y[positivo]).mean()) if positivo.any() else None,
        'retorno_medio':float(np.expm1(y).mean()),'taxa_queda_natural':float(queda.mean()),
        'soma_retorno_quando_queda':float(np.expm1(y[negativo]).sum()),
        'soma_retorno_quando_alta':float(np.expm1(y[positivo]).sum()),
        'acertos_queda':int((negativo&queda).sum()),'acertos_alta':int((positivo&alta).sum())}


def decompor(ordens,eventos,resumo):
    partes={lado:{'preco':0.,'comissao':0.,'slippage':0.,'funding':0.,'dias':0,'dias_sinal_oposto':0,'preco_sinal_oposto':0.,'dias_sinal_correto':0} for lado in ['comprada','vendida']}
    for i,o in enumerate(ordens):
        anterior=o['antes']['quantidade'];dq=o['delta_executado']
        volume=abs(dq)
        if volume:
            if dq>0:
                curta=min(max(-anterior,0.),volume);longa=volume-curta
            else:
                longa=min(max(anterior,0.),volume);curta=volume-longa
            for lado,v in [('comprada',longa),('vendida',curta)]:
                partes[lado]['comissao']+=o['comissao']*v/volume
                partes[lado]['slippage']+=o['slippage']*v/volume
        q=o['depois']['quantidade']
        if i+1<len(ordens) and abs(q)>1e-12:
            lado='comprada' if q>0 else 'vendida';z=partes[lado]
            movimento=ordens[i+1]['preco_meio']-o['preco_meio'];pnl=q*movimento
            z['preco']+=pnl;z['dias']+=1
            if q*o['previsao']<0:z['dias_sinal_oposto']+=1;z['preco_sinal_oposto']+=pnl
            if o['previsao']*movimento>0:z['dias_sinal_correto']+=1
    for e in eventos:
        lado='comprada' if e['btc']>0 else 'vendida';partes[lado]['funding']+=e['fluxo']
    ultima=ordens[-1];q=ultima['depois']['quantidade']
    if abs(q)>1e-12:partes['comprada' if q>0 else 'vendida']['preco']+=q*(ultima['preco_mark']-ultima['preco_meio'])
    for x in partes.values():x['liquido']=x['preco']-x['comissao']-x['slippage']+x['funding']
    assert math.isclose(sum(x['liquido'] for x in partes.values()),resumo['capital_final']-resumo['capital_inicial'],abs_tol=1e-7)
    return partes


def executar():
    ptr=ler_json(RAIZ/'registros/smart_mercados/execucao.json');p=RAIZ/ptr['pasta']
    assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    f=ler_json(p/'congelamento.json')['assinatura'];conferir_arquivos(RAIZ,f['fontes'])
    fim=ler_json(p/'fechamento.json');assert fim['situacao']=='concluido_conferido'
    pub=p/'publicacao';assert sha256(pub/'manifesto.json')==fim['publicacao_sha256']
    conferir_arquivos(pub,ler_json(pub/'manifesto.json')['arquivos'])
    res=ler_json(pub/'resultados.json');predicoes=[];carteiras=[];dados=[];origens={}
    for chave,v in f['series'].items():
        b,modelo,seed=chave.split('/');s=RAIZ/v['pasta'];assert sha256(s/'conclusao.json')==v['conclusao_sha256']
        manifesto=ler_json(s/'conclusao.json');conferir_arquivos(s,{'previsoes_teste.parquet':manifesto['arquivos']['previsoes_teste.parquet']})
        q=pd.read_parquet(s/'previsoes_teste.parquet');t=pd.DatetimeIndex(q.origem_utc);d=q.loc[t.hour==0].reset_index(drop=True)
        for frequencia,z in [('horaria',q),('diaria',d)]:predicoes.append(dict(bloco=b,modelo=modelo,seed=int(seed),frequencia=frequencia,**sinais(z)))
        dados.append(d.assign(bloco=b,modelo=modelo,seed=int(seed)))
        for braco in ['futuro','futuro_bilateral']:
            pasta=p/'carteiras'/b/modelo/seed/'smart'/braco/'iguais'
            mf=ler_json(pasta/'manifesto.json');conferir_arquivos(pasta,mf['arquivos'])
            o=ler_json(pasta/'ordens.json');ev=ler_json(pasta/'funding.json');r=ler_json(pasta/'resumo.json')
            assert len(o)==len(d)+1
            np.testing.assert_allclose([x['previsao'] for x in o[:-1]],d.previsao,rtol=0,atol=0)
            partes=decompor(o,ev,r)
            for lado,x in partes.items():carteiras.append(dict(bloco=b,modelo=modelo,seed=int(seed),braco=braco,lado=lado,**x))
            # Atribuição no horizonte real de execução, sem fingir posição nova hipotética.
            if braco=='futuro_bilateral':
                obs=np.array([x['preco_meio'] for x in o]);d2=d.copy();d2['alvo']=np.log(obs[1:]/obs[:-1])
                predicoes.append(dict(bloco=b,modelo=modelo,seed=int(seed),frequencia='futuro_24h_execucao',**sinais(d2)))
        if b not in origens:origens[b]={'dias':len(d),'taxa_queda':float((d.alvo<0).mean()),'retorno_medio':float(np.expm1(d.alvo).mean())}
    sq=pd.DataFrame(predicoes);cq=pd.DataFrame(carteiras)
    # Contagens agrupadas: dias repetidos por seed não são amostras independentes.
    agregados=[]
    for (modelo,freq),z in sq.groupby(['modelo','frequencia']):
        nneg=int(z.previsoes_queda.sum());npos=int(z.previsoes_alta.sum())
        agregados.append({'modelo':modelo,'frequencia':freq,'n':int(z.n.sum()),'previsoes_queda':nneg,'previsoes_alta':npos,
            'precisao_queda_agrupada':float(z.acertos_queda.sum()/nneg) if nneg else None,
            'precisao_alta_agrupada':float(z.acertos_alta.sum()/npos) if npos else None,
            'retorno_quando_queda_agrupado':float(z.soma_retorno_quando_queda.sum()/nneg) if nneg else None,
            'retorno_quando_alta_agrupado':float(z.soma_retorno_quando_alta.sum()/npos) if npos else None,
            'recall_queda_media_celulas':float(z.recall_queda.mean()),'recall_alta_media_celulas':float(z.recall_alta.mean()),
            'celulas_sem_previsao_queda':int((z.previsoes_queda==0).sum()),'celulas_sem_previsao_alta':int((z.previsoes_alta==0).sum())})
    medias=cq.groupby(['modelo','braco','lado']).mean(numeric_only=True).reset_index().drop(columns='seed')
    blocos=cq.groupby(['bloco','modelo','braco','lado']).mean(numeric_only=True).reset_index().drop(columns='seed')
    sinais_blocos=[]
    for (b,modelo),z in sq[sq.frequencia=='diaria'].groupby(['bloco','modelo']):
        neg=int(z.previsoes_queda.sum());pos=int(z.previsoes_alta.sum())
        sinais_blocos.append({'bloco':b,'modelo':modelo,'previsoes_queda':neg,'previsoes_alta':pos,
            'precisao_queda':float(z.acertos_queda.sum()/neg) if neg else None,
            'precisao_alta':float(z.acertos_alta.sum()/pos) if pos else None,
            'retorno_quando_queda':float(z.soma_retorno_quando_queda.sum()/neg) if neg else None})
    destino=RAIZ/'registros/smart_mercados/diagnosticos'/agora().replace(':','').replace('+','_');destino.mkdir(parents=True,exist_ok=False)
    saida={'utc':agora(),'execucao':ptr,'status':'conferido','carteiras_reconciliadas':128,'series':64,'agregados_sinais':agregados,
        'sinais_por_celula':predicoes,'sinais_por_bloco':sinais_blocos,'decomposicao_por_carteira':carteiras,'medias_componentes':medias.to_dict('records'),'componentes_por_bloco':blocos.to_dict('records'),'mercado_por_bloco':origens,
        'limites':'Diagnostico posterior sem treino/backtest novo; precisao agrupada pondera sinais e nao equivale a media de taxas por seed/bloco; seeds compartilham dias; atribuicao contabil nao e contrafactual causal; sem IC confirmatorio.',
        'achado_politica':'Smart bilateral tambem acelera reducao de posicao comprada: d<0 usa d*(0.95E+qP)/P versus d*q. Diferenca entre bracos nao isola apenas PnL dos shorts.'}
    salvar_json(destino/'diagnostico.json',saida)
    shutil_source=destino/'fonte_analise.py';shutil_source.write_bytes(Path(__file__).read_bytes())
    salvar_json(destino/'manifesto.json',{'arquivos':{x.name:sha256(x) for x in destino.iterdir() if x.is_file()},'origem_publicacao_sha256':sha256(pub/'manifesto.json')})
    print('RECIBO',destino.relative_to(RAIZ).as_posix())
    for x in agregados:
        if x['frequencia']!='horaria':print('SINAIS',x)
    print('ATRIBUICAO',medias.to_dict('records'))
    print('BLOCOS_SINAIS',sinais_blocos)

if __name__=='__main__':executar()
