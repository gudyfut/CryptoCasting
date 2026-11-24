import itertools
import os
import platform
import shutil
import subprocess
import sys
import traceback
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,agora,ler_json,salvar_json,sha256,identidade,conferir_arquivos
from simulacao_operacoes.previsoes import COLUNAS,diarias
from simulacao_operacoes.smart.mercado import contrato_spot,carregar
from simulacao_operacoes.revisada.simulador import simular
from simulacao_operacoes.revisada.auditoria import conferir
from .publicacao import publicar

REG=RAIZ/'registros/revisao_operacional'


def grade(cfg):
    itens=[]
    for b,v,s,p,a,c in itertools.product(cfg['blocos'],cfg['versoes'],cfg['seeds'],cfg['politicas'],cfg['bracos'],cfg['custos']):
        itens.append({'bloco':b,'modelo':v,'seed':s,'politica':p,'braco':a,'cenario':c,'benchmark':None,'serie':f'{b}/{v}/{s}'})
    for b,v,a,c in itertools.product(cfg['blocos'],['caixa','comprar_manter'],cfg['bracos'],cfg['custos']):
        itens.append({'bloco':b,'modelo':v,'seed':None,'politica':'smart','braco':a,'cenario':c,'benchmark':v,'serie':f'{b}/astra/{cfg["seeds"][0]}'})
    for x in itens:x['chave']='/'.join(str(x[k]) for k in ['bloco','modelo','seed','politica','braco','cenario'])
    assert len(itens)==cfg['simulacoes_total']==len({x['chave'] for x in itens})
    return itens


def ler_series(vinculos):
    series={};comuns={}
    for chave,v in vinculos.items():
        p=RAIZ/v['pasta'];assert sha256(p/'conclusao.json')==v['conclusao_sha256']
        conferir_arquivos(p,ler_json(p/'conclusao.json')['arquivos'])
        d=diarias(pd.read_parquet(p/'previsoes_teste.parquet')[COLUNAS]);b=chave.split('/')[0]
        conhecidos=d.drop(columns='previsao')
        if b in comuns:pd.testing.assert_frame_equal(conhecidos,comuns[b])
        else:comuns[b]=conhecidos
        series[chave]=d
    assert len(series)==64
    return series


def fontes():
    ptr=ler_json(RAIZ/'registros/smart_mercados/execucao.json')
    pai=RAIZ/ptr['pasta'];assert sha256(pai/'congelamento.json')==ptr['congelamento_sha256']
    originais=ler_json(pai/'congelamento.json')['assinatura']['fontes']
    conferir_arquivos(RAIZ,originais)
    arquivos=[]
    for pasta in ['simulacao_operacoes/revisada','experimentos/revisao_operacional','tests_revisao_operacional']:
        arquivos.extend((RAIZ/pasta).rglob('*.py'))
    arquivos.extend(RAIZ/n for n in ['configuracoes/revisao_operacional_001.json','docs/protocolo_revisao_operacional.md'])
    arquivos.extend((REG/'fontes_publicas').glob('*.json'))
    return dict(originais,**{p.relative_to(RAIZ).as_posix():sha256(p) for p in arquivos})


