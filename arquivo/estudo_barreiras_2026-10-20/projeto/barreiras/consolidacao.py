"""Tabelas completas, comparações pareadas e patrimônio entre folds."""
from pathlib import Path
import numpy as np
import pandas as pd

from .arquivos import agora,ler_json,salvar_json,sha256,identidade,RAIZ
from .configuracao import celulas,FOLDS
from .metricas import erros
from .estatistica import comparar,indices_blocos,deslocamento_fold


def consolidar(raiz: Path):
    ciclo=ler_json(raiz/'ciclo.json');c=ciclo['assinatura']['configuracao']
    esperadas=celulas(c);registros=[];tentativas=[]
    for p in sorted(raiz.glob('*/estado.json')):
        estado=ler_json(p);tentativas.append({k:estado.get(k) for k in ('id','celula','status','erro')})
        if estado['status']!='concluida_auditada':
            continue
        if estado['id_ciclo']!=ciclo['id'] or estado['dataset']!=ciclo['assinatura']['dataset'] or estado['codigo']!=identidade(ciclo['assinatura']['codigo']):
            raise ValueError('Tentativa de misturar identidades na consolidação.')
        for rel,h in ler_json(p.parent/'integridade.json').items():
            if sha256(p.parent/rel)!=h:
                raise ValueError(f'Artefato alterado: {p.parent/rel}')
        registros.append((estado,p.parent))
    chaves=[identidade(e['celula']) for e,_ in registros]
    if len(set(chaves))!=len(chaves):
        raise ValueError('Duas tentativas concluídas da mesma célula: resolver procedência antes de agregar.')
    if not set(chaves)<=set(identidade(x) for x in esperadas):
        raise ValueError('Célula concluída não pertence à grade.')
    completo=len(registros)==len(esperadas)
    linhas=[];predicoes={};contextos=[]
    for e,p in registros:
        a=e['celula'];chave=(a['par'],a['contexto'],a['horizonte'],a['fold'],a['seed'])
        for nome,r in e['resultados'].items():
            m=r['metricas']['teste'];f=e['financeiro'][nome]['base']
            linhas.append({**a,'modelo':nome,'n':m['n'],'log_loss':m['log_loss'],'brier':m['brier'],
                'balanced_accuracy':m['balanced_accuracy'],'macro_f1':m['macro_f1'],
                'segundos':r.get('segundos'),'parametros':r.get('parametros'),
                'status_financeiro':f['status'],'retorno_liquido':f['retorno_liquido'],
                'drawdown_maximo':f['drawdown_maximo'],'operacoes':f.get('operacoes'),
                'tempo_exposto':f.get('tempo_exposto'),'taxas':f.get('taxas'),'id':e['id']})
            predicoes[chave+(nome,)]=pd.read_parquet(p/nome/'previsoes_teste.parquet')
        ref=e['referencia_constante']['metricas_teste']
        linhas.append({**a,'modelo':'frequencia_treino','n':ref['n'],'log_loss':ref['log_loss'],
              'brier':ref['brier'],'balanced_accuracy':ref['balanced_accuracy'],'macro_f1':ref['macro_f1'],'id':e['id']})
    destino=raiz/'consolidacao';destino.mkdir(exist_ok=True)
    tabela=pd.DataFrame(linhas)
    tabela.to_csv(destino/'celulas.csv',index=False)
    resumo={'id_ciclo':ciclo['id'],'criado_utc':agora(),'status':'completo' if completo else 'parcial',
        'celulas_esperadas':len(esperadas),'celulas_auditadas':len(registros),'tentativas':tentativas,
        'ausentes':[x for x in esperadas if identidade(x) not in chaves]}
    if len(tabela):
        medias=tabela.groupby(['par','contexto','horizonte','fold','modelo'])[['log_loss','brier']].mean()
        resumo['medias_das_celulas_disponiveis']=medias.groupby('modelo').mean().to_dict('index')
    # Efeito de contexto só entre células efetivamente pareadas.
    for chave,a in predicoes.items():
        par,w,h,fold,seed,nome=chave
        b=predicoes.get((par,168,h,fold,seed,nome))
        if w==24 and b is not None:
            contextos.append({'par':par,'horizonte':h,'fold':fold,'seed':seed,'modelo':nome,
                'contraste':'W24 menos W168',**comparar(a,b)})
    salvar_json(destino/'efeito_contexto.json',contextos)
    # Inferência global só quando a grade completa estiver auditada.
    if completo:
        contrastes={}
        for nome in ('lstm','ar1'):
            pares=[]
            for par in c['pares']:
                for w in c['contextos']:
                    for h in c['horizontes']:
                        for f in c['folds']:
                            diferencas=[];origens=None
                            for seed in c['seeds']:
                                a=predicoes[par,w,h,f,seed,'mamba'];b=predicoes[par,w,h,f,seed,nome]
                                if not a.origem_utc.equals(b.origem_utc) or not a.classe.equals(b.classe):
                                    raise ValueError('Contraste global não está pareado.')
                                if origens is not None and not origens.equals(a.origem_utc):
                                    raise ValueError('Seeds com populações diferentes.')
                                origens=a.origem_utc
                                ea=np.column_stack(erros(a.classe,a[['p0','p1','p2']].to_numpy()))
                                eb=np.column_stack(erros(b.classe,b[['p0','p1','p2']].to_numpy()))
                                diferencas.append(ea-eb)
                            d=np.mean(diferencas,axis=0)
                            diario=pd.DataFrame({'dia':origens.dt.floor('D'),'log_loss':d[:,0],'brier':d[:,1],'n':1}).groupby('dia').sum()
                            limites=FOLDS[f].limites()
                            diario=diario.reindex(pd.date_range(limites[2],limites[3],freq='D',inclusive='left'),fill_value=0)
                            pares.append((f,d.mean(axis=0),diario))
            item={'diferenca_media':dict(zip(('log_loss','brier'),np.mean([x[1] for x in pares],axis=0).tolist())),'intervalos':{}}
            for bloco in (7,14,28):
                replicas=[]
                for f,_,dia in pares:
                    ix=indices_blocos(len(dia),bloco,deslocamento_fold(FOLDS[f].limites()[2]))
                    ns=dia.n.to_numpy()[ix].sum(axis=1)
                    if (ns<=0).any():
                        raise ValueError('Réplica bootstrap sem observações.')
                    replicas.append(dia[['log_loss','brier']].to_numpy()[ix].sum(axis=1)/ns[:,None])
                quantis=np.quantile(np.mean(replicas,axis=0),[.025,.975],axis=0)
                item['intervalos'][str(bloco)]={metrica:quantis[:,k].tolist() for k,metrica in enumerate(('log_loss','brier'))}
            contrastes[f'mamba_menos_{nome}']=item
        resumo['contrastes_globais']=contrastes
    # Cada estratégia e seed mantém seu próprio capital. Ausência de um fold
    # ou lacuna em uma posição impede publicar um retorno anual completo.
    curvas={}
    for e,p in registros:
        a=e['celula']
        for nome in ('lstm','mamba','ar1'):
            for variante in ('base','custos_agravados','ambiguidade_superior','sem_filtro'):
                chave=(a['par'],a['contexto'],a['horizonte'],a['seed'],nome,variante)
                curvas.setdefault(chave,{})[a['fold']]=(e['financeiro'][nome][variante],p/nome/f'curva_{variante}.parquet')
    financeiros=[]
    for chave,folds in curvas.items():
        par,w,h,seed,nome,variante=chave
        item={'par':par,'contexto':w,'horizonte':h,'seed':seed,'modelo':nome,'variante':variante}
        if set(folds)!=set(c['folds']) or any(r['status']!='auditavel' for r,_ in folds.values()):
            item.update(status='incompleto_ou_nao_auditavel',retorno_liquido=None)
        else:
            capital=10000.;partes=[];diarios=[]
            for f in c['folds']:
                r,p=folds[f];q=pd.read_parquet(p)
                diario=q.assign(dia=pd.to_datetime(q.minuto_utc,unit='m',utc=True).dt.floor('D')).groupby('dia').patrimonio.last()
                diarios.append((f,diario.to_numpy()/np.r_[10000.,diario.to_numpy()[:-1]]-1))
                q['patrimonio']*=capital/10000.;q['pior_marca_observavel']*=capital/10000.
                capital=float(q.patrimonio.iloc[-1]);partes.append(q)
            curva=pd.concat(partes,ignore_index=True)
            picos=np.maximum.accumulate(np.r_[10000.,curva.patrimonio])[1:]
            arquivo='curva_'+identidade(chave)[:20]+'.parquet'
            curva.to_parquet(destino/arquivo,index=False)
            item.update(status='auditavel',retorno_liquido=capital/10000.-1,
                drawdown_maximo=float((1-curva.patrimonio.to_numpy()/picos).max()),
                tempo_exposto=float(curva.exposto.mean()),arquivo=arquivo,intervalos={})
            for bloco in (7,14,28):
                amostras=np.concatenate([r[indices_blocos(len(r),bloco,deslocamento_fold(FOLDS[f].limites()[2]))] for f,r in diarios],axis=1)
                patrimonio=np.cumprod(1+amostras,axis=1)
                picos=np.maximum.accumulate(np.column_stack([np.ones(len(amostras)),patrimonio]),axis=1)[:,1:]
                item['intervalos'][str(bloco)]={'retorno_liquido':np.quantile(patrimonio[:,-1]-1,[.025,.975]).tolist(),
                    'drawdown_diario':np.quantile((1-patrimonio/picos).max(axis=1),[.025,.975]).tolist()}
        financeiros.append(item)
    controles=[]
    for par in c['pares']:
        for w in c['contextos']:
            for h in c['horizontes']:
                for seed in c['seeds']:
                    encontrados={e['celula']['fold']:e['financeiro']['mamba']['comprar_manter'] for e,_ in registros
                        if all(e['celula'][k]==v for k,v in [('par',par),('contexto',w),('horizonte',h),('seed',seed)])}
                    valido=set(encontrados)==set(c['folds']) and all(x['status']=='auditavel' for x in encontrados.values())
                    controles.append({'par':par,'contexto':w,'horizonte':h,'seed':seed,'controle':'comprar_manter',
                        'status':'auditavel' if valido else 'incompleto_ou_nao_auditavel',
                        'retorno_liquido':float(np.prod([1+x['retorno_liquido'] for x in encontrados.values()])-1) if valido else None})
    resumo['controles_comprar_manter']=controles
    resumo['controle_caixa']={'retorno_liquido':0.}
    salvar_json(destino/'financeiro_concatenado.json',financeiros)
    salvar_json(destino/'resumo.json',resumo)
    salvar_json(RAIZ/'historico/ciclos'/f"resultado_{ciclo['id']}.json",resumo)
    return resumo
