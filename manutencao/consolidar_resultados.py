"""Consolidação completa por fase; nunca transforma uma grade parcial em placar final."""
import argparse
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from previsao24.arquivos import RAIZ,ler_json,salvar_json,sha256,verificar_arquivos,agora
from previsao24.configuracao import FOLDS,celulas
from previsao24.metricas import calcular
from previsao24.financeiro import simular
from previsao24.dados import verificar_dataset

def curva_liquidacao(curva,latencia):
    """Publicar caixa na mesma convenção de liquidação das operações (00:01).

    O simulador devolve marca de caixa na origem 00:00, depois de contabilizar a
    saída agendada da posição anterior às00:01. A apresentação usa o instante
    correto de liquidação; não muda sinais, quantidades ou retornos.
    """
    por_tempo={}
    for ponto in curva:
        t=pd.Timestamp(ponto['tempo_utc'])
        if t.minute==0:
            t+=pd.Timedelta(minutes=latencia)
        por_tempo[t.isoformat()]={'tempo_utc':t.isoformat(),'capital':ponto['capital']}
    return [por_tempo[t] for t in sorted(por_tempo)]

def curva_publicada(curva,c,folds):
    inicio={'tempo_utc':pd.Timestamp(FOLDS[folds[0]][1],tz='UTC').isoformat(),'capital':c['operacao']['capital']}
    return [inicio,*curva_liquidacao(curva,c['operacao']['latencia_minutos'])]

def intervalo_blocos(diarios,dias,replicas,seed):
    """Cada item contém somas/contagens por dia de um fold; pesos iguais entre folds."""
    rng=np.random.default_rng(seed)
    amostras=np.zeros(replicas)
    for somas,contagens in diarios:
        n=len(somas)
        tamanho=min(dias,n)
        quantidade=int(np.ceil(n/tamanho))
        inicios=rng.integers(0,n-tamanho+1,size=(replicas,quantidade))
        indices=(inicios[:,:,None]+np.arange(tamanho)).reshape(replicas,-1)[:,:n]
        denominadores=contagens[indices].sum(axis=1)
        if (denominadores==0).any():
            raise ValueError('Reamostragem sem observações; não inventar intervalo.')
        amostras+=somas[indices].sum(axis=1)/denominadores/len(diarios)
    return {'inferior':float(np.quantile(amostras,.025)),'superior':float(np.quantile(amostras,.975)),
            'dias':dias,'replicas':replicas}

def diario(tempos,valores,fold):
    quadro=pd.DataFrame({'dia':tempos.dt.floor('D'),'valor':valores})
    soma=quadro.groupby('dia')['valor'].sum()
    n=quadro.groupby('dia').size()
    calendario=pd.date_range(FOLDS[fold][1],FOLDS[fold][2],freq='D',inclusive='left',tz='UTC')
    return soma.reindex(calendario,fill_value=0).to_numpy(),n.reindex(calendario,fill_value=0).to_numpy()

