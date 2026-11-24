"""Grade fixa, preservação, identidade, execução exclusiva e auditoria contábil."""
import itertools,os,platform,shutil,subprocess,sys,traceback
from pathlib import Path
import pandas as pd
from infraestrutura.artefatos import RAIZ,agora,ler_json,salvar_json,sha256,identidade,conferir_arquivos
from mercado_futuros.contexto import carregar_contexto
from simulacao_operacoes.previsoes import COLUNAS,diarias
from simulacao_operacoes.futuros.mercado import Mercado
from simulacao_operacoes.futuros.simulador import simular
from simulacao_operacoes.futuros.auditoria import conferir

REG=RAIZ/'registros/futuros'

def grade(cfg):
    linhas=[]
    for b,v,s,p,m,c in itertools.product(cfg['blocos'],cfg['versoes'],cfg['seeds'],cfg['politicas'],cfg['modos'],cfg['custos']):
        linhas.append({'bloco':b,'modelo':v,'seed':s,'politica':p,'modo':m,'cenario':c,'serie':f'{b}/{v}/{s}'})
    for b,v,c in itertools.product(cfg['blocos'],['sempre_comprado','sempre_vendido','caixa'],cfg['custos']):
        linhas.append({'bloco':b,'modelo':v,'seed':None,'politica':'sinal24','modo':'bilateral','cenario':c,'serie':f'{b}/astra/{cfg["seeds"][0]}'})
    for g in linhas:g['chave']='/'.join(str(g[k]) for k in ['bloco','modelo','seed','politica','modo','cenario'])
    assert len(linhas)==cfg['simulacoes_total']==len({g['chave'] for g in linhas})
    return linhas

def fontes():
    arquivos=[]
    for pasta in ['simulacao_operacoes','experimentos/futuros','mercado_futuros','tests_simulacao_operacoes']:
        arquivos.extend((RAIZ/pasta).rglob('*.py'))
    arquivos += [RAIZ/p for p in ['infraestrutura/artefatos.py','infraestrutura/__init__.py','experimentos/__init__.py','configuracoes/futuros_001.json','docs/protocolo_futuros.md']]
    return {p.relative_to(RAIZ).as_posix():sha256(p) for p in arquivos}

def ler_series(vinculos):
    series={};calendarios={}
    for chave,v in vinculos.items():
        p=RAIZ/v['pasta'];assert sha256(p/'conclusao.json')==v['conclusao_sha256']
        conclu=ler_json(p/'conclusao.json');conferir_arquivos(p,conclu['arquivos'])
        q=pd.read_parquet(p/'previsoes_teste.parquet')[COLUNAS];d=diarias(q);b=chave.split('/')[0]
        conhecidos=d.drop(columns='previsao')
        if b in calendarios:pd.testing.assert_frame_equal(conhecidos,calendarios[b])
        else:calendarios[b]=conhecidos
        series[chave]=d
    assert len(series)==64
    return series

