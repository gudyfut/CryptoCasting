"""Ablação delimitada, com referências imutáveis, qualificação e autorização."""
import ast
import contextlib
import inspect
import shutil
import traceback
import unittest
from pathlib import Path
from uuid import uuid4
import pandas as pd
from infraestrutura.artefatos import (RAIZ, agora, identidade, ler_json, salvar_json,
                                    sha256, conferir_arquivos, fontes as listar_fontes)
from treinamento.ambiente import conferir as ambiente_base
from treinamento.preservacao import conferir, publicar as selar, exclusividade
from treinamento.ciclo import reproducao
from modelos.consumo import ConsumoModelos
from experimento_cryptomamba import ciclo as anterior
from .treino import ajustar, avaliar

REGISTROS = RAIZ/'registros/otimizador'
CONFIG = 'configuracoes/cryptomamba_adamw_001.json'
PROTOCOLO = 'docs/protocolo_otimizador_cryptomamba.md'
SEEDS = [17,42,2026,7,123,31415]
ORDEM = [42,17,2026,7,123,31415]


def configuracao():
    c=ler_json(RAIZ/CONFIG);b=anterior.configuracao()
    esperado=dict(b,versao='cryptomamba-adamw-1.0',ciclo='cryptomamba_otimizador_001',
                  hipotese=c['hipotese'],comparacao_primaria=c['comparacao_primaria'],
                  otimizador=dict(b['otimizador'],nome='AdamW'))
    if c!=esperado or c['seeds']!=SEEDS or c['orcamento_ajustes_reais']!=6:
        raise ValueError('Além da identificação, somente Adam → AdamW pode mudar.')
    return c


def equivalencia_treinador():
    a=(RAIZ/'experimento_cryptomamba/treino.py').read_text(encoding='utf-8')
    b=(RAIZ/'experimento_otimizador/treino.py').read_text(encoding='utf-8')
    assert a.count('torch.optim.Adam(')==1 and b.count('torch.optim.AdamW(')==1
    b=b.replace('torch.optim.AdamW(','torch.optim.Adam(').replace(
        'from experimento_cryptomamba.modelo import criar_rede','from .modelo import criar_rede')
    aa,bb=ast.parse(a),ast.parse(b)
    # Docstrings editoriais não são mudança científica.
    aa.body=aa.body[1:];bb.body=bb.body[1:]
    if ast.dump(aa,include_attributes=False)!=ast.dump(bb,include_attributes=False):
        raise ValueError('Treinador difere além da fábrica do otimizador.')
    return {'ast_demais_instrucoes_identico':True,'mudanca':'torch.optim.Adam → torch.optim.AdamW',
            'referencia_sha256':sha256(RAIZ/'experimento_cryptomamba/treino.py')}


def ambiente():
    import torch
    a=ambiente_base()
    a['implementacoes_otimizadores']={nome:sha256(Path(inspect.getfile(getattr(torch.optim,nome))))
                                     for nome in ('Adam','AdamW')}
    return a


def fontes():
    fs=anterior.fontes();fs.update(listar_fontes('experimento_otimizador','tests_otimizador','backtest_carteira'))
    for nome in (CONFIG,PROTOCOLO,'run_otimizador.py'):
        fs[nome]=sha256(RAIZ/nome)
    return fs


def referencias():
    p,f,consumo,partes,_=anterior.conferir_execucao()
    if ler_json(p/'progresso.json')['status']!='concluido' or ler_json(p/'processo.json')['ativo']:
        raise ValueError('CryptoMamba anterior não encerrado.')
    pp=ler_json(p/'publicacao.json');pub=p/pp['pasta']
    conferir_arquivos(pub,{'manifesto.json':pp['manifesto_sha256']})
    conferir_arquivos(pub,ler_json(pub/'manifesto.json')['arquivos'])
    refs={k:RAIZ/v['tentativa_origem'] for k,v in ler_json(pub/'resultados.json')['por_ajuste'].items()}
    if len(refs)!=59:raise ValueError('Esperadas59referências preservadas.')
    for t in refs.values():conferir(t)
    return consumo,partes,refs,pub


