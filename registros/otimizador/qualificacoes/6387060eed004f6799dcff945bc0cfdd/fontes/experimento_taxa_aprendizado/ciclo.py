"""Grade24 congelada de uma vez; componentes científicos anteriores intactos."""
import contextlib
import shutil
import traceback
from pathlib import Path
from uuid import uuid4
import pandas as pd
from infraestrutura.artefatos import RAIZ,agora,identidade,ler_json,salvar_json,sha256,conferir_arquivos,fontes as listar_fontes
from treinamento.ambiente import conferir as ambiente
from treinamento.preservacao import publicar as selar,conferir,exclusividade
from treinamento.ciclo import reproducao
from treinamento.neural import ajustar
from treinamento.avaliar import avaliar
from modelos.consumo import ConsumoModelos
from experimento_complemento16.ciclo import conferir_execucao as abrir_anterior,fontes as fontes_anteriores
from avaliacao.publicacao import conferir_previsoes
from .publicacao import publicar

REGISTROS=RAIZ/'registros/taxa_aprendizado'
CONFIG='configuracoes/taxa_aprendizado_mamba_001.json'
PROTOCOLO='docs/protocolo_taxa_aprendizado.md'
ESTADOS=[8,16,32,64]
SEEDS=[17,42,2026,7,123,31415]
ORDEM_SEEDS=[42,17,2026,7,123,31415]
PARAMETROS={8:17185,16:20257,32:26401,64:38689}


def grade():
    g=ler_json(RAIZ/CONFIG)
    if (g['estados']!=ESTADOS or g['seeds']!=SEEDS or g['ordem_seeds']!=ORDEM_SEEDS or g['ajustes_reais_total']!=24
        or g['taxa_referencia']!=.0002 or g['taxa_candidata']!=.0001
        or g['configuracoes']!={str(n):f'configuracoes/mamba_taxa0001_estado{n}_001.json' for n in ESTADOS}):raise ValueError('Grade fora da autorização24.')
    return g


def configuracao(n):
    if type(n) is not int or n not in ESTADOS:raise ValueError('Estado fora da grade.')
    c=ler_json(RAIZ/grade()['configuracoes'][str(n)]);b=ler_json(RAIZ/'configuracoes/mamba_estado16_complemento_001.json')
    especiais={'versao','ciclo','hipotese','configuracao_modelos','mamba','controle','treino'}
    if set(c)!=set(b):raise ValueError('Campos divergentes.')
    for k in set(b)-especiais:
        if c[k]!=b[k]:raise ValueError(f'Fator extra alterado: {k}')
    if c['mamba']!=dict(b['mamba'],estado=n) or c['treino']!=dict(b['treino'],taxa_aprendizado=.0001):raise ValueError('Mais de uma alteração dentro do estado.')
    a=ler_json(RAIZ/c['configuracao_modelos']);z=ler_json(RAIZ/'configuracoes/modelos_ohlcv24_001.json');z['mamba']['estado']=n
    if a!=z:raise ValueError('Arquitetura contém diferença extra.')
    return c


def fontes():
    f=fontes_anteriores();f.update(listar_fontes('experimento_taxa_aprendizado','tests_taxa_aprendizado'))
    for p in [CONFIG,'run_taxa_aprendizado.py']+[f'configuracoes/{prefixo}_estado{n}_001.json' for n in ESTADOS for prefixo in ('mamba_taxa0001','modelos_mamba_taxa0001')]:f[p]=sha256(RAIZ/p)
    return f


def referencias():
    p,f,consumo,partes,refs=abrir_anterior()
    if ler_json(p/'progresso.json')['status']!='concluido' or ler_json(p/'processo.json')['ativo']:raise ValueError('Referência não encerrada.')
    a=ler_json(RAIZ/'registros/complemento_estado16/conferencia_conclusao.json');conferir_arquivos(RAIZ,{a['arquivo']:a['sha256']})
    if ler_json(RAIZ/a['arquivo'])['execucao']!=f['id']:raise ValueError('Conferência anterior divergente.')
    pp=ler_json(p/'publicacao.json');pub=p/pp['pasta'];conferir_arquivos(pub,{'manifesto.json':pp['manifesto_sha256']});conferir_arquivos(pub,ler_json(pub/'manifesto.json')['arquivos'])
    r=ler_json(pub/'resultados.json');refs={k:RAIZ/v['tentativa_origem'] for k,v in r['por_ajuste'].items()}
    esperado={f'estado{n}_{s}' for n in ESTADOS for s in SEEDS}|{f'lstm_{s}' for s in (17,42,2026)}|{'naive','arima'}
    if set(refs)!=esperado:raise ValueError('Referências incompletas/ambíguas.')
    for t in refs.values():conferir(t)
    return consumo,partes,refs