def preparar():
    REG.mkdir(parents=True,exist_ok=True)
    if (REG/'execucao.json').exists():raise RuntimeError('Preparacao existente: nao sobrescrever.')
    cfg=ler_json(RAIZ/'configuracoes/futuros_001.json');gg=grade(cfg)
    teste=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','discover','-s','tests_simulacao_operacoes','-v'],cwd=RAIZ,capture_output=True,text=True,encoding='utf-8')
    (REG/'qualificacao.log').write_text(teste.stdout+teste.stderr,encoding='utf-8')
    if teste.returncode:raise RuntimeError('Qualificacao sintetica falhou.')
    origem=ler_json(RAIZ/cfg['fontes_modelos']);op=RAIZ/origem['pasta'];assert sha256(op/'congelamento.json')==origem['congelamento_sha256']
    congelado=ler_json(op/'congelamento.json');conferir_arquivos(RAIZ,congelado['fontes'])
    pub=ler_json(op/'publicacao.json');resultado=op/'publicacoes/tentativa_001/resultados.json'
    manifesto=ler_json(resultado.parent/'manifesto.json');conferir_arquivos(resultado.parent,manifesto['arquivos'])
    r=ler_json(resultado);series=ler_series(r['series'])
    mercado=ler_json(RAIZ/'registros/mercado_futuros/contexto.json');m=Mercado(*carregar_contexto(mercado))
    cobertura={}
    for b in cfg['blocos']:
        d=series[f'{b}/astra/{cfg["seeds"][0]}'];inicio=int(d.origem_utc.iloc[0].timestamp()//60);fim=int(d.origem_utc.iloc[-1].timestamp()//60)+1441
        m.indice(inicio-1);m.indice(fim);cobertura[b]={'dias':len(d),'inicio':d.origem_utc.iloc[0].isoformat(),'fim_operacional_minuto':fim}
    # Mapa herdado validado antes de ampliá-lo: não aceitar alterações por novos hashes.
    preservacao=ler_json(RAIZ/'registros/comparacao_astra_crua/preservacao_antes.json')['arquivos'];conferir_arquivos(RAIZ,preservacao)
    preservacao.update(congelado['fontes'])
    preservacao.update({p.relative_to(RAIZ).as_posix():sha256(p) for p in op.rglob('*') if p.is_file()})
    salvar_json(REG/'preservacao_antes.json',{'utc':agora(),'arquivos':preservacao})
    assinatura={'configuracao':cfg,'fontes':fontes(),'mercado':mercado,'origem':origem,'resultado_origem':{'arquivo':resultado.relative_to(RAIZ).as_posix(),'sha256':sha256(resultado)},'series':r['series'],'grade':gg,'cobertura':cobertura,
                'preservacao_sha256':sha256(REG/'preservacao_antes.json'),'qualificacao_sha256':sha256(REG/'qualificacao.log'),'ambiente':{'python':sys.version,'plataforma':platform.platform(),'pandas':pd.__version__}}
    codigo=identidade(assinatura)[:20];p=RAIZ/'dados/experimentos'/('futuros_'+codigo);p.mkdir(parents=True,exist_ok=False)
    for nome in assinatura['fontes']:
        destino=p/'fontes'/nome;destino.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(RAIZ/nome,destino)
    salvar_json(p/'congelamento.json',{'id':codigo,'utc':agora(),'assinatura':assinatura})
    salvar_json(p/'autorizacao.json',{'utc':agora(),'origem':'Pedido explicito do pesquisador neste chat em04/11/2026: modularizar e comecar simulacao de compra/venda em futuros.','escopo':'804carteiras posteriores; zero treino; previsoes preservadas; nao abre ordens reais nem amplia busca.'})
    ptr={'id':codigo,'pasta':p.relative_to(RAIZ).as_posix(),'congelamento_sha256':sha256(p/'congelamento.json')}
    salvar_json(REG/'execucao.json',ptr);salvar_json(REG/'estado.json',{'utc':agora(),'situacao':'preparado_autorizado','execucao':ptr,'total':804,'novos_treinamentos':0})
    print('PREPARADO',ptr,flush=True)

def executar():
    ptr=ler_json(REG/'execucao.json');p=RAIZ/ptr['pasta'];assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    f=ler_json(p/'congelamento.json');a=f['assinatura'];assert identidade(a)[:20]==ptr['id'];cfg=a['configuracao']
    if any((p/n).exists() for n in ['processo.json','fechamento.json','incidente.json']):raise RuntimeError('Execucao ja iniciada; nunca repetir ou retomar automaticamente.')
    lock=REG/'execucao.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    try:
        os.write(fd,f'{platform.node()}:{os.getpid()}'.encode());os.close(fd)
        salvar_json(p/'processo.json',{'utc':agora(),'pid':os.getpid(),'host':platform.node()})
        conferir_arquivos(RAIZ,a['fontes']);conferir_arquivos(p/'fontes',a['fontes'])
        assert sha256(REG/'preservacao_antes.json')==a['preservacao_sha256']
        assert sha256(RAIZ/a['resultado_origem']['arquivo'])==a['resultado_origem']['sha256']
        assert len(a['grade'])==len(grade(cfg))==804
        series=ler_series(a['series']);m=Mercado(*carregar_contexto(a['mercado']));resumos=[]
        for i,g in enumerate(a['grade']):
            pasta=p/'carteiras'/g['chave'];pasta.mkdir(parents=True,exist_ok=False)
            d=series[g['serie']]
            if g['seed'] is None:d=d.assign(previsao={'sempre_comprado':.1,'sempre_vendido':-.1,'caixa':0.}[g['modelo']])
            resumo,trades,curva,eventos=simular(d,m,cfg,g['politica'],g['modo'],g['cenario']);audit=conferir(resumo,trades,eventos,m,cfg)
            salvar_json(pasta/'resumo.json',resumo);salvar_json(pasta/'operacoes.json',trades);salvar_json(pasta/'funding.json',eventos);salvar_json(pasta/'auditoria.json',audit);curva.to_parquet(pasta/'curva.parquet',index=False)
            salvar_json(pasta/'manifesto.json',{'grade':g,'arquivos':{z.name:sha256(z) for z in pasta.iterdir() if z.is_file()}})
            resumos.append(dict(g,**resumo))
            estado={'utc':agora(),'situacao':'executando','execucao':ptr,'concluidas':i+1,'total':804,'percentual':100*(i+1)/804,'novos_treinamentos':0}
            salvar_json(p/'progresso.json',estado);salvar_json(REG/'estado.json',estado)
            if (i+1)%24==0:print('SIMULACOES',i+1,'/804',flush=True)
        publicar(p,ptr,a,resumos)
    except BaseException:
        incidente={'utc':agora(),'situacao':'interrompido','execucao':ptr,'erro':traceback.format_exc()}
        salvar_json(p/'incidente.json',incidente);salvar_json(REG/'estado.json',incidente);raise
    finally:
        if lock.exists():lock.unlink()

def publicar(p,ptr,a,resumos):
    conferir_arquivos(RAIZ,a['fontes']);conferir_arquivos(p/'fontes',a['fontes'])
    antigo=ler_json(REG/'preservacao_antes.json');conferir_arquivos(RAIZ,antigo['arquivos'])
    salvar_json(p/'preservacao_depois.json',{'utc':agora(),'status':'integro','arquivos_conferidos':len(antigo['arquivos']),'mapa_sha256':sha256(REG/'preservacao_antes.json')})
    manifests=list((p/'carteiras').rglob('manifesto.json'));assert len(manifests)==804
    for z in manifests:conferir_arquivos(z.parent,ler_json(z)['arquivos'])
    q=pd.DataFrame(resumos);assert set(q.chave)=={g['chave'] for g in a['grade']}
    metricas=['retorno_liquido','drawdown_mark_close','exposicao_media','funding_liquido','comissoes','slippage','operacoes','compradas','vendidas','recusas']
    por_bloco=q.groupby(['bloco','modelo','politica','modo','cenario'])[metricas].mean().reset_index()
    globais=por_bloco.groupby(['modelo','politica','modo','cenario'])[metricas].mean().reset_index()
    desvio=q[q.seed.notna()].groupby(['modelo','politica','modo','cenario','seed']).retorno_liquido.mean().reset_index()
    resultados={'utc':agora(),'execucao':ptr,'carteiras':resumos,'medias_por_bloco':por_bloco.to_dict('records'),'medias_globais':globais.to_dict('records'),'retornos_por_seed_media_blocos':desvio.to_dict('records'),
                'limites':'Medias descritivas, blocos independentes/peso igual, nao retorno continuo; periodos retrospectivos; nao garante lucro nem promove modelo; funding real, custos hipoteticos, sem liquidacao Binance certificada.'}
    pub=p/'publicacao';pub.mkdir(exist_ok=False);salvar_json(pub/'resultados.json',resultados)
    salvar_json(pub/'manifesto.json',{'arquivos':{'resultados.json':sha256(pub/'resultados.json')},'carteiras':{z.relative_to(p).as_posix():sha256(z) for z in manifests}})
    fechamento={'utc':agora(),'situacao':'concluido_conferido','execucao':ptr,'concluidas':804,'total':804,'novos_treinamentos':0,'publicacao':(pub/'manifesto.json').relative_to(RAIZ).as_posix(),'publicacao_sha256':sha256(pub/'manifesto.json'),'preservacao_sha256':sha256(p/'preservacao_depois.json')}
    salvar_json(p/'fechamento.json',fechamento);salvar_json(p/'progresso.json',fechamento);salvar_json(REG/'estado.json',fechamento);print('CONCLUIDO',ptr['id'],flush=True)
