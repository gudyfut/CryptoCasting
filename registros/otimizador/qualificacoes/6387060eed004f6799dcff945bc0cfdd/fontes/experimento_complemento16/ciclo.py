"""Três ajustes novos para completar seis seeds; demais resultados herdados."""
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
from experimento_estados_ampliados.ciclo import conferir_execucao as abrir64,fontes as fontes_anteriores
from avaliacao.publicacao import conferir_previsoes
from .publicacao import publicar

REGISTROS=RAIZ/'registros/complemento_estado16'
CONFIG='configuracoes/mamba_estado16_complemento_001.json'
SEEDS=[17,42,2026,7,123,31415]
NOVAS=[7,123,31415]
PARAMETROS=20257
PROTOCOLO='docs/protocolo_complemento_estado16.md'


def configuracao():
    c=ler_json(RAIZ/CONFIG);b=ler_json(RAIZ/'configuracoes/mamba_estado8_001.json')
    if set(c)!=set(b):raise ValueError('Campos divergentes.')
    for k in set(b)-{'versao','ciclo','hipotese','configuracao_modelos','mamba','controle'}:
        if c[k]!=b[k]:raise ValueError(f'Fator extra alterado: {k}')
    if c['mamba']!=dict(b['mamba'],estado=16) or c['seeds']!=SEEDS:raise ValueError('Estado/seeds divergentes.')
    arq=ler_json(RAIZ/c['configuracao_modelos'])
    if arq!=ler_json(RAIZ/'configuracoes/modelos_ohlcv24_001.json'):raise ValueError('Arquitetura diverge de R0.')
    return c


def fontes():
    f=fontes_anteriores();f.update(listar_fontes('experimento_complemento16','tests_complemento16'))
    for p in (CONFIG,'run_complemento16.py'):f[p]=sha256(RAIZ/p)
    return f


def referencias():
    pasta,f,consumo,partes,refs=abrir64(64)
    if ler_json(pasta/'progresso.json')['status']!='concluido':raise ValueError('Estado64 deve estar encerrado.')
    a=ler_json(RAIZ/'registros/estados_ampliados/estado64/conferencia_conclusao.json')
    conferir_arquivos(RAIZ,{a['arquivo']:a['sha256']})
    if ler_json(RAIZ/a['arquivo'])['execucao']!=f['id']:raise ValueError('Conferência64 divergente.')
    pub=ler_json(pasta/'publicacao.json');p=pasta/pub['pasta']
    conferir_arquivos(p,{'manifesto.json':pub['manifesto_sha256']});conferir_arquivos(p,ler_json(p/'manifesto.json')['arquivos'])
    refs=dict(refs)
    for s in SEEDS:
        t=pasta/'celulas'/f'mamba_{s}'/'tentativa_001';conferir(t);refs[f'estado64_{s}']=t
    if len(refs)!=26 or any(f'estado16_{s}' in refs for s in NOVAS):raise ValueError('Herança/orçamento divergente.')
    return consumo,partes,refs


def qualificar():
    from tests_modelos.apoio import conjunto
    p=REGISTROS/'qualificacoes'/uuid4().hex;p.mkdir(parents=True)
    fs=fontes()
    for nome in fs:
        d=p/'fontes'/nome;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(RAIZ/nome,d)
    salvar_json(p/'inicio.json',{'utc':agora(),'fontes':fs,'natureza':'somente sintético'})
    try:
        c=configuracao();consumo=ConsumoModelos(conjunto(),'complemento16_sintetico');v={'natureza':'sintetico','estado':16}
        with (p/'qualificacao.log').open('w',encoding='utf-8',buffering=1) as log:
            with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                for n in ('a','b'):
                    d=p/n;d.mkdir()
                    rede,r=ajustar(consumo,'mamba',42,dict(c['treino'],epocas=2,paciencia=2),RAIZ/c['configuracao_modelos'],d,v)
                    assert r['parametros']==PARAMETROS
                    assert all(list(t.shape)==[64,16] for k,t in rede.state_dict().items() if k.endswith('A_log'))
                    avaliar(consumo,consumo._conjunto.partes,'mamba',c,d,v,rede,r);del rede
                controle=reproducao(p/'a',p/'b',c['reproducao'])
                import unittest
                suite=unittest.defaultTestLoader.loadTestsFromName('tests_complemento16.test_ciclo')
                resultado=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
                if not resultado.wasSuccessful() or resultado.skipped:raise ValueError('Testes reprovados.')
        if fs!=fontes():raise ValueError('Fontes alteradas durante qualificação.')
        salvar_json(p/'qualificacao.json',{'status':'aprovado','utc':agora(),'fontes':fs,'ambiente':ambiente(),
            'controle_sintetico':controle,'parametros':PARAMETROS,'ajustes_reais':0,'testes':resultado.testsRun,'skips':0,
            'arquivos':{t.relative_to(p).as_posix():sha256(t) for t in p.rglob('*') if t.is_file()}})
    except BaseException:
        salvar_json(p/'falha.json',{'utc':agora(),'erro':traceback.format_exc()});raise
    return p/'qualificacao.json'


