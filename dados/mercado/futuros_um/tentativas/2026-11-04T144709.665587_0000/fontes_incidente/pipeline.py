import io, json, urllib.request, zipfile, time
from pathlib import Path
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, agora, salvar_json, ler_json, sha256, identidade, conferir_arquivos

REG=RAIZ/'registros/mercado_futuros'
BASE='https://data.binance.vision/data/futures/um/monthly/'

def baixar(url):
    # Retentativa apenas de leitura HTTP, sem alterar fonte ou aceitar resposta parcial.
    for n in range(3):
        try:
            with urllib.request.urlopen(url,timeout=60) as r:return r.read()
        except Exception:
            if n==2:raise
            time.sleep(2*(n+1))

def validar_candles(q,inicio,fim,negocios):
    esperado=np.arange(inicio,fim,60000,dtype=np.int64)
    np.testing.assert_array_equal(q.open_time.to_numpy(),esperado)
    np.testing.assert_array_equal(q.close_time.to_numpy(),esperado+59999)
    x=q[['open','high','low','close']].to_numpy(float)
    assert np.isfinite(x).all() and (x>0).all()
    assert (q.low<=q[['open','close']].min(axis=1)).all() and (q.high>=q[['open','close']].max(axis=1)).all()
    assert (q.high>=q.low).all()
    if negocios:assert (q.volume>=0).all() and (q['count']>=0).all()

