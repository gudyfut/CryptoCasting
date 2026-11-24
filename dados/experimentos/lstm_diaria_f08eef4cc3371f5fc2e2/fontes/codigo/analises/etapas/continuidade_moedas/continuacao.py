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
import shutil
import numpy as np
import pandas as pd
from infraestrutura.caminhos import RAIZ
from simulacao_operacoes.continuidade_diaria.simulador import simular
from simulacao_operacoes.continuidade_diaria.auditoria_grade import conferir

REG=RAIZ/'registros/continuidade_moedas'


def ler(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def salvar(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def utc():return datetime.now(timezone.utc).isoformat()


def preparar():
    anterior=ler(REG/'execucao.json');ap=RAIZ/anterior['pasta']
    assert not (ap/'execucao.lock').exists() and (ap/'incidente.json').exists() and not (ap/'resultados.json').exists()
    assert sha(ap/'congelamento.json')==anterior['congelamento_sha256'];c=ler(ap/'congelamento.json');verificar(ap,c)
    diag=ler(REG/'diagnostico_interrupcao.json');assert sha(ap/'carteiras.zip')==diag['zip_sha256']
    assert diag['carteiras_preservadas']==307 and diag['quantidade_auditor']==-2e-12 and diag['quantidade_simulador']==0.
    c=deepcopy(c);c['utc']=utc();c.pop('id');c['continuidade_tecnica']={'antecessora':anterior,'zip_sha256':sha(ap/'carteiras.zip'),
        'carteiras_herdadas':307,'mudanca':'Somente auditor: quantidade representada na grade inteira, eliminando resíduo fictício de2e-12XRP após fechamento. Mesmo simulador, hipóteses, filtros, dados, parâmetros e previsões; não refazer ARIMA.'}
    for nome in ['codigo/simulacao_operacoes/continuidade_diaria/auditoria_grade.py','codigo/analises/etapas/continuidade_moedas/continuacao.py',
        'testes/simulacao_operacoes/test_auditoria_grade_continuidade.py','registros/continuidade_moedas/diagnostico_interrupcao.json']:
        c['fontes_entradas'][nome]=sha(RAIZ/nome)
    c['pais_artefatos']={q.relative_to(RAIZ).as_posix():sha(q) for q in ap.rglob('*') if q.is_file() and (q.parts[-2].startswith('arima_') or q.name in ['carteiras.zip','incidente.json','congelamento.json','fontes_manifesto.json'])}
    c['id']=hashlib.sha256(json.dumps(c,sort_keys=True).encode()).hexdigest()[:20];p=RAIZ/'dados/reavaliacoes'/f'continuidade_{c["id"]}';p.mkdir(exist_ok=False)
    shutil.copyfile(ap/'carteiras.zip',p/'carteiras.zip');assert sha(p/'carteiras.zip')==diag['zip_sha256']
    for moeda in c['configuracao']['moedas']:shutil.copytree(ap/f'arima_{moeda}',p/f'arima_{moeda}')
    for q in [ap/'fontes']:
        shutil.copytree(q,p/q.name)
    snapshot=ler(ap/'fontes_manifesto.json')
    for nome in c['fontes_entradas']:
        if nome.startswith(('codigo/','testes/','configuracoes/','docs/')):
            dest=p/'fontes'/nome
            if not dest.exists():dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((RAIZ/nome).read_bytes());snapshot[nome]=sha(dest)
    salvar(p/'fontes_manifesto.json',snapshot);salvar(p/'congelamento.json',c);salvar(p/'protocolo.json',c['configuracao'])
    with zipfile.ZipFile(ap/'carteiras.zip') as z:salvar(p/'heranca_membros.json',{n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()})
    salvar(REG/'tentativa_inicial.json',anterior)
    ptr={'id':c['id'],'pasta':p.relative_to(RAIZ).as_posix(),'congelamento_sha256':sha(p/'congelamento.json')};salvar(REG/'execucao.json',ptr)
    salvar(REG/'estado.json',{'utc':utc(),'situacao':'preparado_continuacao','execucao':ptr,'carteiras_herdadas':307,'carteiras_previstas':408,'novos_treinamentos_neurais':0})
    print(json.dumps(ptr),flush=True)


def verificar(p,c):
    for nome,h in c['fontes_entradas'].items():assert sha(RAIZ/nome)==h,nome
    for nome,h in ler(p/'fontes_manifesto.json').items():assert sha(p/'fontes'/nome)==h,nome
    for nome,h in c.get('pais_artefatos',{}).items():assert sha(RAIZ/nome)==h,nome


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
        resultados=[];auditorias=[];reproducoes=[];legados=[];curvas={};medias={};contrastes={};total=0;herdadas=0
        with zipfile.ZipFile(p/'carteiras.zip','a',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            existentes=set(z.namelist())
            for moeda,info in c['moedas'].items():
                conf=info['configuracao'];base=RAIZ/info['base'];diario=pd.read_parquet(RAIZ/info['diario']['pasta']/'diario.parquet')
                dados={fase:dict(np.load(base/'publicacao/previsoes'/f'{fase}_{cfg["seeds"][0]}.npz',allow_pickle=False)) for fase in cfg['fases']}
                salvar(REG/'estado.json',{'utc':utc(),'situacao':'arima','execucao':ptr,'moeda':moeda,'carteiras_concluidas':total,'carteiras_previstas':408})
                arima={fase:np.load(p/f'arima_{moeda}'/f'{fase}.npz',allow_pickle=False)['previsoes'] for fase in cfg['fases']}
                assert ler(p/f'arima_{moeda}'/'controle.json')['parametros_repetidos_exatos']
                print('ARIMA',moeda,'herdado e controle preservado',flush=True)
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
                                ident=f'{moeda}/{fase}/{nome}/custo_{mult}/{modo}';herdar=ident+'/resultado.json' in existentes
                                if herdar:
                                    r=json.loads(z.read(ident+'/resultado.json'));curva=dict(np.load(io.BytesIO(z.read(ident+'/curva.npz')),allow_pickle=False));curva.pop('origens_ms');herdadas+=1
                                else:r,curva=simular(t,prev,u,m,regras,modo,forcar)
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
                                if not herdar:
                                    r['regras']=regras;z.writestr(ident+'/resultado.json',json.dumps(r,ensure_ascii=False,allow_nan=False));b=io.BytesIO();np.savez_compressed(b,origens_ms=t,**curva);z.writestr(ident+'/curva.npz',b.getvalue())
                                resultados.append({'moeda':moeda,'fase':fase,'unidade':nome,'custo':mult,'modo':modo,'membro':ident,'metricas':r['metricas']});auditorias.append(dict(identidade=ident,**au));curvas[(moeda,fase,nome,mult,modo)]=curva['saldos_diarios']
                                total+=1
                            print('CARTEIRAS',moeda,fase,nome,mult,total,'/408',flush=True)
                            salvar(REG/'estado.json',{'utc':utc(),'situacao':'executando','execucao':ptr,'moeda':moeda,'carteiras_concluidas':total,'carteiras_previstas':408})
                    for mult in [1,2,3]:
                        regras=deepcopy(conf['operacoes']);regras['slippage_por_lado']=.0001*mult
                        a=int(np.searchsorted(m['tempo'],t[0]+regras['latencia_minutos']*60000));pe=(math.ceil(float(m['negocio'][a,0])*(1+regras['slippage_por_lado'])/regras['tick_preco']))*regras['tick_preco']
                        q0=math.floor(regras['capital_inicial']*regras['fracao_nocional']/pe/regras['passo_quantidade']);agenda=np.full(len(t),q0,dtype=np.int64)
                        ident=f'{moeda}/{fase}/comprar_manter/custo_{mult}/passivo';herdar=ident+'/resultado.json' in existentes
                        if herdar:
                            r=json.loads(z.read(ident+'/resultado.json'));curva=dict(np.load(io.BytesIO(z.read(ident+'/curva.npz')),allow_pickle=False));curva.pop('origens_ms');herdadas+=1
                        else:r,curva=simular(t,u,u,m,regras,'agenda',1,agenda)
                        au=conferir(r,curva,m,regras,'agenda',t,u,u,1,agenda)
                        assert r['metricas']['ordens']==2 and all(q['alvo_lotes']==q0 for q in r['dias'])
                        if not herdar:
                            r['regras']=regras;z.writestr(ident+'/resultado.json',json.dumps(r,ensure_ascii=False,allow_nan=False));b=io.BytesIO();np.savez_compressed(b,origens_ms=t,**curva);z.writestr(ident+'/curva.npz',b.getvalue())
                        resultados.append({'moeda':moeda,'fase':fase,'unidade':'comprar_manter','custo':mult,'modo':'passivo','membro':ident,'metricas':r['metricas']});auditorias.append(dict(identidade=ident,**au));curvas[(moeda,fase,'comprar_manter',mult,'passivo')]=curva['saldos_diarios'];total+=1
                # Libera mercado grande antes da moeda seguinte.
                del m
        assert total==408 and herdadas==307
        with zipfile.ZipFile(p/'carteiras.zip') as z:
            for nome,h in ler(p/'heranca_membros.json').items():assert hashlib.sha256(z.read(nome)).hexdigest()==h,nome
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
            'carteiras':total,'carteiras_herdadas':herdadas,'carteiras_novas_continuacao':total-herdadas,'medias_tres_seeds':medias,'contrastes_pareados':contrastes,'resultados':resultados,'limites':'2024 seleção;2025 retrospectivo;IC exploratório condicional;sem ranking entre moedas emUSDT;BH é futuro passivo com funding;Naive=caixa.'})
        salvar(p/'conferencia.json',{'utc':utc(),'id':c['id'],'reproducoes_diarias':reproducoes,'btc_legado_reproduzido':legados,'auditorias':auditorias,
            'fontes_antes_depois_preservadas':True,'heranca_307_carteiras_bytes_exatos':True,'auditor_grade_inteira':True,'ordens_conferidas':sum(x['ordens'] for x in auditorias),'fundings_conferidos':sum(x['fundings'] for x in auditorias),
            'residuo_maximo_usdt':max(x['residuo_usdt'] for x in auditorias),'zip_integral':zipfile.ZipFile(p/'carteiras.zip').testzip()})
        salvar(p/'manifesto.json',{'id':c['id'],'utc':utc(),'arquivos':{q.relative_to(p).as_posix():sha(q) for q in p.rglob('*') if q.is_file() and q.name not in ['manifesto.json','execucao.lock','processo.json']}})
        salvar(REG/'estado.json',{'utc':utc(),'situacao':'concluido_conferido','execucao':ptr,'carteiras_concluidas':total,'carteiras_previstas':408,'novos_treinamentos_neurais':0})
        print('CONCLUIDO',c['id'],flush=True)
    except BaseException:
        salvar(p/'incidente.json',{'utc':utc(),'erro':traceback.format_exc()});salvar(REG/'estado.json',{'utc':utc(),'situacao':'interrompido_preservado','execucao':ptr});raise
    finally:(p/'execucao.lock').unlink()


def main():
    a=argparse.ArgumentParser();a.add_argument('acao',choices=['preparar','executar']);x=a.parse_args();preparar() if x.acao=='preparar' else executar()


if __name__=="__main__":main()
