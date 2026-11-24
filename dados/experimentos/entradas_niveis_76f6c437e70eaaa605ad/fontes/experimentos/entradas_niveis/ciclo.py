"""Fila exclusiva, qualificação, congelamento e 64 ajustes novos+2 controles."""
import contextlib
import os
import platform
import shutil
import time
import traceback
import unittest
from pathlib import Path
from uuid import uuid4

from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256, identidade, fontes as listar_fontes
from treinamento.ambiente import conferir as ambiente
from treinamento.neural import ajustar
from treinamento.avaliar import avaliar
from treinamento.preservacao import conferir, publicar as selar, exclusividade, inicio_processo
from treinamento.ciclo import reproducao
from .dados import REG, CONFIG, VARIANTES, preparar as preparar_dados, carregar

PROTOCOLO = 'docs/protocolo_entradas_niveis.md'


def configuracao():
    c = ler_json(RAIZ/CONFIG)
    assert c['variantes_novas'] == VARIANTES and c['variantes'] == ['atual']+VARIANTES
    assert c['seeds'] == [17,42,2026,7,123,31415,271828,161803]
    assert (c['principais_novos'],c['controles_reais'],c['reais_novos_total']) == (64,2,66)
    anterior = ler_json(RAIZ/'configuracoes/huber_blocos_001.json')
    assert c['blocos'] == anterior['blocos'] and c['seeds'] == anterior['seeds']
    assert c['simulacoes_novas'] == 384 and c['simulacoes_herdadas'] == 216
    return c


def grade(c):
    g = []
    for b in c['blocos']:
        for seed in c['ordem_seeds']:
            for variante in VARIANTES:
                g.append({'bloco':b,'variante':variante,'seed':seed,'controle':False})
            if b == 'B1' and seed == 42:
                for variante in VARIANTES:
                    g.append({'bloco':b,'variante':variante,'seed':seed,'controle':True})
    assert len(g) == 66
    return g


def chave(i): return f'{i["bloco"]}_{i["variante"]}_{i["seed"]}'


def receita(c, b, variante, pasta):
    r = ler_json(RAIZ/'configuracoes/mamba16_perda_huber_001.json')
    r.update(versao='entradas-niveis-1', ciclo=c['ciclo'], hipotese='Comparar representações OHLCV mantendo alvo e receita MSE.',
        seeds=c['seeds'], seeds_pareadas=c['seeds'], divisao=c['blocos'][b], bloco=b, variante=variante,
        referencia_execucao=c['predecessor']['id'], entradas_pasta=pasta,
        entradas=['abertura_usdt','maxima_usdt','minima_usdt','fechamento_usdt','volume_btc'],
        representacao='OHLCV em nível, sem log ou timestamp',
        normalizacao='identidade' if variante=='crua' else 'zscore_treino',
        controle='Reprodução sintética e dois controles reais B1/42, antes das outras seeds.',
        perda={'nome':'MSELoss','alvo':'padronizado_treino'})
    return r


def fontes():
    fs = ler_json(RAIZ/'dados/experimentos/huber_blocos_10dac17ea9df2c540c57/congelamento.json')['contrato']['fontes'].copy()
    fs.update(listar_fontes('experimentos/entradas_niveis','tests_entradas_niveis'))
    for n in (CONFIG,PROTOCOLO): fs[n] = sha256(RAIZ/n)
    # Preserva hashes já qualificados, nunca aceita alterações nas dependências.
    for n,h in fs.items():
        if sha256(RAIZ/n) != h: raise ValueError(f'Fonte congelada divergente: {n}')
    return fs


def conferir_mapa(mapa):
    for n,h in mapa.items():
        if sha256(RAIZ/n) != h: raise ValueError(f'Arquivo alterado: {n}')


def planejar():
    if (REG/'plano.json').exists(): raise FileExistsError('Plano já preparado; não duplicar fila.')
    c=configuracao();mapa=preparar_dados();fs=fontes()
    ct={'configuracao':c,'entradas':mapa,'fontes':fs,'grade':grade(c),'predecessor':c['predecessor']}
    plano={'id':identidade(ct)[:20],'utc':agora(),'contrato':ct}
    for n in fs:
        d=REG/'fontes_planejadas'/n;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(RAIZ/n,d)
    salvar_json(REG/'plano.json',plano)
    salvar_json(REG/'estado.json',{'situacao':'preparado_cpu_aguardando_fila','plano':plano['id'],
        'ajustes_novos':66,'referencias_a_herdar':32,'treinamento_mercado_iniciado':False,'utc':agora()})
    return plano


