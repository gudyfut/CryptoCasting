"""Auditoria dos artefatos e rotulador de referência independente do kernel numba."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .arquivos import ler_json, salvar_json, sha256
from .metricas import calcular


def auditar_financeiro(previsoes,minutos,primeiro_minuto,limites,resumo,ordens,curva,
                      *,filtro=True,agravado=False,superior_ambiguo=False):
    """Reconstrói decisões e caixa sem chamar o simulador nem sua fórmula auxiliar."""
    taxa,slip=(.002,.001) if agravado else (.001,.0005)
    inicio=int(limites[2].timestamp()//60)-primeiro_minuto
    fim=int(limites[3].timestamp()//60)-primeiro_minuto
    esperado=np.full(fim-inicio,10000.,dtype=float)
    patrimonio=10000.;livre=-1;indice=0;invalidacao=None
    for r in previsoes.itertuples(index=False):
        e=int(r.entrada_indice)
        if e-1<=livre or e<inicio or e+r.horizonte*60>=fim:
            continue
        fator=.9995*.999/(1.0005*1.001)
        ganho=np.exp(r.distancia)*fator-1
        perda=np.exp(-r.distancia)*fator-1
        if filtro and (r.p2<.6 or r.p2*ganho+(1-r.p2)*perda<=0):
            continue
        y,s,b,amb=rotulo_referencia(minutos,e,r.distancia,r.horizonte)
        if y<0:
            invalidacao=r.origem_utc.isoformat();esperado[e-inicio:]=np.nan
            break
        if indice>=len(ordens):
            raise ValueError('Operação elegível ausente no livro.')
        ordem=ordens.iloc[indice]
        a=float(minutos[e,0])
        if amb and superior_ambiguo:
            b=a*np.exp(r.distancia);y=2
        fracao=min(1.,.01/-perda)
        q=patrimonio*fracao/(a*(1+slip)*(1+taxa))
        caixa=patrimonio*(1-fracao)
        depois=caixa+q*b*(1-slip)*(1-taxa)
        if ordem.origem_utc!=r.origem_utc or ordem.entrada_utc!=r.entrada_utc or ordem.saida_utc!=r.saida_utc:
            raise ValueError('Timestamps do livro divergem da origem/execução.')
        for chave,valor in {'preco_entrada':a,'preco_saida':b,'quantidade':q,'fracao':fracao,
                    'capital_antes':patrimonio,'capital_depois':depois,'lucro':depois-patrimonio,
                    'classe':y,'taxas':q*(a*(1+slip)+b*(1-slip))*taxa,
                    'slippage':q*(a+b)*slip}.items():
            if not np.isclose(ordem[chave],valor,rtol=1e-10,atol=1e-10):
                raise ValueError(f'Contabilidade divergente: {chave}')
        esperado[e-inicio:s-inicio]=caixa+q*minutos[e:s,3]*(1-slip)*(1-taxa)
        esperado[s-inicio:]=depois
        conhecido=s if y==1 or minutos[s,0]>=a*np.exp(r.distancia) or minutos[s,0]<=a*np.exp(-r.distancia) else s+1
        if conhecido!=ordem.saida_conhecida_indice:
            raise ValueError('Instante conhecido da saída divergiu.')
        patrimonio=depois;livre=conhecido;indice+=1
    if indice!=len(ordens) or not np.allclose(esperado,curva.patrimonio,rtol=1e-10,atol=1e-9,equal_nan=True):
        raise ValueError('Livro ou curva não corresponde às decisões causais.')
    if invalidacao:
        if resumo['status']!='nao_auditavel' or resumo['invalidacao']['origem_utc']!=invalidacao or resumo['retorno_liquido'] is not None:
            raise ValueError('Lacuna foi omitida da avaliação financeira.')
    else:
        if resumo['status']!='auditavel' or resumo['operacoes']!=indice:
            raise ValueError('Status financeiro ou contagem divergente.')
        comparar_json(resumo['capital_final'],patrimonio,'capital_final')
        comparar_json(resumo['retorno_liquido'],patrimonio/10000.-1,'retorno_liquido')
        picos=np.maximum.accumulate(np.r_[10000.,esperado])[1:]
        comparar_json(resumo['drawdown_maximo'],float((1-esperado/picos).max()),'drawdown')
    return {'operacoes_recalculadas':indice,'curva_recalculada':True,'lacuna_identificada':invalidacao}


def rotulo_referencia(minutos,e,d,h):
    v=e+h*60
    if e>=len(minutos) or not np.isfinite(minutos[e,0]) or minutos[e,5]<=0:
        return -1,-1,np.nan,False
    a=minutos[e,0];u=a*np.exp(d);l=a*np.exp(-d)
    trecho=minutos[e:min(v,len(minutos))]
    finito=np.isfinite(trecho[:,:3]).all(axis=1)
    evento=((trecho[:,1]>=u)|(trecho[:,2]<=l))&(trecho[:,5]>0)&finito
    candidatos=np.flatnonzero(evento|~finito)
    if len(candidatos):
        k=int(candidatos[0]);j=e+k
        if not finito[k]:
            return -1,-1,np.nan,False
        o,alto,baixo=trecho[k,:3]
        if o>=u:
            return 2,j,o,False
        if o<=l:
            return 0,j,o,False
        if baixo<=l:
            return 0,j,l,bool(alto>=u)
        return 2,j,u,False
    if v>=len(minutos) or not np.isfinite(minutos[v,0]) or minutos[v,5]<=0:
        return -1,-1,np.nan,False
    return 1,v,minutos[v,0],False


def comparar_json(a,b,caminho=''):
    if isinstance(a,dict):
        if set(a)!=set(b):
            raise ValueError(f'Campos de métricas divergentes: {caminho}')
        for k in a:
            comparar_json(a[k],b[k],caminho+'/'+k)
    elif isinstance(a,list):
        if len(a)!=len(b):
            raise ValueError(f'Comprimento divergente: {caminho}')
        for i,(x,y) in enumerate(zip(a,b)):
            comparar_json(x,y,caminho+f'/{i}')
    elif isinstance(a,(float,int)) and not isinstance(a,bool):
        if not np.isclose(a,b,rtol=1e-10,atol=1e-12):
            raise ValueError(f'Métrica divergiu: {caminho}: {a} != {b}')
    elif a!=b:
        raise ValueError(f'Métrica divergiu: {caminho}')


def auditar_celula(pasta,blocos,horas,minutos,escalas,celula,limites):
    evidencias={}
    # Recalcular os desfechos sem chamar a função usada para fabricar o dataset.
    uniao=pd.concat([blocos['teste'],blocos['operacional']]).drop_duplicates('origem_utc')
    for r in uniao.itertuples(index=False):
        y,s,p,amb=rotulo_referencia(minutos,int(r.entrada_indice),float(r.distancia),celula['horizonte'])
        if y!=r.classe or (y>=0 and (s!=r.saida_indice or not np.isclose(p,r.preco_saida,rtol=1e-12) or amb!=r.ambiguo)):
            raise ValueError(f'Rotulador independente divergiu em {r.origem_utc}')
    evidencias['rotulos_recalculados']=len(uniao)
    # Recalcular o resumo de risco e as cinco features diretamente dos minutos.
    indices=np.unique(np.linspace(0,len(uniao)-1,min(32,len(uniao)),dtype=int))
    for i in indices:
        r=uniao.iloc[i];fim=int(r.entrada_indice)-1
        closes=minutos[fim-169*60+59:fim:60,3]
        sigma=np.std(np.diff(np.log(closes)),ddof=1)
        if not np.isclose(sigma,r.sigma,rtol=1e-8,atol=1e-12):
            raise ValueError('Volatilidade não corresponde ao passado na origem.')
        ultimo=minutos[fim-60:fim]
        anterior=minutos[fim-61,3]
        x=[np.log(ultimo[0,0]/anterior),np.log(ultimo[:,1].max()/anterior),
           np.log(ultimo[:,2].min()/anterior),np.log(ultimo[-1,3]/anterior),np.log1p(ultimo[:,4].sum())]
        from .configuracao import COLUNAS
        if not np.allclose(horas.loc[int(r.indice_hora),list(COLUNAS)].to_numpy(float),x,rtol=1e-12,atol=1e-12):
            raise ValueError('Features não correspondem aos minutos anteriores à origem.')
    evidencias['origens_features_recalculadas']=len(indices)
    referencia=ler_json(pasta/'referencia_constante.json')
    frequencias=(np.bincount(blocos['treino'].classe,minlength=3)+.5)/(len(blocos['treino'])+1.5)
    comparar_json(referencia['probabilidades'],frequencias.tolist(),'frequencias_treino')
    comparar_json(referencia['metricas_teste'],calcular(blocos['teste'].classe,
        np.tile(frequencias,(len(blocos['teste']),1)),blocos['teste'].ambiguo),'referencia_constante')
    evidencias['referencia_constante_recalculada']=True
    if pd.Timestamp(escalas['ultima_hora_ajuste'])>=limites[1]:
        raise ValueError('Scaler consultou validação ou teste.')
    for nome in ('lstm','mamba','ar1'):
        resultado=ler_json(pasta/nome/'resultado_modelo.json')
        q=pd.read_parquet(pasta/nome/'previsoes_teste.parquet')
        esperado=blocos['teste']
        if not q['origem_utc'].equals(esperado['origem_utc']) or not np.array_equal(q['classe'],esperado['classe']):
            raise ValueError('Previsões não estão alinhadas por origem e alvo.')
        recalculo=calcular(q['classe'],q[['p0','p1','p2']].to_numpy(),q['ambiguo'])
        comparar_json(resultado['metricas']['teste'],recalculo,nome)
        if nome!='ar1':
            epocas=ler_json(pasta/nome/'epocas.json')
            menor=min(epocas,key=lambda r:r['validacao_log_loss'])
            if menor['epoca']!=resultado['epoca_selecionada'] or not resultado['recarga_exata']:
                raise ValueError('Checkpoint não corresponde ao mínimo de validação/recarga.')
        evidencias[nome]={'metricas_recalculadas':True,'n':len(q)}
        operacional=pd.read_parquet(pasta/nome/'previsoes_operacional.parquet')
        if not operacional.origem_utc.equals(blocos['operacional'].origem_utc):
            raise ValueError('População operacional alterada.')
        financeiro=ler_json(pasta/nome/'financeiro.json')
        primeiro_minuto=int(limites[0].timestamp()//60)
        for rotulo,opcoes in [('base',{}),('custos_agravados',{'agravado':True}),
                              ('ambiguidade_superior',{'superior_ambiguo':True}),('sem_filtro',{'filtro':False})]:
            evidencias[nome][rotulo]=auditar_financeiro(operacional,minutos,primeiro_minuto,limites,
                financeiro[rotulo],pd.read_parquet(pasta/nome/f'ordens_{rotulo}.parquet'),
                pd.read_parquet(pasta/nome/f'curva_{rotulo}.parquet'),**opcoes)
    evidencias['temporais']={nome:{'n':len(q),'inicio':q.origem_utc.min().isoformat(),
                       'fim':q.origem_utc.max().isoformat(),
                       'expiracao_maxima':q.expiracao_maxima_utc.max().isoformat()}
                            for nome,q in blocos.items() if nome!='operacional'}
    evidencias['status']='aprovado'
    salvar_json(pasta/'auditoria.json',evidencias)
    hashes={p.relative_to(pasta).as_posix():sha256(p) for p in sorted(pasta.rglob('*'))
            if p.is_file() and p.name not in ('integridade.json','estado.json')}
    salvar_json(pasta/'integridade.json',hashes)
    return evidencias
