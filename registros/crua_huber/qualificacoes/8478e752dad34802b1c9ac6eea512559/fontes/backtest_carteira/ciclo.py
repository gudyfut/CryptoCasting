"""Execução identificada só de backtests, com qualificação e preservação próprias."""
import contextlib
import importlib.metadata
import io
import math
import os
import platform
import shutil
import traceback
import unittest
from uuid import uuid4
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,agora,ler_json,salvar_json,sha256,identidade,conferir_arquivos,fontes
from .simulador import simular,COLUNAS
from .auditoria import conferir

REG=RAIZ/'registros/backtest_carteira'
CONFIG='configuracoes/backtest_carteira_001.json'
PROTOCOLO='docs/protocolo_backtest_carteira.md'
SEEDS=[17,42,2026,7,123,31415]


def ambiente():return {'python':platform.python_version(),'host':platform.node(),'sistema':platform.system(),'pacotes':{n:importlib.metadata.version(n) for n in ('numpy','pandas','pyarrow','matplotlib')}}


def configuracao():
    c=ler_json(RAIZ/CONFIG)
    assert c['seeds']==SEEDS and c['seeds_pareadas_lstm']==SEEDS[:3] and c['politicas']==['smart','vanilla','diaria24'] and c['partes']==['validacao','teste']
    esperadas={f'estado16_{s}' for s in SEEDS}|{f'cryptomamba_{s}' for s in SEEDS}|{f'lstm_{s}' for s in SEEDS[:3]}|{'naive','arima'}
    assert set(c['series'])==esperadas and c['simulacoes_planejadas']==369 and c['novos_treinamentos']==c['buscas_parametros']==0
    assert (c['capital'],c['risco_smart'],c['limiar_vanilla'],c['latencia_minutos'],c['passo_btc'],c['minimo_usdt'])==(10000.,.02,.01,1,.00001,5.)
    assert c['custos']=={'ideal':{'taxa':0.,'slippage':0.},'base':{'taxa':.001,'slippage':.0005},'agravado':{'taxa':.002,'slippage':.001}}
    assert c['bootstrap']=={'dias':14,'replicas':2000,'seed':20261030}
    return c


def fontes_atuais():
    fs=fontes('backtest_carteira','tests_backtest_carteira')
    for n in (CONFIG,'run_backtest.py','infraestrutura/artefatos.py',PROTOCOLO):fs[n]=sha256(RAIZ/n)
    orig='registros/cryptomamba/fontes_externas/fef42727861a9c3a32241283ab981ef21a49e291/'
    for n in ('utils/trade.py','scripts/simulate_trade.py','LICENSE','proveniencia.json'):fs[orig+n]=sha256(RAIZ/(orig+n))
    return fs


def entradas(c):
    ins={};guard=ler_json(RAIZ/'registros/cryptomamba/preservacao_antes.json')['arquivos'].copy()
    ptr=ler_json(RAIZ/'registros/cryptomamba/execucao.json');p=RAIZ/ptr['pasta'];conferir_arquivos(p,{'congelamento.json':ptr['congelamento_sha256']})
    assert ler_json(p/'progresso.json')['status']=='concluido' and not ler_json(p/'processo.json')['ativo']
    f=ler_json(p/'congelamento.json');conferir_arquivos(RAIZ,f['contrato']['fontes']);guard.update(f['contrato']['fontes'])
    pp=ler_json(p/'publicacao.json');pub=p/pp['pasta'];assert pub==RAIZ/c['publicacao_origem']
    conferir_arquivos(pub,{'manifesto.json':pp['manifesto_sha256']});man=ler_json(pub/'manifesto.json');conferir_arquivos(pub,man['arquivos'])
    for n,h in man['arquivos'].items():guard[(pub/n).relative_to(RAIZ).as_posix()]=h
    publicado=ler_json(pub/'resultados.json')['por_ajuste'];pred={};mu={}
    for k,t in c['series'].items():
        assert publicado[k]['tentativa_origem']==t
        d=RAIZ/t;fim=ler_json(d/'conclusao.json');assert fim['status']=='concluido';conferir_arquivos(d,fim['arquivos'])
        ins[t+'/conclusao.json']=sha256(d/'conclusao.json')
        for n,h in fim['arquivos'].items():guard[t+'/'+n]=h
        guard[t+'/conclusao.json']=ins[t+'/conclusao.json']
        for b in c['partes']:
            n=t+f'/previsoes_{b}.parquet';ins[n]=sha256(RAIZ/n);q=pd.read_parquet(RAIZ/n)[COLUNAS];pred[k,b]=q
            assert len(q)==(8760 if b=='validacao' else 8736)
        daily=pred[k,'validacao'].loc[pd.DatetimeIndex(pred[k,'validacao'].origem_utc).hour==0];mu[k]=float(daily.previsao.mean())
    for b in c['partes']:
        ref=pred[next(iter(c['series'])),b].drop(columns='previsao').reset_index(drop=True)
        for k in c['series']:pd.testing.assert_frame_equal(ref,pred[k,b].drop(columns='previsao').reset_index(drop=True),check_exact=True)
    mercado=RAIZ/c['mercado_pasta'];qm=ler_json(mercado/'qualidade.json');mm=ler_json(mercado/'manifesto.json')
    selecionadas=[r for r in qm['partes'] if r['par']=='BTCUSDT' and r['periodo']['inicio']>='2023-12' and r['periodo']['inicio']<'2026-01']
    assert len(selecionadas)==25
    for r in selecionadas:ins[c['mercado_pasta']+'/'+r['arquivo']]=mm['arquivos'][r['arquivo']]
    for n in ('manifesto.json','qualidade.json'):ins[c['mercado_pasta']+'/'+n]=sha256(mercado/n)
    ins[c['publicacao_origem']+'/manifesto.json']=sha256(pub/'manifesto.json');ins[c['publicacao_origem']+'/resultados.json']=sha256(pub/'resultados.json')
    for n in ('registros/cryptomamba/execucao.json','registros/cryptomamba/fechamento.json','registros/referencias/mamba16_ohlcv24_001.json'):ins[n]=sha256(RAIZ/n)
    conferir_arquivos(RAIZ,ins);conferir_arquivos(RAIZ,guard)
    return ins,guard,mu,selecionadas