def predecessora(c, exigir_fechamento=True):
    pt=c['predecessor'];p=RAIZ/pt['pasta']
    assert sha256(p/'congelamento.json')==pt['congelamento_sha256']
    f=ler_json(p/'congelamento.json')
    assert identidade(f['contrato'])[:20]==pt['id']
    conferir_mapa(f['contrato']['fontes'])
    if exigir_fechamento:
        fim=ler_json(RAIZ/'registros/huber_blocos/fechamento.json')
        assert fim['situacao']=='concluido_conferido' and fim['execucao']==pt
        assert ler_json(p/'progresso.json')['status']=='concluido'
        assert not ler_json(p/'processo.json')['ativo']
        pp=ler_json(p/'publicacao.json');pub=p/pp['pasta']
        assert sha256(pub/'manifesto.json')==pp['manifesto_sha256']
        for n,h in ler_json(pub/'manifesto.json')['arquivos'].items():
            if sha256(pub/n)!=h: raise ValueError(f'Publicação herdada alterada: {n}')
        return p,f,pub,ler_json(pub/'resultados.json')
    return p,f


def esperar(c):
    p,_=predecessora(c,False)
    while not (RAIZ/'registros/huber_blocos/fechamento.json').exists():
        prog=ler_json(p/'progresso.json');proc=ler_json(p/'processo.json')
        boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        vivo=proc['host']==platform.node() and proc['boot']==boot and inicio_processo(proc['pid'])==proc['inicio_proc']
        if not vivo or prog['status']=='interrompido':
            raise RuntimeError('Predecessora encerrada sem fechamento ou interrompida; investigar, sem iniciar nova rodada.')
        salvar_json(REG/'estado.json',{'situacao':'aguardando_predecessora','utc':agora(),
            'plano':ler_json(REG/'plano.json')['id'],'pid_fila':os.getpid(),
            'predecessora':c['predecessor']['id'],'principais_anteriores_concluidos':prog.get('principais_concluidos'),
            'treinamento_mercado_iniciado':False})
        time.sleep(30)
    predecessora(c)


def qualificar(plano):
    from tests_entradas_niveis.test_ciclo import sinteticos
    p=REG/'qualificacoes'/uuid4().hex;p.mkdir(parents=True)
    fs=plano['contrato']['fontes'];conferir_mapa(fs)
    try:
        controles={}
        with (p/'qualificacao.log').open('w',encoding='utf-8',buffering=1) as log:
            with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromName(n) for n in
                    ('tests_entradas_niveis.test_ciclo','tests_backtest_carteira.test_carteira')])
                resultado=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
                if not resultado.wasSuccessful() or resultado.skipped:raise ValueError('Testes de qualificação reprovados.')
                for variante,x in sinteticos().items():
                    cfg=receita(configuracao(),'B1',variante,'sintetico')
                    cfg['treino']=dict(cfg['treino'],epocas=2,paciencia=2)
                    for nome in ('a','b'):
                        d=p/f'{variante}_{nome}';d.mkdir();v={'natureza':'sintetico','variante':variante}
                        rede,aj=ajustar(x,'mamba',42,cfg['treino'],RAIZ/cfg['configuracao_modelos'],d,v)
                        assert aj['parametros']==20257
                        avaliar(x,x._conjunto.partes,'mamba',cfg,d,v,rede,aj);del rede
                    controles[variante]=reproducao(p/f'{variante}_a',p/f'{variante}_b',cfg['reproducao'])
        carregar(plano['contrato']['entradas']);conferir_mapa(fs)
        q={'status':'aprovado','utc':agora(),'plano':plano['id'],'fontes':fs,'ambiente':ambiente(),
            'testes':resultado.testsRun,'skips':0,'ajustes_sinteticos':4,'reproducao':controles,
            'treinamentos_mercado':0,'arquivos':{f.relative_to(p).as_posix():sha256(f) for f in p.rglob('*') if f.is_file()}}
        salvar_json(p/'qualificacao.json',q);return p/'qualificacao.json'
    except BaseException:
        salvar_json(p/'falha.json',{'utc':agora(),'erro':traceback.format_exc()});raise


