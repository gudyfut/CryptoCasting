"""Ciclo posterior fechado: quatro moedas, previsões herdadas e ARIMA diário."""
import argparse
from copy import deepcopy
from datetime import datetime,timezone
import hashlib
import io
import json
import math
import os
from pathlib import Path
import platform
import sys
import traceback
import zipfile
import numpy as np
import pandas as pd
from infraestrutura.caminhos import RAIZ
from simulacao_operacoes.continuidade_diaria import simular,conferir
from .arima_diario import ajustar

REG=RAIZ/'registros/continuidade_moedas'


def ler(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def salvar(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def utc():return datetime.now(timezone.utc).isoformat()


def preparar():
    assert not (REG/'execucao.json').exists()
    cfg=ler(RAIZ/'configuracoes/continuidade_moedas_001.json');fg=ler(RAIZ/'registros/generalizacao_moedas/execucao.json')
    assert sha(RAIZ/fg['pasta']/'congelamento.json')==fg['congelamento_sha256'];g=ler(RAIZ/fg['pasta']/'congelamento.json')
    ptr=ler(RAIZ/'registros/padronizacao_diaria/execucao.json');fb=ler(RAIZ/ptr['pasta']/'congelamento.json')
    assert sha(RAIZ/ptr['pasta']/'congelamento.json')==ptr['congelamento_sha256']
    fechamento=ler(REG.parent/'generalizacao_moedas/fechamento.json');assert sha(RAIZ/fechamento['arquivo'])==fechamento['sha256']
    fech=ler(RAIZ/fechamento['arquivo']);fontes={};adicionar=lambda p:fontes.update({p.relative_to(RAIZ).as_posix():sha(p)})
    for p in [RAIZ/fg['pasta']/'congelamento.json',RAIZ/ptr['pasta']/'congelamento.json',RAIZ/fechamento['arquivo']]:adicionar(p)
    moedas={}
    for moeda in cfg['moedas']:
        nome=moeda.removesuffix('USDT');prova=fech['moedas'][nome];base=RAIZ/prova['pasta']
        assert sha(base/'fechamento.json')==prova['fechamento_sha256'];fc=ler(base/'fechamento.json');adicionar(base/'fechamento.json')
        conf=fb['configuracao'] if moeda=='BTCUSDT' else g['moedas'][moeda]['configuracao']
        mercado=fb['mercado_minuto'] if moeda=='BTCUSDT' else g['moedas'][moeda]['mercado']
        diario=fb['diario'] if moeda=='BTCUSDT' else mercado
        for q in {mercado['pasta']:mercado,diario['pasta']:diario}.values():
            p=RAIZ/q['pasta'];assert sha(p/'manifesto.json')==q['manifesto_sha256'];man=ler(p/'manifesto.json');adicionar(p/'manifesto.json')
            usados=['diario.parquet'] if p==RAIZ/diario['pasta'] else []
            if p==RAIZ/mercado['pasta']:usados+=['klines.parquet','markPriceKlines.parquet','funding.parquet']
            if (p/'marca_envelopes.parquet').exists():usados.append('marca_envelopes.parquet')
            for nomearq in set(usados):assert sha(p/nomearq)==man['arquivos'][nomearq];adicionar(p/nomearq)
        for fase in cfg['fases']:
            for seed in cfg['seeds']:
                rel=f'publicacao/previsoes/{fase}_{seed}.npz';assert sha(base/rel)==fc['arquivos'][rel];adicionar(base/rel)
        moedas[moeda]={'base':base.relative_to(RAIZ).as_posix(),'configuracao':conf,'mercado':mercado,'diario':diario}
    custos=ler(RAIZ/'registros/custos_vigentes/vigente.json');p=RAIZ/custos['pasta'];assert sha(p/'publicacao_manifesto.json')==custos['manifesto_sha256']
    mf=ler(p/'publicacao_manifesto.json');assert sha(p/'publicacao/diarias.json')==mf['arquivos']['publicacao/diarias.json']
    for q in [p/'publicacao_manifesto.json',p/'publicacao/diarias.json',RAIZ/'registros/custos_vigentes/vigente.json']:adicionar(q)
    anterior=ler(RAIZ/'registros/continuidade_diaria/execucao.json');ap=RAIZ/anterior['pasta'];assert sha(ap/'manifesto.json')==anterior['manifesto_sha256'];am=ler(ap/'manifesto.json')
    for rel in ['resultados.json','carteiras.zip']:
        assert sha(ap/rel)==am['arquivos'][rel];adicionar(ap/rel)
    adicionar(ap/'manifesto.json')
    sources=list((RAIZ/'codigo/simulacao_operacoes/continuidade_diaria').glob('*.py'))+list((RAIZ/'codigo/analises/etapas/continuidade_moedas').glob('*.py'))
    sources += [RAIZ/n for n in ['codigo/modelos/arima.py','codigo/modelos/contratos.py','codigo/treinamento/selecao.py',
        'codigo/simulacao_operacoes/diaria_24h.py','codigo/simulacao_operacoes/revisada/conta.py','codigo/experimentos/generalizacao_moedas/avaliacao.py',
        'codigo/simulacao_operacoes/envelopes_marcacao.py','codigo/infraestrutura/caminhos.py',
        'testes/simulacao_operacoes/test_continuidade_diaria.py','testes/simulacao_operacoes/test_arima_diario_continuidade.py',
        'configuracoes/continuidade_moedas_001.json','docs/protocolo_continuidade_moedas.md']]
    for p in sources:adicionar(p)
    import statsmodels,scipy
    c={'utc':utc(),'configuracao':cfg,'moedas':moedas,'custos':custos,'btc_legado':anterior,'fontes_entradas':fontes,
        'ambiente':{'host':platform.node(),'python':sys.version,'executavel':sys.executable,'numpy':np.__version__,'pandas':pd.__version__,'statsmodels':statsmodels.__version__,'scipy':scipy.__version__},
        'autorizacao':'Pesquisador solicitou registrar marco e ampliar continuidade para todos os casos completos da receita diária escolhida, com Naive, ARIMA e comprar/manter; sem retreinar redes.'}
    ident=hashlib.sha256(json.dumps(c,sort_keys=True).encode()).hexdigest()[:20];c['id']=ident;p=RAIZ/'dados/reavaliacoes'/f'continuidade_{ident}';p.mkdir(exist_ok=False)
    salvar(p/'congelamento.json',c);salvar(p/'protocolo.json',cfg)
    snapshot={}
    for nome,h in fontes.items():
        if nome.startswith(('codigo/','testes/','configuracoes/','docs/')):
            dest=p/'fontes'/nome;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((RAIZ/nome).read_bytes());assert sha(dest)==h;snapshot[nome]=h
    salvar(p/'fontes_manifesto.json',snapshot)
    ponteiro={'id':ident,'pasta':p.relative_to(RAIZ).as_posix(),'congelamento_sha256':sha(p/'congelamento.json')};salvar(REG/'execucao.json',ponteiro)
    salvar(REG/'estado.json',{'utc':utc(),'situacao':'preparado','execucao':ponteiro,'carteiras_previstas':408,'novos_treinamentos_neurais':0,'arima_candidatos':36,'arima_controles':4})
    print(json.dumps(ponteiro),flush=True)


def verificar(p,c):
    for nome,h in c['fontes_entradas'].items():assert sha(RAIZ/nome)==h,nome
    for nome,h in ler(p/'fontes_manifesto.json').items():assert sha(p/'fontes'/nome)==h,nome


def intervalo(a,b,bloco):
    rng=np.random.default_rng(11112026);n=a.shape[1];v=[]
    for _ in range(2000):
        ss=rng.integers(0,len(a),len(a));ix=(rng.integers(0,n-bloco+1,int(np.ceil(n/bloco)))[:,None]+np.arange(bloco)).ravel()[:n]
        v.append(float((a[ss][:,ix]-b[ss][:,ix]).mean()))
    return {'media_delta_log_diario':float((a-b).mean()),'ic95':np.quantile(v,[.025,.975]).tolist(),'bloco':bloco,'replicas':2000}


def executar():
    ptr=ler(REG/'execucao.json');p=RAIZ/ptr['pasta'];assert sha(p/'congelamento.json')==ptr['congelamento_sha256'];c=ler(p/'congelamento.json');cfg=c['configuracao']
    assert not (p/'resultados.json').exists() and not (p/'incidente.json').exists();verificar(p,c)
    fd=os.open(p/'execucao.lock',os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(fd)
    salvar(p/'processo.json',{'utc':utc(),'host':platform.node(),'pid':os.getpid(),'python':sys.executable})
    try:
        from experimentos.generalizacao_moedas.avaliacao import carregar_mercado
        from simulacao_operacoes.diaria_24h import simular as original
        from simulacao_operacoes.diaria_24h import conferir as conferir_original
        vigente=ler(RAIZ/c['custos']['pasta']/'publicacao/diarias.json');legado=ler(RAIZ/c['btc_legado']['pasta']/'resultados.json')
        resultados=[];auditorias=[];reproducoes=[];legados=[];curvas={};medias={};contrastes={};total=0;numensaios=0
        with zipfile.ZipFile(p/'carteiras.zip','x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for moeda,info in c['moedas'].items():
                conf=info['configuracao'];base=RAIZ/info['base'];diario=pd.read_parquet(RAIZ/info['diario']['pasta']/'diario.parquet')
                dados={fase:dict(np.load(base/'publicacao/previsoes'/f'{fase}_{cfg["seeds"][0]}.npz',allow_pickle=False)) for fase in cfg['fases']}
                salvar(REG/'estado.json',{'utc':utc(),'situacao':'arima','execucao':ptr,'moeda':moeda,'carteiras_concluidas':total,'carteiras_previstas':408})
                print('ARIMA',moeda,'iniciando9candidatos+controle',flush=True)
                arima=ajustar(diario,conf,dados,c['id']+'_'+moeda,p/('arima_'+moeda))
                print('ARIMA',moeda,'controle aprovado',flush=True)
                m=carregar_mercado(info['mercado']);assert np.isfinite(m['negocio']).all() and np.isfinite(m['marca'][:,1:3]).all()
                for fase in cfg['fases']:
                    ds=[dict(np.load(base/'publicacao/previsoes'/f'{fase}_{s}.npz',allow_pickle=False)) for s in cfg['seeds']]
                    t=ds[0]['origens_ms'];u=ds[0]['ultimo_close']
                    for q in ds[1:]:
                        np.testing.assert_array_equal(t,q['origens_ms']);np.testing.assert_array_equal(u,q['ultimo_close']);np.testing.assert_array_equal(ds[0]['y'],q['y'])
                    unidades={str(s):(q['previsoes'],None) for s,q in zip(cfg['seeds'],ds)}
                    unidades.update(ensemble=(np.mean([q['previsoes'] for q in ds],axis=0),None),naive=(u,None),arima=(arima[fase],None),sempre_comprado=(u,1),sempre_vendido=(u,-1))
                    for nome,(prev,forcar) in unidades.items():
                        for mult in [1,2,3]:
                            regras=deepcopy(conf['operacoes']);regras['slippage_por_lado']=.0001*mult
                            ref,cv=original(t,prev,u,m,regras,{'slippage_multiplicador':1,'lado':0},forcar);conferir_original(ref,cv,regras)
                            if nome!='arima':
                                esperado=next(q['metricas'] for q in vigente[info['base']]['carteiras'] if q['fase']==fase and q['unidade']==nome and q['cenario']=={1:'base',2:'slippage2',3:'slippage3'}[mult])
                                for k,v in esperado.items():
                                    if isinstance(v,(int,float)):np.testing.assert_allclose(v,ref['metricas'][k],atol=1e-7,rtol=1e-10,err_msg=k)
                            for modo in cfg['modos']:
                                r,curva=simular(t,prev,u,m,regras,modo,forcar)
                                au=conferir(r,curva,m,regras,modo,t,prev,u,forcar)
                                if modo=='diaria':
                                    np.testing.assert_allclose(cv['saldos_diarios'],curva['saldos_diarios'],atol=1e-7,rtol=1e-10)
                                    for k in ['capital_final','drawdown_maximo','comissoes','funding']:np.testing.assert_allclose(ref['metricas'][k],r['metricas'][k],atol=1e-7,rtol=1e-10)
                                    mapa={o['origem_ms']:o for o in ref['operacoes']};agenda=[int(round(mapa[int(ts)]['lado']*mapa[int(ts)]['quantidade']/regras['passo_quantidade'])) if int(ts) in mapa else 0 for ts in t]
                                    assert agenda==[q['alvo_lotes'] for q in r['dias']]
                                    reproducoes.append({'moeda':moeda,'fase':fase,'unidade':nome,'custo':mult,'quantidades_exatas':True,'residuo_saldos':float(np.max(np.abs(cv['saldos_diarios']-curva['saldos_diarios'])))})
                                if moeda=='BTCUSDT' and nome!='arima' and modo=='liquida':
                                    le,lc=simular(t,prev,u,m,regras,modo,forcar,filtrar_ordens=False)
                                    q=next(v for v in legado['resultados'] if v['fase']==fase and v['unidade']==nome and v['custo']==mult and v['modo']==modo)
                                    for k,v in q['metricas'].items():
                                        if isinstance(v,(int,float)):np.testing.assert_allclose(v,le['metricas'][k],atol=1e-7,rtol=1e-10,err_msg=k)
                                    legados.append({'fase':fase,'unidade':nome,'custo':mult,'reproducao_legada':True,'delta_retorno_filtro':r['metricas']['retorno_liquido']-le['metricas']['retorno_liquido']})
                                ident=f'{moeda}/{fase}/{nome}/custo_{mult}/{modo}'
                                r['regras']=regras;z.writestr(ident+'/resultado.json',json.dumps(r,ensure_ascii=False,allow_nan=False));b=io.BytesIO();np.savez_compressed(b,origens_ms=t,**curva);z.writestr(ident+'/curva.npz',b.getvalue())
                                resultados.append({'moeda':moeda,'fase':fase,'unidade':nome,'custo':mult,'modo':modo,'membro':ident,'metricas':r['metricas']});auditorias.append(dict(identidade=ident,**au));curvas[(moeda,fase,nome,mult,modo)]=curva['saldos_diarios']
                                total+=1
                            print('CARTEIRAS',moeda,fase,nome,mult,total,'/408',flush=True)
                            salvar(REG/'estado.json',{'utc':utc(),'situacao':'executando','execucao':ptr,'moeda':moeda,'carteiras_concluidas':total,'carteiras_previstas':408})
                    for mult in [1,2,3]:
                        regras=deepcopy(conf['operacoes']);regras['slippage_por_lado']=.0001*mult
                        a=int(np.searchsorted(m['tempo'],t[0]+regras['latencia_minutos']*60000));pe=(math.ceil(float(m['negocio'][a,0])*(1+regras['slippage_por_lado'])/regras['tick_preco']))*regras['tick_preco']
                        q0=math.floor(regras['capital_inicial']*regras['fracao_nocional']/pe/regras['passo_quantidade']);agenda=np.full(len(t),q0,dtype=np.int64)
                        r,curva=simular(t,u,u,m,regras,'agenda',1,agenda);au=conferir(r,curva,m,regras,'agenda',t,u,u,1,agenda)
                        assert r['metricas']['ordens']==2 and all(q['alvo_lotes']==q0 for q in r['dias'])
                        ident=f'{moeda}/{fase}/comprar_manter/custo_{mult}/passivo';r['regras']=regras
                        z.writestr(ident+'/resultado.json',json.dumps(r,ensure_ascii=False,allow_nan=False));b=io.BytesIO();np.savez_compressed(b,origens_ms=t,**curva);z.writestr(ident+'/curva.npz',b.getvalue())
                        resultados.append({'moeda':moeda,'fase':fase,'unidade':'comprar_manter','custo':mult,'modo':'passivo','membro':ident,'metricas':r['metricas']});auditorias.append(dict(identidade=ident,**au));curvas[(moeda,fase,'comprar_manter',mult,'passivo')]=curva['saldos_diarios'];total+=1
                # Libera mercado grande antes da moeda seguinte.
                del m
        assert total==408
        for moeda in cfg['moedas']:
            medias[moeda]={};contrastes[moeda]={}
            for fase in cfg['fases']:
                medias[moeda][fase]={};contrastes[moeda][fase]={}
                for mult in [1,2,3]:
                    medias[moeda][fase][str(mult)]={};contrastes[moeda][fase][str(mult)]={}
                    for modo in cfg['modos']:
                        rr=[q['metricas'] for q in resultados if q['moeda']==moeda and q['fase']==fase and q['custo']==mult and q['modo']==modo and q['unidade'] in [str(s) for s in cfg['seeds']]]
                        medias[moeda][fase][str(mult)][modo]={k:float(np.mean([v[k] for v in rr])) for k in rr[0] if all(isinstance(v[k],(int,float)) for v in rr)}
                    la=np.array([np.diff(np.log(curvas[(moeda,fase,str(s),mult,'liquida')])) for s in cfg['seeds']]);lb=np.array([np.diff(np.log(curvas[(moeda,fase,str(s),mult,'diaria')])) for s in cfg['seeds']])
                    contrastes[moeda][fase][str(mult)]['liquida_menos_diaria']={str(b):intervalo(la,lb,b) for b in [7,14,28]}
                    for ref,modo in [('naive','liquida'),('arima','liquida'),('comprar_manter','passivo')]:
                        lr=np.broadcast_to(np.diff(np.log(curvas[(moeda,fase,ref,mult,modo)])),la.shape)
                        contrastes[moeda][fase][str(mult)]['mamba_menos_'+ref]={str(b):intervalo(la,lr,b) for b in [7,14,28]}
        verificar(p,c)
        salvar(p/'resultados.json',{'id':c['id'],'utc':utc(),'situacao':'concluido_conferido','novos_treinamentos_neurais':0,'ajustes_arima_candidatos':36,'controles_arima':4,
            'carteiras':total,'medias_tres_seeds':medias,'contrastes_pareados':contrastes,'resultados':resultados,'limites':'2024 seleção;2025 retrospectivo;IC exploratório condicional;sem ranking entre moedas emUSDT;BH é futuro passivo com funding;Naive=caixa.'})
        salvar(p/'conferencia.json',{'utc':utc(),'id':c['id'],'reproducoes_diarias':reproducoes,'btc_legado_reproduzido':legados,'auditorias':auditorias,
            'fontes_antes_depois_preservadas':True,'ordens_conferidas':sum(x['ordens'] for x in auditorias),'fundings_conferidos':sum(x['fundings'] for x in auditorias),
            'residuo_maximo_usdt':max(x['residuo_usdt'] for x in auditorias),'zip_integral':zipfile.ZipFile(p/'carteiras.zip').testzip()})
        salvar(p/'manifesto.json',{'id':c['id'],'utc':utc(),'arquivos':{q.relative_to(p).as_posix():sha(q) for q in p.rglob('*') if q.is_file() and q.name not in ['manifesto.json','execucao.lock','processo.json']}})
        salvar(REG/'estado.json',{'utc':utc(),'situacao':'concluido_conferido','execucao':ptr,'carteiras_concluidas':total,'carteiras_previstas':408,'novos_treinamentos_neurais':0})
        print('CONCLUIDO',c['id'],flush=True)
    except BaseException:
        salvar(p/'incidente.json',{'utc':utc(),'erro':traceback.format_exc()});salvar(REG/'estado.json',{'utc':utc(),'situacao':'interrompido_preservado','execucao':ptr});raise
    finally:(p/'execucao.lock').unlink()


def main():
    a=argparse.ArgumentParser();a.add_argument('acao',choices=['preparar','executar']);x=a.parse_args();preparar() if x.acao=='preparar' else executar()