def grade(c):
    g=[]
    for b in c['partes']:
        for custo in c['custos']:
            for pol in c['politicas']:
                for k in c['series']:g.append({'parte':b,'cenario':custo,'politica':pol,'serie':k})
            if b=='teste':
                for k in c['series']:g.append({'parte':b,'cenario':custo,'politica':'smart_constante','serie':k})
            for pol in ('caixa','comprar_manter'):g.append({'parte':b,'cenario':custo,'politica':pol,'serie':'benchmark'})
    assert len(g)==c['simulacoes_planejadas'];return g


def preparar():
    if (REG/'execucao.json').exists():raise FileExistsError('Execução já preparada; não duplicar.')
    c=configuracao();fs=fontes_atuais();q=REG/'qualificacoes'/uuid4().hex;q.mkdir(parents=True)
    for n in fs:
        d=q/'fontes'/n;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(RAIZ/n,d)
    log=io.StringIO()
    suite=unittest.defaultTestLoader.loadTestsFromName('tests_backtest_carteira.test_carteira')
    with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):r=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    (q/'testes.log').write_text(log.getvalue(),encoding='utf-8')
    salvar_json(q/'resultado.json',{'utc':agora(),'aprovado':r.wasSuccessful() and not r.skipped,'testes':r.testsRun,'skips':len(r.skipped),'fontes':fs,'simulacoes_mercado':0,'treinamentos':0})
    if not r.wasSuccessful() or r.skipped:raise ValueError('Qualificação reprovada; preservar.')
    ins,guard,mu,partes=entradas(c)
    assert fontes_atuais()==fs
    contrato={'configuracao':c,'fontes':fs,'insumos':ins,'mercado_partes':partes,'medias_validacao_para_controle':mu,'grade':grade(c),'ambiente':ambiente(),'qualificacao':{'arquivo':(q/'resultado.json').relative_to(RAIZ).as_posix(),'sha256':sha256(q/'resultado.json')}}
    codigo=identidade(contrato)[:20];p=RAIZ/f'dados/experimentos/backtest_carteira_{codigo}';p.mkdir(parents=True)
    for n in fs:
        d=p/'fontes'/n;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(RAIZ/n,d)
    salvar_json(p/'congelamento.json',{'id':codigo,'utc':agora(),'contrato':contrato});salvar_json(p/'progresso.json',{'status':'preparado','concluidas':0,'total':369})
    salvar_json(REG/'preservacao_antes.json',{'utc':agora(),'arquivos':guard});ptr={'id':codigo,'pasta':p.relative_to(RAIZ).as_posix(),'congelamento_sha256':sha256(p/'congelamento.json')};salvar_json(REG/'execucao.json',ptr)
    salvar_json(REG/'estado.json',{'situacao':'preparado_qualificado','execucao':ptr,'progresso':ptr['pasta']+'/progresso.json','simulacoes_planejadas':369,'treinamentos':0});return ptr


