"""Reavalia custos de execuções encerradas sem importar treinamento ou seleção."""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import platform
import sqlite3
import time
import traceback
import zipfile
import zlib
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,sha256,identidade,agora
from .historico import instalar
from . import adaptadores as a

PONTEIRO=RAIZ/'registros/custos_vigentes/execucao.json'


def preparar():
    from .inventario import montar
    r=RAIZ/'registros/custos_vigentes/inventario_preparacao.json'
    inv=ler_json(r) if r.exists() else montar()
    fontes={p.relative_to(RAIZ).as_posix():sha256(p) for pasta in ('codigo/analises/etapas/custos_vigentes','codigo/simulacao_operacoes','codigo/avaliacao') for p in (RAIZ/pasta).rglob('*.py')}
    fontes['arquivo/desenvolvimento_encerrado/fontes.zip']=sha256(RAIZ/'arquivo/desenvolvimento_encerrado/fontes.zip')
    cfg=ler_json(RAIZ/'configuracoes/custos_vigentes_001.json')
    assinatura={'configuracao':cfg,'inventario':inv,'fontes':fontes,'somente_financeiro':True,'selecao_historica_preservada':True}
    codigo=identidade(assinatura)[:20];p=RAIZ/'dados/reavaliacoes'/f'custos_{codigo}'
    if p.exists():raise FileExistsError(p)
    p.mkdir(parents=True);salvar_json(p/'congelamento.json',{'id':codigo,'utc':agora(),**assinatura})
    salvar_json(PONTEIRO,{'id':codigo,'pasta':p.relative_to(RAIZ).as_posix(),'congelamento_sha256':sha256(p/'congelamento.json')})
    salvar_json(p/'progresso.json',{'situacao':'preparado','previstos':len(inv['jobs']),'concluidos':0,'utc':agora()})
    print(p,flush=True)


def limpar(x):
    if isinstance(x,pd.DataFrame):return limpar(x.to_dict('records'))
    if isinstance(x,dict):return {k:limpar(v) for k,v in x.items()}
    if isinstance(x,(list,tuple,np.ndarray)):return [limpar(v) for v in x]
    if isinstance(x,(pd.Timestamp,)):return x.isoformat()
    if isinstance(x,np.generic):return limpar(x.item())
    if isinstance(x,float) and not np.isfinite(x):return None
    return x


def chave(j):
    typ=j['tipo'];cfg=a.contrato(j['pai']);p=RAIZ/j['fonte']
    if typ=='spot_retida':
        r=ler_json(RAIZ/j['resumo']);c=a.localizar(cfg,{'custos','risco_smart','passo_btc','minimo_usdt'})
        if c is None:c=a.contrato('backtest_carteira_8ec8a66648313caa48e3')['configuracao']
        return identidade([typ,j['sha256'],c,r['politica'],r['cenario']])
    if typ in ('spot24','spot24_preliminar'):
        o=ler_json(p);ops=o['ordens'] if isinstance(o,dict) else o
        r=o['estrategia'] if isinstance(o,dict) else a.resumo_spot24(j)
        c=a.localizar(cfg,{'hora_utc','taxa','slippage','taxa_agravada'})
        if c is None:c=ler_json(RAIZ/'configuracoes/mamba_estado8_001.json')['operacao']
        return identidade(['spot24',[(v['origem_utc'],v['previsao'],v['saida_minuto']) for v in ops],c,j['cenario'],r.get('par','BTCUSDT'),r.get('controle',False)])
    # Outras famílias têm contratos e mercados distintos: não deduplicar por métricas.
    return identidade([typ,j['fonte'],j['sha256']])