def preparar():
    REG.mkdir(parents=True,exist_ok=True)
    if (REG/'execucao.json').exists():raise RuntimeError('Preparacao ja existente.')
    cfg=ler_json(RAIZ/'configuracoes/revisao_operacional_001.json');gg=grade(cfg)
    t=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','discover','-s','tests_revisao_operacional','-v'],cwd=RAIZ,capture_output=True,text=True,encoding='utf-8')
    (REG/'qualificacao.log').write_text(t.stdout+t.stderr,encoding='utf-8')
    if t.returncode:raise RuntimeError('Qualificacao reprovada.')
    pai=ler_json(RAIZ/'registros/smart_mercados/execucao.json');p=RAIZ/pai['pasta']
    assert sha256(p/'congelamento.json')==pai['congelamento_sha256']
    f=ler_json(p/'congelamento.json')['assinatura'];conferir_arquivos(RAIZ,f['fontes'])
    fim_pai=ler_json(p/'fechamento.json');assert fim_pai['situacao']=='concluido_conferido'
    assert sha256(p/'publicacao/manifesto.json')==fim_pai['publicacao_sha256']
    pub=ler_json(p/'publicacao/manifesto.json');conferir_arquivos(p/'publicacao',pub['arquivos']);conferir_arquivos(p,pub['carteiras'])
    for nome in pub['carteiras']:
        manifesto=p/nome;conferir_arquivos(manifesto.parent,ler_json(manifesto)['arquivos'])
    antiga=ler_json(RAIZ/'registros/smart_mercados/preservacao_antes.json')['arquivos']
    conferir_arquivos(RAIZ,antiga)
    antiga.update(f['fontes'])
    antiga.update({x.relative_to(RAIZ).as_posix():sha256(x) for x in p.rglob('*') if x.is_file()})
    salvar_json(REG/'preservacao_antes.json',{'utc':agora(),'arquivos':antiga})
    spot=contrato_spot();mercados=carregar(spot,f['futuros']);series=ler_series(f['series'])
    cobertura={}
    for b in cfg['blocos']:
        d=series[f'{b}/astra/{cfg["seeds"][0]}'];s=mercados['spot']
        indices=[s.indice(int(v.timestamp()//60)-1) for v in d.origem_utc]
        np.testing.assert_allclose(d.close,s.negocio[indices,3],rtol=1e-12,atol=1e-10)
        final=int(d.origem_utc.iloc[-1].timestamp()//60)+1441
        for m in mercados.values():m.indice(final)
        cobertura[b]={'dias':len(d),'primeira_origem':d.origem_utc.iloc[0].isoformat(),'fim_minuto':final}
    assinatura={'configuracao':cfg,'fontes':fontes(),'grade':gg,'series':f['series'],'spot':spot,'futuros':f['futuros'],'pai':pai,
        'cobertura':cobertura,'preservacao_sha256':sha256(REG/'preservacao_antes.json'),'qualificacao_sha256':sha256(REG/'qualificacao.log'),
        'ambiente':{'python':sys.version,'pandas':pd.__version__,'plataforma':platform.platform()}}
    codigo=identidade(assinatura)[:20];destino=RAIZ/'dados/experimentos'/('revisao_operacional_'+codigo);destino.mkdir(exist_ok=False)
    for nome in assinatura['fontes']:
        d=destino/'fontes'/nome;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(RAIZ/nome,d)
    salvar_json(destino/'congelamento.json',{'id':codigo,'utc':agora(),'assinatura':assinatura})
    salvar_json(destino/'autorizacao.json',{'utc':agora(),'origem':'Pedido explicito do pesquisador neste chat: auditar/corrigir simuladores Spot/futuros e apresentar resultados; ADR0026.','escopo':'1200carteiras;64series herdadas;zero treinos;grade/politicas/custos fixados antes dos resultados;sem ordens reais.'})
    ptr={'id':codigo,'pasta':destino.relative_to(RAIZ).as_posix(),'congelamento_sha256':sha256(destino/'congelamento.json')}
    salvar_json(REG/'execucao.json',ptr);salvar_json(REG/'estado.json',{'utc':agora(),'situacao':'preparado_autorizado','execucao':ptr,'total':1200})
    print('PREPARADO',ptr,flush=True)


def executar():
    ptr=ler_json(REG/'execucao.json');p=RAIZ/ptr['pasta']
    assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    f=ler_json(p/'congelamento.json')['assinatura'];assert identidade(f)[:20]==ptr['id']
    if any((p/n).exists() for n in ['processo.json','fechamento.json','incidente.json']):raise RuntimeError('Ciclo ja iniciado: nao repetir.')
    lock=REG/'execucao.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    try:
        os.write(fd,f'{platform.node()}:{os.getpid()}'.encode());os.close(fd)
        salvar_json(p/'processo.json',{'utc':agora(),'pid':os.getpid(),'host':platform.node()})
        conferir_arquivos(RAIZ,f['fontes']);conferir_arquivos(p/'fontes',f['fontes'])
        assert sha256(REG/'preservacao_antes.json')==f['preservacao_sha256']
        mercados=carregar(f['spot'],f['futuros']);series=ler_series(f['series']);resumos=[]
        for i,g in enumerate(f['grade']):
            dest=p/'carteiras'/g['chave'];dest.mkdir(parents=True,exist_ok=False)
            m=mercados['spot' if g['braco']=='spot' else 'futuro']
            r,o,e,c,d=simular(series[g['serie']],m,f['configuracao'],g['politica'],g['braco'],g['cenario'],g['benchmark'])
            auditoria=conferir(r,o,e,m,f['configuracao'],series[g['serie']])
            for nome,valor in [('resumo',r),('ordens',o),('funding',e),('diarios',d),('auditoria',auditoria)]:salvar_json(dest/(nome+'.json'),valor)
            c.to_parquet(dest/'curva.parquet',index=False)
            salvar_json(dest/'manifesto.json',{'grade':g,'arquivos':{z.name:sha256(z) for z in dest.iterdir() if z.is_file()}})
            resumos.append(dict(g,**r,componentes=auditoria['decomposicao_futuros']))
            estado={'utc':agora(),'situacao':'executando','execucao':ptr,'concluidas':i+1,'total':len(f['grade']),'percentual':100*(i+1)/len(f['grade']),'novos_treinamentos':0}
            salvar_json(p/'progresso.json',estado);salvar_json(REG/'estado.json',estado)
            if (i+1)%48==0:print('CARTEIRAS',i+1,'/',len(f['grade']),flush=True)
        publicar(p,ptr,f,resumos)
    except BaseException:
        erro={'utc':agora(),'situacao':'interrompido','execucao':ptr,'erro':traceback.format_exc()}
        salvar_json(p/'incidente.json',erro);salvar_json(REG/'estado.json',erro);raise
    finally:
        if lock.exists():lock.unlink()