def carregar_mercado(p,contrato):
    cfg=contrato['configuracao'];ts=[]
    for r in sorted(contrato['mercado_partes'],key=lambda d:d['periodo']['inicio']):ts.append(pd.read_parquet(RAIZ/cfg['mercado_pasta']/r['arquivo']))
    m=pd.concat(ts,ignore_index=True);t=pd.DatetimeIndex(m.inicio_utc)
    assert t.tz is not None and (t[1:]-t[:-1]==pd.Timedelta(minutes=1)).all()
    x=m[['open','high','low','close','volume','negocios']].to_numpy(float);x[~m.completo.to_numpy()]=np.nan
    return x,int(t[0].timestamp()//60)


def executar(autorizacao):
    import msvcrt
    ptr=ler_json(REG/'execucao.json');p=RAIZ/ptr['pasta'];conferir_arquivos(p,{'congelamento.json':ptr['congelamento_sha256']});f=ler_json(p/'congelamento.json');ct=f['contrato'];c=ct['configuracao']
    assert identidade(ct)[:20]==ptr['id'] and c==configuracao() and ct['ambiente']==ambiente();conferir_arquivos(RAIZ,ct['fontes']);conferir_arquivos(p/'fontes',ct['fontes']);conferir_arquivos(RAIZ,ct['insumos'])
    a=ler_json(autorizacao)
    assert a['execucao']==ptr['id'] and a['simulacoes_total']==369 and a['novos_treinamentos']==0 and a['mensagem_usuario']
    if ler_json(p/'progresso.json')['status']!='preparado':raise ValueError('Não repetir executor após resultados/interrupção.')
    with (p/'execucao.lock').open('a+b') as lock:
        if not lock.tell():lock.write(b'0');lock.flush()
        lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        proc={'ativo':True,'pid':os.getpid(),'host':platform.node(),'inicio_utc':agora()};salvar_json(p/'processo.json',proc);salvar_json(p/'autorizacao.json',a)
        n=0
        try:
            minutos,primeiro=carregar_mercado(p,ct);pred={(k,b):pd.read_parquet(RAIZ/t/f'previsoes_{b}.parquet')[COLUNAS] for k,t in c['series'].items() for b in c['partes']};res={}
            for job in ct['grade']:
                b,custo,pol,k=[job[z] for z in ('parte','cenario','politica','serie')];q=pred[next(iter(c['series'])) if k=='benchmark' else k,b].copy()
                if pol=='smart_constante':q['previsao']=ct['medias_validacao_para_controle'][k]
                politica='smart' if pol=='smart_constante' else pol
                r,o,cur,d,si=simular(q,minutos,primeiro,c,politica,custo);ver=conferir(q,minutos,primeiro,c,politica,custo,r,o,d)
                assert r['dias_decisao']==(365 if b=='validacao' else 364)
                chave=f'{b}/{custo}/{pol}/{k}';dest=p/'resultados'/chave;dest.mkdir(parents=True)
                salvar_json(dest/'resumo.json',r);salvar_json(dest/'ordens.json',o);salvar_json(dest/'sinais.json',si);salvar_json(dest/'verificacao.json',ver);cur.to_parquet(dest/'curva.parquet',index=False);d.to_parquet(dest/'diarios.parquet',index=False)
                salvar_json(dest/'manifesto.json',{'arquivos':{q.name:sha256(q) for q in dest.iterdir() if q.is_file()}});res[chave]=r;n+=1
                salvar_json(p/'progresso.json',{'status':'simulando','concluidas':n,'total':369,'atual':job,'utc':agora()})
                if n%15==0:print(f'{n}/369 simulações auditadas',flush=True)
            conferir_arquivos(RAIZ,ct['fontes']);conferir_arquivos(RAIZ,ct['insumos']);guard=ler_json(REG/'preservacao_antes.json')['arquivos'];conferir_arquivos(RAIZ,guard)
            from .relatorio import publicar
            rel=publicar(p,f,res)
            salvar_json(p/'resultados/manifesto.json',{'arquivos':{q.relative_to(p/'resultados').as_posix():sha256(q) for q in (p/'resultados').rglob('*') if q.is_file()}})
            salvar_json(p/'progresso.json',{'status':'concluido','concluidas':n,'total':369,'utc':agora()})
            fim={'situacao':'concluido_conferido','utc':agora(),'execucao':ptr,'simulacoes':n,'treinamentos':0,'preservados':len(guard),'resultado':(p/'resultados/comparacao.json').relative_to(RAIZ).as_posix(),'resultado_sha256':sha256(p/'resultados/comparacao.json'),'relatorio':rel}
            salvar_json(REG/'fechamento.json',fim);salvar_json(REG/'estado.json',fim);print(fim,flush=True)
        except BaseException:
            salvar_json(p/'progresso.json',{'status':'interrompido','concluidas':n,'total':369,'utc':agora(),'erro':traceback.format_exc()});salvar_json(p/'incidentes'/f'{uuid4().hex}.json',{'utc':agora(),'erro':traceback.format_exc()});raise
        finally:
            salvar_json(p/'processo.json',dict(proc,ativo=False,fim_utc=agora()));lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