def executar():
    ptr=ler_json(PONTEIRO);p=RAIZ/ptr['pasta'];f=ler_json(p/'congelamento.json')
    if sha256(p/'congelamento.json')!=ptr['congelamento_sha256']:raise ValueError('Congelamento divergente')
    for arq,h in f['fontes'].items():
        if sha256(RAIZ/arq)!=h:raise ValueError('Fonte alterada: '+arq)
    for arq,h in f['inventario']['fontes_congelamento'].items():
        if sha256(RAIZ/arq)!=h:raise ValueError('Pai alterado: '+arq)
    lock=p/'execucao.lock'
    with lock.open('x',encoding='utf8') as v:v.write(json.dumps({'pid':os.getpid(),'host':platform.node(),'utc':agora()}))
    salvar_json(p/'processo.json',{'pid':os.getpid(),'host':platform.node(),'utc':agora(),'comando':'python -B -m analises.etapas.custos_vigentes.executar executar'})
    instalar();inicio=time.time();db=sqlite3.connect(p/'carteiras.sqlite')
    db.execute('CREATE TABLE IF NOT EXISTS cache (chave TEXT PRIMARY KEY, antigo BLOB, novo BLOB, ledger TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS carteiras (fonte TEXT PRIMARY KEY, sha256 TEXT, chave TEXT, tipo TEXT, pai TEXT, resumo TEXT)')
    feitos={r[0] for r in db.execute('SELECT fonte FROM carteiras')};unicos=db.execute('SELECT COUNT(*) FROM cache').fetchone()[0]
    total=len(f['inventario']['jobs']);n=len(feitos);ultima=0
    def estado(situacao,**campos):salvar_json(p/'progresso.json',{'situacao':situacao,'previstos':total,'concluidos':n,'execucoes_unicas':unicos,'decorridos_segundos':time.time()-inicio,'utc':agora(),**campos})
    try:
        with zipfile.ZipFile(p/'ledgers.zip','a',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as z:
            for j in f['inventario']['jobs']:
                if j['fonte'] in feitos:continue
                if sha256(RAIZ/j['fonte'])!=j['sha256']:raise ValueError('Resultado pai alterado: '+j['fonte'])
                k=chave(j);c=db.execute('SELECT antigo,novo,ledger FROM cache WHERE chave=?',(k,)).fetchone()
                if c:
                    ant=json.loads(zlib.decompress(c[0]));novo=json.loads(zlib.decompress(c[1]));extra_nome=c[2]
                    esperado=ler_json(RAIZ/j['resumo']) if j['tipo']=='spot_retida' else (ler_json(RAIZ/j['fonte'])['estrategia'] if j['tipo']=='spot24_preliminar' else a.resumo_spot24(j))
                    a.conferir_reproducao(esperado,ant)
                    for campo in ('par','modelo','contexto','seed','arquivo'):
                        if campo in esperado:novo[campo]=esperado[campo]
                else:
                    esperado,reproduzido,_=a.executar(j,1.);a.conferir_reproducao(esperado,reproduzido)
                    _,novo,extra=a.executar(j,.2)
                    extra_nome=k+'.json';z.writestr(extra_nome,json.dumps(limpar(extra),ensure_ascii=False,allow_nan=False,separators=(',',':')))
                    db.execute('INSERT INTO cache VALUES (?,?,?,?)',(k,zlib.compress(json.dumps(limpar(esperado)).encode()),zlib.compress(json.dumps(limpar(novo)).encode()),extra_nome));unicos+=1
                db.execute('INSERT INTO carteiras VALUES (?,?,?,?,?,?)',(j['fonte'],j['sha256'],k,j['tipo'],j['pai'],json.dumps(limpar(novo),ensure_ascii=False,allow_nan=False)))
                db.commit();n+=1
                if time.time()-ultima>5:
                    estado('executando',atual=j['fonte']);ultima=time.time();print(f'{n}/{total} unicas={unicos} {j["tipo"]}',flush=True)
        for arq,h in f['inventario']['fontes_congelamento'].items():
            if sha256(RAIZ/arq)!=h:raise ValueError('Pai modificado durante leitura: '+arq)
        estado('recalculado_conferido');salvar_json(p/'conferencia.json',{'utc':agora(),'carteiras':n,'reproducoes_e_recalculos_unicos':unicos,'novos_treinamentos':0,'fontes_historicas_importadas':instalados()})
    except BaseException:
        estado('falha',erro=traceback.format_exc());raise
    finally:
        db.close();lock.unlink()


def instalados():
    import sys
    return {k:v for l in sys.meta_path if hasattr(l,'carregados') for k,v in l.carregados.items()}


if __name__=='__main__':
    cli=argparse.ArgumentParser();cli.add_argument('acao',choices=['preparar','executar']);args=cli.parse_args()
    preparar() if args.acao=='preparar' else executar()