def qualificar():
    from tests_modelos.apoio import conjunto
    p=REGISTROS/'qualificacoes'/uuid4().hex;p.mkdir(parents=True);fs=fontes()
    for nome in fs:
        d=p/'fontes'/nome;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(RAIZ/nome,d)
    salvar_json(p/'inicio.json',{'utc':agora(),'fontes':fs,'natureza':'sintético; zero ajustes reais'})
    try:
        controles={};consumo=ConsumoModelos(conjunto(),'qualificacao_taxa0001')
        with (p/'qualificacao.log').open('w',encoding='utf-8',buffering=1) as log:
            with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                for n in ESTADOS:
                    c=configuracao(n);v={'natureza':'sintetico','estado':n,'taxa':.0001}
                    for nome in ('a','b'):
                        d=p/f'estado{n}'/nome;d.mkdir(parents=True)
                        rede,r=ajustar(consumo,'mamba',42,dict(c['treino'],epocas=2,paciencia=2),RAIZ/c['configuracao_modelos'],d,v)
                        assert r['parametros']==PARAMETROS[n]
                        estados=[t for k,t in rede.state_dict().items() if k.endswith('A_log')]
                        assert len(estados)==2 and all(list(t.shape)==[64,n] for t in estados)
                        avaliar(consumo,consumo._conjunto.partes,'mamba',c,d,v,rede,r);del rede
                    controles[str(n)]=reproducao(p/f'estado{n}'/'a',p/f'estado{n}'/'b',c['reproducao'])
                import unittest
                suite=unittest.defaultTestLoader.loadTestsFromName('tests_taxa_aprendizado.test_ciclo')
                resultado=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
                if not resultado.wasSuccessful() or resultado.skipped:raise ValueError('Testes reprovados.')
        if fs!=fontes():raise ValueError('Fontes alteradas na qualificação.')
        salvar_json(p/'qualificacao.json',{'status':'aprovado','utc':agora(),'fontes':fs,'ambiente':ambiente(),'controles':controles,
            'parametros':PARAMETROS,'ajustes_reais':0,'testes':resultado.testsRun,'skips':0,
            'arquivos':{t.relative_to(p).as_posix():sha256(t) for t in p.rglob('*') if t.is_file()}})
    except BaseException:
        salvar_json(p/'falha.json',{'utc':agora(),'erro':traceback.format_exc()});raise
    return p/'qualificacao.json'


def validar_qualificacao(caminho):
    p=Path(caminho).resolve();q=ler_json(p)
    if q['status']!='aprovado' or q['fontes']!=fontes() or q['ambiente']!=ambiente() or q['ajustes_reais']!=0:raise ValueError('Qualificação divergente.')
    conferir_arquivos(p.parent,q['arquivos']);return p


def preparar(qualificacao):
    q=validar_qualificacao(qualificacao);g=grade();configs={str(n):configuracao(n) for n in ESTADOS};consumo,partes,refs=referencias()
    contrato={'grade':g,'configuracoes':configs,'fontes':fontes(),'ambiente':ambiente(),'consumo':consumo.especificacao.identidade,
        'referencias':{k:{'pasta':t.relative_to(RAIZ).as_posix(),'conclusao_sha256':sha256(t/'conclusao.json')} for k,t in refs.items()},
        'qualificacao':{'arquivo':q.relative_to(RAIZ).as_posix(),'sha256':sha256(q)},'protocolo_sha256':sha256(RAIZ/PROTOCOLO)}
    codigo=identidade(contrato)[:20];p=RAIZ/f'dados/experimentos/taxa_aprendizado_{codigo}'
    if p.exists() or (REGISTROS/'execucao.json').exists():raise FileExistsError('Já preparado; não duplicar.')
    p.mkdir(parents=True)
    for nome in contrato['fontes']:
        d=p/'fontes'/nome;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(RAIZ/nome,d)
    shutil.copy2(RAIZ/PROTOCOLO,p/'protocolo.md')
    salvar_json(p/'congelamento.json',{'id':codigo,'utc':agora(),'contrato':contrato})
    salvar_json(p/'progresso.json',{'status':'preparado','concluidos':[],'total':24})
    r={'id':codigo,'pasta':p.relative_to(RAIZ).as_posix(),'congelamento_sha256':sha256(p/'congelamento.json')};salvar_json(REGISTROS/'execucao.json',r);return r


