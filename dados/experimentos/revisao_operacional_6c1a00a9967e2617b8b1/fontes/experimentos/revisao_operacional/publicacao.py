import pandas as pd
from infraestrutura.artefatos import RAIZ,agora,ler_json,salvar_json,sha256,conferir_arquivos


def publicar(p,ptr,f,resumos):
    conferir_arquivos(RAIZ,f['fontes']);conferir_arquivos(p/'fontes',f['fontes'])
    reg=RAIZ/'registros/revisao_operacional';antigos=ler_json(reg/'preservacao_antes.json')['arquivos'];conferir_arquivos(RAIZ,antigos)
    salvar_json(p/'preservacao_depois.json',{'utc':agora(),'status':'integro','arquivos':len(antigos),'mapa_sha256':sha256(reg/'preservacao_antes.json')})
    manifestos=list((p/'carteiras').rglob('manifesto.json'))
    total=f['configuracao']['simulacoes_total']
    assert len(manifestos)==total and len(resumos)==total
    for x in manifestos:conferir_arquivos(x.parent,ler_json(x)['arquivos'])
    q=pd.DataFrame(resumos);assert set(q.chave)=={g['chave'] for g in f['grade']}
    grupos=['modelo','politica','braco','cenario']
    metricas=['retorno_liquido','drawdown','exposicao_media','exposicao_vendida','comissoes','slippage','funding','ordens','recusas','giro','abaixo_minimo','residuo_usdt']
    blocos=q.groupby(['bloco']+grupos)[metricas].mean().reset_index()
    medias=blocos.groupby(grupos)[metricas].mean().reset_index()
    seeds=q[q.seed.notna()].groupby(['seed']+grupos)[metricas].mean().reset_index()
    contrastes=[]
    for modelo in f['configuracao']['versoes']:
        for braco in f['configuracao']['bracos']:
            tab=q[(q.modelo==modelo)&(q.braco==braco)&(q.cenario=='base')].pivot(index=['bloco','seed'],columns='politica',values='retorno_liquido')
            for a,b in [('direcional','smart'),('direcional_filtrada','direcional')]:
                d=tab[a]-tab[b];ds=d.groupby('seed').mean();db=d.groupby('bloco').mean()
                contrastes.append({'modelo':modelo,'braco':braco,'contraste':a+'_menos_'+b,'media_pp':100*float(d.mean()),'pares_melhores':int((d>0).sum()),'pares':32,
                    'seeds_melhores':int((ds>0).sum()),'seeds':8,'min_seed_pp':100*float(ds.min()),'max_seed_pp':100*float(ds.max()),'blocos_melhores':int((db>0).sum()),'blocos':4})
    r={'utc':agora(),'execucao':ptr,'carteiras':resumos,'medias_por_bloco':blocos.to_dict('records'),'medias_globais':medias.to_dict('records'),'medias_por_seed':seeds.to_dict('records'),'contrastes_descritivos':contrastes,
       'limites':'Retrospectivo: medias de blocos independentes/seeds, nao retorno composto nem IC confirmatorio. Regras de pesquisa e envelope de margem, sem replica integral da Binance.'}
    pub=p/'publicacao';pub.mkdir(exist_ok=False);salvar_json(pub/'resultados.json',r)
    salvar_json(pub/'manifesto.json',{'arquivos':{'resultados.json':sha256(pub/'resultados.json')},'carteiras':{x.relative_to(p).as_posix():sha256(x) for x in manifestos}})
    fim={'utc':agora(),'situacao':'concluido_conferido','execucao':ptr,'concluidas':total,'total':total,'novos_treinamentos':0,'publicacao_sha256':sha256(pub/'manifesto.json'),'preservacao_sha256':sha256(p/'preservacao_depois.json')}
    salvar_json(p/'fechamento.json',fim);salvar_json(p/'progresso.json',fim);salvar_json(reg/'estado.json',fim);print('CONCLUIDO',ptr['id'],flush=True)