def preservacao(refs,pub):
    guard=ler_json(RAIZ/'registros/cryptomamba/preservacao_antes.json')['arquivos'].copy()
    ptr=ler_json(RAIZ/'registros/cryptomamba/execucao.json');p=RAIZ/ptr['pasta']
    guard.update(ler_json(p/'congelamento.json')['contrato']['fontes'])
    guard[ptr['pasta']+'/congelamento.json']=ptr['congelamento_sha256']
    guard[ptr['pasta']+'/protocolo.md']=sha256(p/'protocolo.md')
    for t in refs.values():
        for nome,h in ler_json(t/'conclusao.json')['arquivos'].items():
            guard[(t/nome).relative_to(RAIZ).as_posix()]=h
        guard[(t/'conclusao.json').relative_to(RAIZ).as_posix()]=sha256(t/'conclusao.json')
    for nome,h in ler_json(pub/'manifesto.json')['arquivos'].items():guard[(pub/nome).relative_to(RAIZ).as_posix()]=h
    guard[(pub/'manifesto.json').relative_to(RAIZ).as_posix()]=sha256(pub/'manifesto.json')
    bp=ler_json(RAIZ/'registros/backtest_carteira/execucao_atual.json');b=RAIZ/bp['pasta']
    assert ler_json(b/'progresso.json')['status']=='concluido' and not ler_json(b/'processo.json')['ativo']
    guard.update(ler_json(RAIZ/'registros/backtest_carteira/revisao_loader/preservacao_antes.json')['arquivos'])
    guard[bp['pasta']+'/congelamento.json']=bp['congelamento_sha256']
    for nome,h in ler_json(b/'resultados/manifesto.json')['arquivos'].items():guard[(b/'resultados'/nome).relative_to(RAIZ).as_posix()]=h
    guard[(b/'resultados/manifesto.json').relative_to(RAIZ).as_posix()]=sha256(b/'resultados/manifesto.json')
    for pasta in ('registros/backtest_carteira/entrega/fechamento_20261030','registros/cryptomamba/entrega/907a54b2c063464b9c7e8bfbcda3c525'):
        for t in (RAIZ/pasta).rglob('*'):
            if t.is_file():guard[t.relative_to(RAIZ).as_posix()]=sha256(t)
    conferir_arquivos(RAIZ,guard)
    return guard


def qualificar():
    from tests_modelos.apoio import conjunto
    p=REGISTROS/'qualificacoes'/uuid4().hex;p.mkdir(parents=True);fs=fontes()
    for nome in fs:
        d=p/'fontes'/nome;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(RAIZ/nome,d)
    salvar_json(p/'inicio.json',{'utc':agora(),'fontes':fs,'natureza':'sintético; zero ajustes de mercado'})
    try:
        c=configuracao();v={'natureza':'sintetico','familia':'cryptomamba_adamw'}
        consumo=ConsumoModelos(conjunto(),'qualificacao_otimizador')
        with (p/'qualificacao.log').open('w',encoding='utf-8',buffering=1) as log:
            with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                eq=equivalencia_treinador()
                suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromName(nome) for nome in
                    ('tests_otimizador.test_ablação','tests_backtest_carteira.test_carteira','tests_backtest_carteira.test_mercado')])
                r=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
                if not r.wasSuccessful() or r.skipped:raise ValueError('Qualificação reprovada.')
                for nome in ('a','b'):
                    d=p/nome;d.mkdir();cfg=dict(c,treino=dict(c['treino'],epocas=2,paciencia=2))
                    rede,aj=ajustar(consumo,42,cfg,d,v);avaliar(consumo,consumo._conjunto.partes,cfg,d,v,rede,aj);del rede
                repeticao=reproducao(p/'a',p/'b',c['reproducao'])
        if fontes()!=fs:raise ValueError('Fontes alteradas durante a qualificação.')
        salvar_json(p/'qualificacao.json',{'status':'aprovado','utc':agora(),'fontes':fs,'ambiente':ambiente(),
                    'ast':eq,'testes':r.testsRun,'skips':0,'controle_sintetico':repeticao,'ajustes_reais':0,
                    'arquivos':{t.relative_to(p).as_posix():sha256(t) for t in p.rglob('*') if t.is_file()}})
    except BaseException:
        salvar_json(p/'falha.json',{'utc':agora(),'erro':traceback.format_exc()});raise
    return p/'qualificacao.json'


def validar_qualificacao(caminho):
    p=Path(caminho).resolve();q=ler_json(p)
    if q['status']!='aprovado' or q['fontes']!=fontes() or q['ambiente']!=ambiente() or q['ajustes_reais']!=0:
        raise ValueError('Qualificação inválida ou desatualizada.')
    conferir_arquivos(p.parent,q['arquivos']);return p


def preparar(qualificacao):
    if (REGISTROS/'execucao.json').exists():raise FileExistsError('Já há execução preparada; não duplicar.')
    q=validar_qualificacao(qualificacao);c=configuracao();consumo,partes,refs,pub=referencias()
    guard=preservacao(refs,pub)
    contrato={'configuracao':c,'fontes':fontes(),'ambiente':ambiente(),'consumo':consumo.especificacao.identidade,
        'referencias':{k:{'pasta':t.relative_to(RAIZ).as_posix(),'conclusao_sha256':sha256(t/'conclusao.json')} for k,t in refs.items()},
        'publicacao_anterior':pub.relative_to(RAIZ).as_posix(),
        'qualificacao':{'arquivo':q.relative_to(RAIZ).as_posix(),'sha256':sha256(q)},
        'dependencias':{c[k]:sha256(RAIZ/c[k]/'manifesto.json') for k in ('entradas_pasta','mercado_pasta')},
        'protocolo_sha256':sha256(RAIZ/PROTOCOLO),'ast':equivalencia_treinador()}
    codigo=identidade(contrato)[:20];p=RAIZ/f'dados/experimentos/cryptomamba_adamw_{codigo}'
    p.mkdir(parents=True,exist_ok=False)
    for nome in contrato['fontes']:
        d=p/'fontes'/nome;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(RAIZ/nome,d)
    shutil.copy2(RAIZ/PROTOCOLO,p/'protocolo.md');salvar_json(p/'congelamento.json',{'id':codigo,'utc':agora(),'contrato':contrato})
    salvar_json(p/'progresso.json',{'status':'preparado','concluidos':[],'total':6})
    salvar_json(REGISTROS/'preservacao_antes.json',{'utc':agora(),'arquivos':guard})
    ptr={'id':codigo,'pasta':p.relative_to(RAIZ).as_posix(),'congelamento_sha256':sha256(p/'congelamento.json')}
    salvar_json(REGISTROS/'execucao.json',ptr)
    salvar_json(REGISTROS/'estado.json',{'situacao':'preparado_qualificado','execucao':ptr,'preservados':len(guard),'novos_planejados':6,'herdados':59})
    return ptr