def conferir_execucao():
    r=ler_json(REGISTROS/'execucao.json');p=RAIZ/r['pasta'];conferir_arquivos(p,{'congelamento.json':r['congelamento_sha256']})
    f=ler_json(p/'congelamento.json');c=f['contrato']
    if f['id']!=r['id'] or identidade(c)[:20]!=r['id'] or c['grade']!=grade() or c['configuracoes']!={str(n):configuracao(n) for n in ESTADOS}:raise ValueError('Identidade/configuração divergente.')
    conferir_arquivos(RAIZ,c['fontes']);conferir_arquivos(p/'fontes',c['fontes']);conferir_arquivos(p,{'protocolo.md':c['protocolo_sha256']})
    conferir_arquivos(RAIZ,{c['qualificacao']['arquivo']:c['qualificacao']['sha256']});validar_qualificacao(RAIZ/c['qualificacao']['arquivo'])
    consumo,partes,refs=referencias();atuais={k:{'pasta':t.relative_to(RAIZ).as_posix(),'conclusao_sha256':sha256(t/'conclusao.json')} for k,t in refs.items()}
    if atuais!=c['referencias'] or consumo.especificacao.identidade!=c['consumo']:raise ValueError('Herança/dados alterados.')
    return p,f,consumo,partes,refs


def validar_autorizacao(caminho,codigo):
    a=ler_json(caminho)
    if (a.get('execucao')!=codigo or a.get('estados')!=ESTADOS or a.get('seeds')!=SEEDS or a.get('ajustes_reais_total')!=24
        or a.get('taxa_referencia')!=.0002 or a.get('taxa_candidata')!=.0001 or not a.get('mensagem_usuario')):raise ValueError('Autorização incompatível com24 ajustes.')
    return a


def executar(autorizacao,retomar=False):
    p,f,consumo,partes,refs=conferir_execucao();g=f['contrato']['grade'];configs={int(n):c for n,c in f['contrato']['configuracoes'].items()};a=validar_autorizacao(autorizacao,f['id'])
    with exclusividade(p,retomar):
        status=ler_json(p/'progresso.json')['status']
        if status=='concluido':raise ValueError('Executor encerrado não deve ser repetido.')
        if status!='preparado' and not retomar:raise ValueError('Retomada exige investigação.')
        if (p/'autorizacao.json').exists():
            if ler_json(p/'autorizacao.json')!=a:raise ValueError('Autorização alterada.')
        else:salvar_json(p/'autorizacao.json',a)
        prontas={}
        try:
            for n in ESTADOS:
                c=configs[n]
                for s in ORDEM_SEEDS:
                    raiz=p/'celulas'/f'estado{n}_mamba_{s}';anteriores=sorted(raiz.glob('tentativa_*'));fechadas=[t for t in anteriores if (t/'conclusao.json').exists()]
                    if len(fechadas)>1:raise ValueError('Conclusões ambíguas; não selecionar tentativa.')
                    if fechadas:t=fechadas[0];conferir(t)
                    else:
                        t=raiz/f'tentativa_{len(anteriores)+1:03d}';t.mkdir(parents=True)
                        v={'execucao':f['id'],'seed':s,'estado':n,'taxa':.0001,'identidade_consumo':consumo.especificacao.identidade,'treino':c['treino']}
                        salvar_json(t/'inicio.json',{'utc':agora(),'vinculo':v,'anteriores_preservadas':[x.name for x in anteriores]})
                        salvar_json(p/'progresso.json',{'status':'executando','estado_atual':n,'seed_atual':s,'concluidos':[f'{e}_{z}' for e,z in prontas],'total':24,'utc':agora()})
                        try:
                            with (t/'treinamento.log').open('w',encoding='utf-8',buffering=1) as log:
                                with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                                    rede,r=ajustar(consumo,'mamba',s,c['treino'],RAIZ/c['configuracao_modelos'],t,v)
                                    if r['parametros']!=PARAMETROS[n]:raise ValueError('Capacidade divergente.')
                                    avaliar(consumo,partes,'mamba',c,t,v,rede,r);del rede
                            selar(t)
                        except BaseException:
                            salvar_json(t/'falha.json',{'utc':agora(),'erro':traceback.format_exc()});raise
                    prontas[n,s]=t
                salvar_json(p/f'estado{n}_concluido.json',{'utc':agora(),'estado':n,'seeds':SEEDS,'tentativas':{str(s):{'pasta':prontas[n,s].relative_to(RAIZ).as_posix() if prontas[n,s].is_relative_to(RAIZ) else str(prontas[n,s]),'conclusao_sha256':sha256(prontas[n,s]/'conclusao.json')} for s in SEEDS}})
            if set(prontas)!={(n,s) for n in ESTADOS for s in SEEDS}:raise ValueError('Cobertura incompleta.')
            conferir_arquivos(RAIZ,f['contrato']['fontes'])
            for t in prontas.values():conferir(t)
            salvar_json(p/'progresso.json',{'status':'publicando','concluidos':[f'{n}_{s}' for n,s in prontas],'total':24,'utc':agora()})
            publicar(p,g,configs,partes,prontas,refs)
            salvar_json(p/'progresso.json',{'status':'concluido','concluidos':[f'{n}_{s}' for n,s in prontas],'total':24,'utc':agora()})
        except BaseException:
            salvar_json(p/'progresso.json',{'status':'interrompido','concluidos':[f'{n}_{s}' for n,s in prontas],'total':24,'utc':agora(),'erro':traceback.format_exc()});raise