def congelar(plano,q):
    if (REG/'execucao.json').exists():raise FileExistsError('Execução já congelada.')
    c=configuracao();pred,pf,pub,rs=predecessora(c)
    guard=ler_json(RAIZ/'registros/huber_blocos/preservacao_antes.json')['arquivos'].copy()
    guard.update(pf['contrato']['fontes'])
    for base in (pred/'fontes',):
        guard.update({(base/n).relative_to(RAIZ).as_posix():h for n,h in pf['contrato']['fontes'].items()})
    for base,m in ((pub,ler_json(pub/'manifesto.json')),):
        guard.update({(base/n).relative_to(RAIZ).as_posix():h for n,h in m['arquivos'].items()})
    # Preserva todas as tentativas da predecessora, incluindo os controles.
    for fim in pred.glob('**/conclusao.json'):
        if 'fontes' in fim.parts:continue
        rec=ler_json(fim)
        if 'arquivos' in rec:
            guard.update({(fim.parent/n).relative_to(RAIZ).as_posix():h for n,h in rec['arquivos'].items()})
            guard[fim.relative_to(RAIZ).as_posix()]=sha256(fim)
    for arquivo in (pred/'congelamento.json',pub/'manifesto.json',RAIZ/'registros/huber_blocos/fechamento.json'):
        guard[arquivo.relative_to(RAIZ).as_posix()]=sha256(arquivo)
    conferir_mapa(guard)
    receitas={b:{v:receita(c,b,v,plano['contrato']['entradas'][b][v]['pasta']) for v in VARIANTES} for b in c['blocos']}
    ct=dict(plano['contrato'],plano=plano['id'],qualificacao={'arquivo':q.relative_to(RAIZ).as_posix(),'sha256':sha256(q)},
        ambiente=ambiente(),receitas=receitas,publicacao_herdada={'pasta':pub.relative_to(RAIZ).as_posix(),
        'manifesto_sha256':sha256(pub/'manifesto.json')},preservacao_sha256=identidade(guard))
    codigo=identidade(ct)[:20];p=RAIZ/f'dados/experimentos/entradas_niveis_{codigo}';p.mkdir(parents=True,exist_ok=False)
    for n in ct['fontes']:
        d=p/'fontes'/n;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(RAIZ/n,d)
    salvar_json(p/'congelamento.json',{'id':codigo,'utc':agora(),'contrato':ct})
    salvar_json(p/'progresso.json',{'status':'preparado','concluidos':[],'principais_concluidos':0,'controles_concluidos':0})
    salvar_json(REG/'preservacao_antes.json',{'arquivos':guard,'utc':agora()})
    pt={'id':codigo,'pasta':p.relative_to(RAIZ).as_posix(),'congelamento_sha256':sha256(p/'congelamento.json')}
    salvar_json(REG/'execucao.json',pt)
    autorizacao=ler_json(REG/'autorizacao_plano.json')
    assert autorizacao['plano']==plano['id'] and autorizacao['plano_sha256']==sha256(REG/'plano.json')
    assert autorizacao['reais_novos_total']==66 and autorizacao['mensagem_usuario']
    salvar_json(REG/'autorizacao.json',dict(autorizacao,execucao=codigo,congelamento_sha256=pt['congelamento_sha256'],
        qualificacao_sha256=sha256(q),vinculacao='Derivação automática do plano explicitamente autorizado, sem mudar orçamento/fontes/receitas.'))
    return pt


def conferir_execucao():
    pt=ler_json(REG/'execucao.json');p=RAIZ/pt['pasta']
    assert sha256(p/'congelamento.json')==pt['congelamento_sha256']
    f=ler_json(p/'congelamento.json');ct=f['contrato']
    assert identidade(ct)[:20]==f['id']==pt['id'] and ct['configuracao']==configuracao()
    conferir_mapa(ct['fontes'])
    for n,h in ct['fontes'].items():assert sha256(p/'fontes'/n)==h
    q=RAIZ/ct['qualificacao']['arquivo'];assert sha256(q)==ct['qualificacao']['sha256']
    qr=ler_json(q);assert qr['status']=='aprovado' and qr['ambiente']==ambiente()==ct['ambiente']
    for n,h in qr['arquivos'].items():assert sha256(q.parent/n)==h
    guard=ler_json(REG/'preservacao_antes.json')['arquivos'];assert identidade(guard)==ct['preservacao_sha256'];conferir_mapa(guard)
    return p,f,carregar(ct['entradas'])


