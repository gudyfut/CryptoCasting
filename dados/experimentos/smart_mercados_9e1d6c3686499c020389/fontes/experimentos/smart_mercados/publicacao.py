import pandas as pd
from infraestrutura.artefatos import RAIZ,agora,ler_json,salvar_json,sha256,conferir_arquivos


def publicar(p,ptr,f,resumos):
    conferir_arquivos(RAIZ,f['fontes']);conferir_arquivos(p/'fontes',f['fontes'])
    reg=RAIZ/'registros/smart_mercados';antigos=ler_json(reg/'preservacao_antes.json')['arquivos'];conferir_arquivos(RAIZ,antigos)
    salvar_json(p/'preservacao_depois.json',{'utc':agora(),'status':'integro','arquivos':len(antigos),'mapa_sha256':sha256(reg/'preservacao_antes.json')})
    manifestos=list((p/'carteiras').rglob('manifesto.json'))
    assert len(manifestos)==1632 and len(resumos)==1632
    for x in manifestos:conferir_arquivos(x.parent,ler_json(x)['arquivos'])
    q=pd.DataFrame(resumos);assert set(q.chave)=={g['chave'] for g in f['grade']}
    grupos=['modelo','politica','braco','cenario']
    metricas=['retorno_liquido','drawdown','exposicao_media','exposicao_vendida','comissoes','slippage','funding','ordens','recusas','giro']
    blocos=q.groupby(['bloco']+grupos)[metricas].mean().reset_index()
    medias=blocos.groupby(grupos)[metricas].mean().reset_index()
    seeds=q[q.seed.notna()].groupby(['seed']+grupos)[metricas].mean().reset_index()
    contrastes=[]
    for modelo in ['astra','crua']:
        for politica in ['smart','smart_filtrada']:
            z=q[(q.modelo==modelo)&(q.politica==politica)&(q.cenario=='iguais')]
            tabela=z.pivot(index=['bloco','seed'],columns='braco',values='retorno_liquido')
            for a,b in [('futuro_sem_funding','spot'),('futuro','futuro_sem_funding'),('futuro','spot'),('futuro_bilateral','futuro')]:
                d=tabela[a]-tabela[b];ds=d.groupby('seed').mean()
                contrastes.append({'modelo':modelo,'politica':politica,'contraste':a+'_menos_'+b,'media_pp':100*float(d.mean()),'pares_melhores':int((d>0).sum()),'pares':32,'seeds_melhores':int((ds>0).sum()),'seeds':8,'min_seed_pp':100*float(ds.min()),'max_seed_pp':100*float(ds.max())})
    for modelo in ['astra','crua']:
        for braco in f['configuracao']['bracos']:
            z=q[(q.modelo==modelo)&(q.braco==braco)&(q.cenario=='iguais')]
            tab=z.pivot(index=['bloco','seed'],columns='politica',values='retorno_liquido');d=tab.smart_filtrada-tab.smart
            contrastes.append({'modelo':modelo,'braco':braco,'contraste':'filtrada_menos_smart','media_pp':100*float(d.mean()),'pares_melhores':int((d>0).sum()),'pares':32})
    r={'utc':agora(),'execucao':ptr,'carteiras':resumos,'medias_por_bloco':blocos.to_dict('records'),'medias_globais':medias.to_dict('records'),'medias_por_seed':seeds.to_dict('records'),'contrastes_descritivos':contrastes,
       'limites':'Media de blocos independentes e seeds; retrospectivo, sem IC confirmatorio; mesmo filtro/gestao em todos; Smart95 comum nao e reproducao exata da Smart antiga; custos/filtros de pesquisa, sem liquidacao real completa.'}
    pub=p/'publicacao';pub.mkdir(exist_ok=False);salvar_json(pub/'resultados.json',r)
    salvar_json(pub/'manifesto.json',{'arquivos':{'resultados.json':sha256(pub/'resultados.json')},'carteiras':{x.relative_to(p).as_posix():sha256(x) for x in manifestos}})
    fim={'utc':agora(),'situacao':'concluido_conferido','execucao':ptr,'concluidas':1632,'total':1632,'novos_treinamentos':0,'publicacao_sha256':sha256(pub/'manifesto.json'),'preservacao_sha256':sha256(p/'preservacao_depois.json')}
    salvar_json(p/'fechamento.json',fim);salvar_json(p/'progresso.json',fim);salvar_json(reg/'estado.json',fim);print('CONCLUIDO',ptr['id'],flush=True)