def conferir_execucao():
    ptr=ler_json(REGISTROS/'execucao.json');p=RAIZ/ptr['pasta'];conferir_arquivos(p,{'congelamento.json':ptr['congelamento_sha256']})
    f=ler_json(p/'congelamento.json');c=f['contrato']
    assert identidade(c)[:20]==ptr['id']==f['id'] and c['configuracao']==configuracao() and c['ambiente']==ambiente()
    conferir_arquivos(RAIZ,c['fontes']);conferir_arquivos(p/'fontes',c['fontes'])
    conferir_arquivos(p,{'protocolo.md':c['protocolo_sha256']})
    validar_qualificacao(RAIZ/c['qualificacao']['arquivo'])
    conferir_arquivos(RAIZ,{c['qualificacao']['arquivo']:c['qualificacao']['sha256']})
    consumo,partes,refs,pub=referencias()
    assert c['consumo']==consumo.especificacao.identidade
    assert c['referencias']=={k:{'pasta':t.relative_to(RAIZ).as_posix(),'conclusao_sha256':sha256(t/'conclusao.json')} for k,t in refs.items()}
    conferir_arquivos(RAIZ,ler_json(REGISTROS/'preservacao_antes.json')['arquivos'])
    return p,f,consumo,partes,refs,pub


def validar_autorizacao(caminho,codigo):
    a=ler_json(caminho)
    if a.get('execucao')!=codigo or a.get('seeds')!=SEEDS or a.get('ajustes_reais_total')!=6 or a.get('abordagem')!='cryptomamba_adamw' or not a.get('mensagem_usuario'):
        raise ValueError('Autorização fora da identidade/orçamento.')
    return a


def executar(autorizacao,retomar=False):
    p,f,consumo,partes,refs,pub=conferir_execucao();c=f['contrato']['configuracao']
    a=validar_autorizacao(autorizacao,f['id'])
    with exclusividade(p,retomar):
        status=ler_json(p/'progresso.json')['status']
        if status=='concluido':raise ValueError('Não repetir treinamento concluído.')
        if status!='preparado' and not retomar:raise ValueError('Investigar antes de retomar.')
        if (p/'autorizacao.json').exists():assert ler_json(p/'autorizacao.json')==a
        else:salvar_json(p/'autorizacao.json',a)
        prontas={}
        try:
            for s in ORDEM:
                raiz=p/'celulas'/f'cryptomamba_adamw_{s}';ant=sorted(raiz.glob('tentativa_*'))
                fechadas=[t for t in ant if (t/'conclusao.json').exists()]
                if len(fechadas)>1:raise ValueError('Tentativas ambíguas.')
                if fechadas:t=fechadas[0];conferir(t)
                else:
                    t=raiz/f'tentativa_{len(ant)+1:03d}';t.mkdir(parents=True)
                    v={'execucao':f['id'],'seed':s,'familia':'cryptomamba_adaptado','identidade_consumo':consumo.especificacao.identidade,'configuracao':c}
                    salvar_json(t/'inicio.json',{'utc':agora(),'vinculo':v,'anteriores_preservadas':[x.name for x in ant]})
                    salvar_json(p/'progresso.json',{'status':'executando','seed_atual':s,'concluidos':list(prontas),'total':6,'utc':agora()})
                    try:
                        with (t/'treinamento.log').open('w',encoding='utf-8',buffering=1) as log:
                            with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                                rede,r=ajustar(consumo,s,c,t,v)
                                if r['parametros']!=139317:raise ValueError('Capacidade inesperada.')
                                avaliar(consumo,partes,c,t,v,rede,r);del rede
                        selar(t)
                    except BaseException:
                        salvar_json(t/'falha.json',{'utc':agora(),'erro':traceback.format_exc()});raise
                prontas[s]=t
            conferir_arquivos(RAIZ,f['contrato']['fontes'])
            conferir_arquivos(RAIZ,ler_json(REGISTROS/'preservacao_antes.json')['arquivos'])
            salvar_json(p/'progresso.json',{'status':'concluido','concluidos':list(prontas),'total':6,'utc':agora()})
        except BaseException:
            salvar_json(p/'progresso.json',{'status':'interrompido','concluidos':list(prontas),'total':6,'utc':agora(),'erro':traceback.format_exc()});raise