def executar():
    p,f,xs=conferir_execucao();a=ler_json(REG/'autorizacao.json')
    assert a['execucao']==f['id'] and a['reais_novos_total']==66 and a['seeds']==configuracao()['seeds']
    with exclusividade(p):
        assert ler_json(p/'progresso.json')['status']=='preparado','Executor já iniciado; não repetir.'
        salvar_json(p/'autorizacao.json',a);prontas=[];caminhos={}
        try:
            for item in f['contrato']['grade']:
                b,v,seed=item['bloco'],item['variante'],item['seed'];cfg=f['contrato']['receitas'][b][v]
                t=p/('controles' if item['controle'] else 'celulas')/chave(item)/'tentativa_001'
                t.mkdir(parents=True,exist_ok=False)
                vinc={'execucao':f['id'],'bloco':b,'variante':v,'controle':item['controle'],'seed':seed,
                    'familia':'mamba','identidade_consumo':xs[b][v].especificacao.identidade,'configuracao':cfg}
                salvar_json(t/'inicio.json',{'utc':agora(),'vinculo':vinc})
                salvar_json(p/'progresso.json',{'status':'executando','utc':agora(),'concluidos':prontas,
                    'principais_concluidos':sum(not i['controle'] for i in prontas),'controles_concluidos':sum(i['controle'] for i in prontas),'atual':item})
                salvar_json(REG/'estado.json',{'situacao':'executando','execucao':ler_json(REG/'execucao.json'),
                    'progresso':(p/'progresso.json').relative_to(RAIZ).as_posix(),'treinamento_mercado_iniciado':True,'atual':item,'utc':agora()})
                try:
                    with (t/'treinamento.log').open('w',encoding='utf-8',buffering=1) as log:
                        with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                            rede,aj=ajustar(xs[b][v],'mamba',seed,cfg['treino'],RAIZ/cfg['configuracao_modelos'],t,vinc)
                            assert aj['parametros']==20257
                            avaliar(xs[b][v],xs[b][v]._conjunto.partes,'mamba',cfg,t,vinc,rede,aj);del rede
                    selar(t)
                except BaseException:
                    salvar_json(t/'falha.json',{'utc':agora(),'erro':traceback.format_exc()});raise
                if item['controle']:
                    r=reproducao(caminhos[chave(item)],t,cfg['reproducao'])
                    salvar_json(p/f'controle_{v}.json',r)
                else:caminhos[chave(item)]=t
                prontas.append(item)
            conferir_execucao()
            salvar_json(p/'progresso.json',{'status':'concluido','utc':agora(),'concluidos':prontas,
                'principais_concluidos':64,'controles_concluidos':2})
        except BaseException:
            salvar_json(p/'progresso.json',{'status':'interrompido','concluidos':prontas,'utc':agora(),'erro':traceback.format_exc()});raise


def fila():
    with exclusividade(REG):
        try:
            plano=ler_json(REG/'plano.json');c=configuracao();a=ler_json(REG/'autorizacao_plano.json')
            assert a['plano']==plano['id'] and a['plano_sha256']==sha256(REG/'plano.json')
            assert a['reais_novos_total']==66 and a['seeds']==c['seeds'] and a['mensagem_usuario']
            assert plano['id']==identidade(plano['contrato'])[:20] and plano['contrato']['configuracao']==c
            conferir_mapa(plano['contrato']['fontes']);esperar(c)
            salvar_json(REG/'estado.json',{'situacao':'qualificando_cuda','utc':agora(),'plano':plano['id'],'treinamento_mercado_iniciado':False})
            q=qualificar(plano);congelar(plano,q);executar()
            from .publicacao import publicar
            publicar()
        except BaseException:
            erro=traceback.format_exc();salvar_json(REG/'incidentes'/f'{uuid4().hex}.json',{'utc':agora(),'erro':erro})
            salvar_json(REG/'estado.json',{'situacao':'interrompido','utc':agora(),'erro':erro,
                'instrucao':'Investigar. Não repetir fila, qualificação ou treinos automaticamente.'})
            raise