def conferir_conclusao():
    import torch
    p,f,consumo,partes,refs=conferir_execucao();assert ler_json(p/'progresso.json')['status']=='concluido' and not ler_json(p/'processo.json')['ativo']
    assert set(ler_json(p/'progresso.json')['concluidos'])=={f'{n}_{s}' for n in ESTADOS for s in SEEDS}
    pp=ler_json(p/'publicacao.json');pub=p/pp['pasta'];conferir_arquivos(pub,{'manifesto.json':pp['manifesto_sha256']});conferir_arquivos(pub,ler_json(pub/'manifesto.json')['arquivos'])
    rp=ler_json(pub/'resultados.json');assert rp['novos']==24 and rp['herdados']==29 and len(rp['por_ajuste'])==53
    auditoria={}
    for n in ESTADOS:
        for s in SEEDS:
            raiz=p/'celulas'/f'estado{n}_mamba_{s}';ts=[t for t in raiz.glob('tentativa_*') if (t/'conclusao.json').exists()];assert len(ts)==1
            t=ts[0];conferir(t);r=ler_json(t/'resultado.json');assert r['recarga_exata'] and r['parametros']==PARAMETROS[n]
            sel=ler_json(t/'selecao.json');conferir_arquivos(t,{sel['arquivo']:sel['sha256']})
            m=torch.load(t/sel['arquivo'],map_location='cpu',weights_only=True)['modelo']
            assert m['configuracao']['mamba']['estado']==n and m['especificacao']['identidade']==f['contrato']['consumo']
            aa=[v for k,v in m['pesos'].items() if k.endswith('A_log')];assert len(aa)==2 and all(list(v.shape)==[64,n] for v in aa)
            assert sum(v.numel() for v in m['pesos'].values())==PARAMETROS[n]
            melhor=min(ler_json(t/'epocas.json'),key=lambda e:(e['mse_validacao'],e['epoca']))
            assert melhor['epoca']==sel['epoca']==r['epoca_selecionada'] and melhor['mse_validacao']==sel['mse_validacao']==r['metricas']['validacao']['mse']
            auditoria[f'{n}_{s}']={b:conferir_previsoes(pd.read_parquet(t/f'previsoes_{b}.parquet'),partes[b],r['metricas'].get(b)) for b in ('validacao','teste','operacional')}
    d=REGISTROS/'conferencias'/uuid4().hex;d.mkdir(parents=True)
    salvar_json(d/'conclusao.json',{'status':'aprovado','utc':agora(),'execucao':f['id'],'novos':24,'herdados':29,'auditoria':auditoria,'publicacao':pub.relative_to(RAIZ).as_posix(),
        'limites':'Hashes,cobertura,dimensões,seleção e métricas conferidos; recarga/Spot atestadas pelo executor/publicação. Sem repetição real extra.'})
    recibo={'arquivo':(d/'conclusao.json').relative_to(RAIZ).as_posix(),'sha256':sha256(d/'conclusao.json')};salvar_json(REGISTROS/'conferencia_conclusao.json',recibo);return recibo