def validar_qualificacao(caminho):
    p=Path(caminho).resolve();q=ler_json(p)
    if q['status']!='aprovado' or q['fontes']!=fontes() or q['ambiente']!=ambiente() or q['ajustes_reais']!=0:
        raise ValueError('Qualificação divergente.')
    conferir_arquivos(p.parent,q['arquivos']);return p


def preparar(qualificacao):
    c=configuracao();q=validar_qualificacao(qualificacao);consumo,partes,refs=referencias()
    contrato={'configuracao':c,'fontes':fontes(),'ambiente':ambiente(),'consumo':consumo.especificacao.identidade,
        'seeds_novas':NOVAS,'referencias':{k:{'pasta':t.relative_to(RAIZ).as_posix(),'conclusao_sha256':sha256(t/'conclusao.json')} for k,t in refs.items()},
        'qualificacao':{'arquivo':q.relative_to(RAIZ).as_posix(),'sha256':sha256(q)},'protocolo_sha256':sha256(RAIZ/PROTOCOLO)}
    codigo=identidade(contrato)[:20];p=RAIZ/f'dados/experimentos/complemento_estado16_{codigo}'
    if p.exists() or (REGISTROS/'execucao.json').exists():raise FileExistsError('Já preparado; não duplicar.')
    p.mkdir(parents=True)
    for nome in contrato['fontes']:
        d=p/'fontes'/nome;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(RAIZ/nome,d)
    shutil.copy2(RAIZ/PROTOCOLO,p/'protocolo.md')
    salvar_json(p/'congelamento.json',{'id':codigo,'utc':agora(),'contrato':contrato})
    salvar_json(p/'progresso.json',{'status':'preparado','concluidos':[]})
    r={'id':codigo,'pasta':p.relative_to(RAIZ).as_posix(),'congelamento_sha256':sha256(p/'congelamento.json')}
    salvar_json(REGISTROS/'execucao.json',r);return r


def conferir_execucao():
    r=ler_json(REGISTROS/'execucao.json');p=RAIZ/r['pasta'];conferir_arquivos(p,{'congelamento.json':r['congelamento_sha256']})
    f=ler_json(p/'congelamento.json');c=f['contrato']
    if f['id']!=r['id'] or identidade(c)[:20]!=r['id'] or c['seeds_novas']!=NOVAS:raise ValueError('Identidade divergente.')
    conferir_arquivos(RAIZ,c['fontes']);conferir_arquivos(p/'fontes',c['fontes']);conferir_arquivos(p,{'protocolo.md':c['protocolo_sha256']})
    conferir_arquivos(RAIZ,{c['qualificacao']['arquivo']:c['qualificacao']['sha256']});validar_qualificacao(RAIZ/c['qualificacao']['arquivo'])
    consumo,partes,refs=referencias()
    atuais={k:{'pasta':t.relative_to(RAIZ).as_posix(),'conclusao_sha256':sha256(t/'conclusao.json')} for k,t in refs.items()}
    if atuais!=c['referencias'] or consumo.especificacao.identidade!=c['consumo']:raise ValueError('Herança/dados alterados.')
    return p,f,consumo,partes,refs


def validar_autorizacao(caminho,codigo):
    a=ler_json(caminho)
    if (a.get('execucao')!=codigo or a.get('seeds_novas')!=NOVAS or a.get('seeds_finais')!=SEEDS
        or a.get('ajustes_reais_total')!=3 or not a.get('mensagem_usuario')):raise ValueError('Autorização divergente.')
    return a