def consolidar(fase):
    ponteiro=ler_json(RAIZ/'registros/execucao_atual.json')
    pasta=RAIZ/ponteiro['caminho']
    if not (pasta/f'{fase}_concluido.json').exists():
        raise ValueError('Fase ainda incompleta; não consolidar como concluída.')
    execucao=ler_json(pasta/'execucao.json')
    dados=RAIZ/execucao['dataset_caminho']
    manifesto=verificar_dataset(dados)
    if manifesto['id']!=ponteiro['dataset'] or manifesto['id']!=execucao['assinatura']['dataset']:
        raise ValueError('Dataset da publicação difere da execução.')
    hash_manifesto=sha256(dados/'dataset.json')
    c=execucao['assinatura']['configuracao']
    folds=c['folds_desenvolvimento'] if fase=='desenvolvimento' else c['folds_avaliacao']
    esperado={(x['par'],x['fold'],x['contexto'],x['seed'],x['modelo']) for x in celulas(c,fase)}
    esperado|={(p,f,None,None,m) for p in c['pares'] for f in folds for m in ('arima','naive')}
    registros={}
    resultados=[]
    arima=[]
    fontes={}
    for t in sorted(pasta.glob('celulas/*/tentativa_*/tentativa.json')):
        tentativa=ler_json(t)
        x=tentativa['celula']
        if x['fold'] not in folds or tentativa['status']!='auditada':
            continue
        chave=(x['par'],x['fold'],x.get('contexto'),x.get('seed'),x['modelo'])
        if chave in registros:
            raise ValueError('Resultado auditado duplicado.')
        auditoria=ler_json(t.parent/'auditoria.json')
        verificar_arquivos(t.parent,auditoria['arquivos'])
        fontes[t.parent.relative_to(RAIZ).as_posix()]=sha256(t.parent/'auditoria.json')
        q=pd.read_parquet(t.parent/'previsoes_teste.parquet')
        metrica=calcular(q['alvo'],q['previsao'])
        salvo=ler_json(t.parent/'resultado.json')
        if metrica!=salvo['metricas']['teste']:
            raise ValueError('Métricas salvas divergentes.')
        registros[chave]=(q,t.parent,salvo)
        resultados.append({**x,**metrica,'epoca':salvo.get('epoca_selecionada'),'segundos':salvo.get('segundos'),'parametros':salvo.get('parametros'),
                           'media_previsao':float(q['previsao'].mean()),'desvio_previsao':float(q['previsao'].std(ddof=0)),
                           'media_alvo':float(q['alvo'].mean()),'desvio_alvo':float(q['alvo'].std(ddof=0))})
        if x['modelo']=='arima':
            arima.append({'par':x['par'],'fold':x['fold'],'ordem':salvo['ordem'],'validos':salvo['candidatos_validos'],'falhos':salvo['candidatos_falhos']})
    if set(registros)!=esperado:
        raise ValueError(f'Inventário incompleto/extra: {len(registros)}/{len(esperado)}')
    destino=RAIZ/'registros/analises'/ponteiro['id']/fase
    destino.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(resultados).to_csv(destino/'metricas_por_ajuste.csv',index=False)
    escores={}
    medias=[]
    tempos={}
    for fold in folds:
        for par in c['pares']:
            for w in c['contextos']:
                for modelo in ('lstm','mamba','arima','naive'):
                    itens=[registros[par,fold,w,s,modelo] for s in c['seeds']] if modelo in ('lstm','mamba') else [registros[par,fold,None,None,modelo]]
                    referencia=itens[0][0]
                    for q,_,_ in itens:
                        if not referencia['origem_utc'].equals(q['origem_utc']) or not referencia['alvo'].equals(q['alvo']):
                            raise ValueError('Seeds desalinhadas.')
                    erro=np.mean([(q['previsao'].to_numpy()-q['alvo'].to_numpy())**2 for q,_,_ in itens],axis=0)
                    escores[par,fold,w,modelo]=erro
                    if fold in tempos and not tempos[fold].equals(referencia['origem_utc']):
                        raise ValueError('Origens não comuns entre moedas/contextos.')
                    tempos[fold]=referencia['origem_utc']
                    media={k:float(np.mean([r['metricas']['teste'][k] for _,_,r in itens])) for k in ('mse','mae','habilidade_mse','acuracia_direcional','acerto_balanceado_direcional')}
                    media.update(par=par,fold=fold,contexto=w,modelo=modelo,rmse=float(np.sqrt(media['mse'])))
                    medias.append(media)
    quadro=pd.DataFrame(medias)
    quadro.to_csv(destino/'metricas_medias_seeds.csv',index=False)
    global_modelos=[]
    for modelo in ('lstm','mamba','arima','naive'):
        q=quadro[quadro.modelo==modelo]
        global_modelos.append({'modelo':modelo,**{k:float(q[k].mean()) for k in ('mse','mae','habilidade_mse','acuracia_direcional','acerto_balanceado_direcional')},'rmse':float(np.sqrt(q.mse.mean()))})
    estabilidade=[]
    for modelo in ('lstm','mamba'):
        por_seed=[]
        for seed in c['seeds']:
            itens=[r for r in resultados if r['modelo']==modelo and r['seed']==seed]
            por_seed.append({'seed':seed,'mse':float(np.mean([r['mse'] for r in itens])),
                             'habilidade_mse':float(np.mean([r['habilidade_mse'] for r in itens]))})
        estabilidade.append({'modelo':modelo,'por_seed':por_seed,'mse_desvio_entre_seeds':float(np.std([r['mse'] for r in por_seed],ddof=0))})
    contrastes=[]
    for a,b in (('mamba','lstm'),('mamba','arima'),('mamba','naive'),('lstm','naive')):
        diarios=[]
        pontuais=[]
        for fold in folds:
            diferenca=np.mean([escores[p,fold,w,a]-escores[p,fold,w,b] for p in c['pares'] for w in c['contextos']],axis=0)
            diarios.append(diario(tempos[fold],diferenca,fold))
            pontuais.append(float(diferenca.mean()))
        contrastes.append({'contraste':f'{a}_menos_{b}','metrica':'mse','diferenca':float(np.mean(pontuais)),
                           'intervalos':[intervalo_blocos(diarios,d,c['bootstrap']['replicas'],c['bootstrap']['seed']) for d in c['bootstrap']['dias']]})
    contexto=[]
    for modelo in ('mamba','lstm'):
        for w in c['contextos'][1:]:
            diarios=[]
            valores=[]
            for fold in folds:
                diferenca=np.mean([escores[p,fold,24,modelo]-escores[p,fold,w,modelo] for p in c['pares']],axis=0)
                valores.append(float(diferenca.mean()))
                diarios.append(diario(tempos[fold],diferenca,fold))
            contexto.append({'modelo':modelo,'contexto_referencia':24,'contexto_comparado':w,'mse_curto_menos_longo':float(np.mean(valores)),
                             'intervalos':[intervalo_blocos(diarios,d,c['bootstrap']['replicas'],c['bootstrap']['seed']) for d in c['bootstrap']['dias']]})
    # Simular a fase concatenada: uma conta por estratégia; sementes não viram ensemble.
    financeiro=[]
    for par in c['pares']:
        minutos=np.load(dados/par/'minutos.npy',mmap_mode='r')
        estrategias=[(m,w,s) for m in ('lstm','mamba') for w in c['contextos'] for s in c['seeds']]+[(m,None,None) for m in ('arima','naive')]
        for modelo,w,seed in estrategias:
            trechos=[]
            for fold in folds:
                _,local,_=registros[par,fold,w,seed,modelo]
                q=pd.read_parquet(local/'previsoes_operacional.parquet')
                # Filtro somente de calendário; nunca olhar alvo/preço de saída.
                fim=pd.Timestamp(FOLDS[fold][2],tz='UTC')
                q=q.loc[(q['origem_utc']+pd.Timedelta(hours=24,minutes=1)).lt(fim)]
                trechos.append(q)
            operacionais=pd.concat(trechos,ignore_index=True)
            for agravado in (False,True):
                resumo,ordens,curva=simular(operacionais,minutos,manifesto['primeiro_minuto'],FOLDS[folds[-1]][2],c['operacao'],agravado=agravado)
                curva=curva_publicada(curva,c,folds)
                chave={'par':par,'modelo':modelo,'contexto':w,'seed':seed,**resumo}
                financeiro.append(chave)
                nome=f'{par}_{modelo}_W{w}_S{seed}_{"agravado" if agravado else "base"}.json'
                chave['arquivo']=f'operacoes/{nome}'
                salvar_json(destino/'operacoes'/nome,{'estrategia':chave,'ordens':ordens,'curva':curva})
            if modelo=='naive':
                resumo,ordens,curva=simular(operacionais,minutos,manifesto['primeiro_minuto'],FOLDS[folds[-1]][2],c['operacao'],controle=True)
                curva=curva_publicada(curva,c,folds)
                financeiro.append({'par':par,'modelo':'compra_diaria','contexto':None,'seed':None,**resumo})
                financeiro[-1]['arquivo']=f'operacoes/{par}_compra_diaria.json'
                salvar_json(destino/'operacoes'/f'{par}_compra_diaria.json',{'estrategia':financeiro[-1],'ordens':ordens,'curva':curva})
        del minutos
    pd.DataFrame(financeiro).to_csv(destino/'financeiro.csv',index=False)
    salvar_json(destino/'resumo.json',{'fase':fase,'execucao':ponteiro['id'],'dataset':ponteiro['dataset'],'gerado_utc':agora(),
                                     'dataset_manifesto_sha256':hash_manifesto,
                                     'configuracao':c,'modelos':global_modelos,'contrastes':contrastes,'contextos':contexto,
                                     'metricas':medias,'ajustes':resultados,'estabilidade':estabilidade,'arima':arima,'financeiro':financeiro,'fontes':fontes,'consolidador_sha256':sha256(Path(__file__))})
    publicados=[destino/'resumo.json',destino/'metricas_por_ajuste.csv',destino/'metricas_medias_seeds.csv',destino/'financeiro.csv']
    publicados+=sorted((destino/'operacoes').glob('*.json'))
    salvar_json(destino/'publicacao.json',{'execucao':ponteiro['id'],'fase':fase,'gerado_utc':agora(),
                                         'arquivos':{p.relative_to(destino).as_posix():sha256(p) for p in publicados}})
    print(f'Consolidação completa: {destino}',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--fase',choices=['desenvolvimento','avaliacao'],required=True)
    fase=parser.parse_args().fase
    consolidar(fase)
    from auditar_publicacao import auditar
    auditar(fase)
    if fase=='desenvolvimento':
        # Disponibilizar a fase inteira antes da avaliação posterior, sem alterar
        # modelos ou antecipar a leitura de resultados ainda não executados.
        from exportar_portal import exportar
        exportar()