def coletar():
    REG.mkdir(parents=True,exist_ok=True)
    if (REG/'execucao.json').exists():raise RuntimeError('Coleta publicada: conferir, nao sobrescrever.')
    d=RAIZ/'dados/mercado/futuros_um/tentativas'/agora().replace(':','').replace('+','_');d.mkdir(parents=True)
    origens=[];dados={k:[] for k in ['klines','markPriceKlines','fundingRate']}
    try:
        for mes in pd.date_range('2024-01-01','2025-12-01',freq='MS',tz='UTC'):
            for tipo in dados:
                nome=(f'BTCUSDT-fundingRate-{mes:%Y-%m}.zip' if tipo=='fundingRate' else f'BTCUSDT-1m-{mes:%Y-%m}.zip')
                sub=f'BTCUSDT/{nome}' if tipo=='fundingRate' else f'BTCUSDT/1m/{nome}'
                url=BASE+tipo+'/'+sub;h=baixar(url+'.CHECKSUM');raw=baixar(url)
                path=d/'brutos'/tipo/nome;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);path.with_suffix('.zip.CHECKSUM').write_bytes(h)
                esperado=h.decode().split()[0];assert sha256(path)==esperado,'Checksum remoto divergente.'
                z=zipfile.ZipFile(io.BytesIO(raw));assert len(z.namelist())==1
                q=pd.read_csv(io.BytesIO(z.read(z.namelist()[0])))
                ini=int(mes.timestamp()*1000);fim=int((mes+pd.offsets.MonthBegin()).timestamp()*1000)
                if tipo!='fundingRate':validar_candles(q,ini,fim,tipo=='klines')
                else:
                    assert q.calc_time.is_unique and q.calc_time.is_monotonic_increasing
                    assert ((q.calc_time>=ini)&(q.calc_time<fim)).all()
                    assert np.isfinite(q.last_funding_rate).all() and (q.funding_interval_hours>0).all()
                dados[tipo].append(q);origens.append({'url':url,'checksum':esperado,'arquivo':path.relative_to(d).as_posix(),'linhas':len(q)})
                salvar_json(REG/'estado.json',{'utc':agora(),'situacao':'coletando','arquivos':len(origens),'total_arquivos':72,'pasta':d.relative_to(RAIZ).as_posix()})
                print('COLETA',len(origens),'/72',tipo,f'{mes:%Y-%m}',flush=True)
        # API fornece mark price efetivo do funding; arquivo mensal confere taxas/cobertura.
        ini=1704067200000;fim=1767225600000;eventos=[];paginas=[]
        while ini<fim:
            url=f'https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&startTime={ini}&endTime={fim-1}&limit=1000'
            raw=baixar(url);q=json.loads(raw);assert isinstance(q,list)
            arq=d/'brutos'/f'funding_api_{len(paginas):03}.json';arq.write_bytes(raw);paginas.append({'url':url,'arquivo':arq.relative_to(d).as_posix(),'sha256':sha256(arq)})
            if not q:break
            assert all(x['symbol']=='BTCUSDT' and ini<=x['fundingTime']<fim for x in q)
            eventos.extend(q);ini=int(q[-1]['fundingTime'])+1
        api=pd.DataFrame(eventos);api['fundingTime']=api.fundingTime.astype('int64');api['fundingRate']=api.fundingRate.astype(float);api['markPrice']=api.markPrice.astype(float)
        arc=pd.concat(dados['fundingRate'],ignore_index=True)
        assert len(api)==len(arc) and api.fundingTime.is_unique and api.fundingTime.is_monotonic_increasing
        # Settlements podem ter milissegundos adicionais. Associacao por minuto, sem inventar taxa.
        np.testing.assert_array_equal(api.fundingTime.to_numpy()//60000,arc.calc_time.to_numpy()//60000)
        np.testing.assert_allclose(api.fundingRate,arc.last_funding_rate,rtol=0,atol=1e-12)
        assert np.isfinite(api.markPrice).all() and (api.markPrice>0).all()
        # Cobertura esperada segundo intervalo declarado no arquivo, sem preencher lacunas.
        assert arc.calc_time.iloc[0]==1704067200000
        np.testing.assert_array_equal(np.diff(arc.calc_time),arc.funding_interval_hours.iloc[1:].to_numpy()*3600000)
        assert arc.calc_time.iloc[-1]+arc.funding_interval_hours.iloc[-1]*3600000==fim
        for tipo in ['klines','markPriceKlines']:
            q=pd.concat(dados[tipo],ignore_index=True);validar_candles(q,1704067200000,fim,tipo=='klines')
            q.to_parquet(d/(tipo+'.parquet'),index=False)
        api[['fundingTime','fundingRate','markPrice']].to_parquet(d/'funding.parquet',index=False)
        contrato={'simbolo':'BTCUSDT','mercado':'USD-M perpetuo','inicio':'2024-01-01','fim_exclusivo':'2026-01-01',
                  'origens':origens,'funding_api':paginas,'unidade_temporal':'milissegundos','fontes':{p.relative_to(RAIZ).as_posix():sha256(p) for p in (RAIZ/'mercado_futuros').glob('*.py')}}
        for nome in ['klines.parquet','markPriceKlines.parquet','funding.parquet']:contrato[nome]=sha256(d/nome)
        codigo=identidade(contrato)[:20]
        salvar_json(d/'manifesto.json',{'id':codigo,'utc':agora(),'contrato':contrato,'arquivos':{p.relative_to(d).as_posix():sha256(p) for p in d.rglob('*') if p.is_file()}})
        ptr={'id':codigo,'pasta':d.relative_to(RAIZ).as_posix(),'manifesto_sha256':sha256(d/'manifesto.json')}
        salvar_json(REG/'execucao.json',ptr);salvar_json(REG/'estado.json',{'utc':agora(),'situacao':'concluido_conferido','execucao':ptr,'minutos':1052640,'eventos_funding':len(api)})
        print('MERCADO_CONCLUIDO',ptr,flush=True)
    except BaseException:
        import traceback
        r={'utc':agora(),'situacao':'interrompido','pasta':d.relative_to(RAIZ).as_posix(),'erro':traceback.format_exc()}
        salvar_json(d/'incidente.json',r);salvar_json(REG/'estado.json',r);raise

def carregar(ptr):
    p=RAIZ/ptr['pasta'];assert sha256(p/'manifesto.json')==ptr['manifesto_sha256'];m=ler_json(p/'manifesto.json');conferir_arquivos(p,m['arquivos'])
    negocio=pd.read_parquet(p/'klines.parquet');marca=pd.read_parquet(p/'markPriceKlines.parquet');funding=pd.read_parquet(p/'funding.parquet')
    np.testing.assert_array_equal(negocio.open_time,marca.open_time)
    return negocio,marca,funding