def executar(autorizacao,retomar=False):
    p,f,consumo,partes,refs=conferir_execucao();c=f['contrato']['configuracao'];a=validar_autorizacao(autorizacao,f['id'])
    with exclusividade(p,retomar):
        status=ler_json(p/'progresso.json')['status']
        if status=='concluido':raise ValueError('Executor encerrado não deve ser repetido.')
        if status!='preparado' and not retomar:raise ValueError('Retomada exige investigação.')
        if (p/'autorizacao.json').exists():
            if ler_json(p/'autorizacao.json')!=a:raise ValueError('Autorização alterada.')
        else:salvar_json(p/'autorizacao.json',a)
        prontas={}
        try:
            for s in NOVAS:
                raiz=p/'celulas'/f'mamba_{s}';anteriores=sorted(raiz.glob('tentativa_*'));fechadas=[t for t in anteriores if (t/'conclusao.json').exists()]
                if len(fechadas)>1:raise ValueError('Tentativas concluídas ambíguas.')
                if fechadas:t=fechadas[0];conferir(t)
                else:
                    t=raiz/f'tentativa_{len(anteriores)+1:03d}';t.mkdir(parents=True)
                    v={'execucao':f['id'],'seed':s,'estado':16,'identidade_consumo':consumo.especificacao.identidade,'treino':c['treino']}
                    salvar_json(t/'inicio.json',{'utc':agora(),'vinculo':v,'anteriores_preservadas':[x.name for x in anteriores]})
                    salvar_json(p/'progresso.json',{'status':'executando','atual':s,'concluidos':list(prontas),'utc':agora()})
                    try:
                        with (t/'treinamento.log').open('w',encoding='utf-8',buffering=1) as log:
                            with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                                rede,r=ajustar(consumo,'mamba',s,c['treino'],RAIZ/c['configuracao_modelos'],t,v)
                                if r['parametros']!=PARAMETROS:raise ValueError('Capacidade divergente.')
                                avaliar(consumo,partes,'mamba',c,t,v,rede,r);del rede
                        selar(t)
                    except BaseException:
                        salvar_json(t/'falha.json',{'utc':agora(),'erro':traceback.format_exc()});raise
                prontas[s]=t
            if set(prontas)!=set(NOVAS):raise ValueError('Cobertura incompleta.')
            conferir_arquivos(RAIZ,f['contrato']['fontes'])
            for t in prontas.values():conferir(t)
            publicar(p,c,partes,prontas,refs,16)
            salvar_json(p/'progresso.json',{'status':'concluido','concluidos':list(prontas),'utc':agora()})
        except BaseException:
            salvar_json(p/'progresso.json',{'status':'interrompido','concluidos':list(prontas),'utc':agora(),'erro':traceback.format_exc()});raise


def conferir_conclusao():
    import torch
    p,f,consumo,partes,refs=conferir_execucao();assert ler_json(p/'progresso.json')['status']=='concluido'
    assert set(ler_json(p/'progresso.json')['concluidos'])==set(NOVAS) and not ler_json(p/'processo.json')['ativo']
    pp=ler_json(p/'publicacao.json');pub=p/pp['pasta'];conferir_arquivos(pub,{'manifesto.json':pp['manifesto_sha256']});conferir_arquivos(pub,ler_json(pub/'manifesto.json')['arquivos'])
    rpub=ler_json(pub/'resultados.json');assert len(rpub['por_ajuste'])==29
    auditoria={}
    for s in NOVAS:
        ts=[t for t in (p/'celulas'/f'mamba_{s}').glob('tentativa_*') if (t/'conclusao.json').exists()];assert len(ts)==1
        t=ts[0];conferir(t);r=ler_json(t/'resultado.json');assert r['recarga_exata'] and r['parametros']==PARAMETROS
        selecao=ler_json(t/'selecao.json');conferir_arquivos(t,{selecao['arquivo']:selecao['sha256']})
        m=torch.load(t/selecao['arquivo'],map_location='cpu',weights_only=True)['modelo']
        assert m['configuracao']['mamba']['estado']==16 and m['especificacao']['identidade']==f['contrato']['consumo']
        estados=[v for k,v in m['pesos'].items() if k.endswith('A_log')]
        assert len(estados)==2 and all(list(v.shape)==[64,16] for v in estados) and sum(v.numel() for v in m['pesos'].values())==PARAMETROS
        melhor=min(ler_json(t/'epocas.json'),key=lambda x:(x['mse_validacao'],x['epoca']))
        assert melhor['epoca']==selecao['epoca']==r['epoca_selecionada']
        assert melhor['mse_validacao']==selecao['mse_validacao']==r['metricas']['validacao']['mse']
        auditoria[str(s)]={b:conferir_previsoes(pd.read_parquet(t/f'previsoes_{b}.parquet'),partes[b],r['metricas'].get(b)) for b in ('validacao','teste','operacional')}
    d=REGISTROS/'conferencias'/uuid4().hex;d.mkdir(parents=True)
    salvar_json(d/'conclusao.json',{'status':'aprovado','utc':agora(),'execucao':f['id'],'ajustes_novos':3,'herdadas':26,
        'seeds_finais':SEEDS,'auditoria':auditoria,'publicacao':pub.relative_to(RAIZ).as_posix(),
        'limites':'Checkpoint/seleção/métricas conferidos; recarga e operação atestadas pelo executor/publicação. Sem repetição de mercado adicional.'})
    recibo={'arquivo':(d/'conclusao.json').relative_to(RAIZ).as_posix(),'sha256':sha256(d/'conclusao.json')}
    salvar_json(REGISTROS/'conferencia_conclusao.json',recibo);return recibo
