"""Coleta independente de candles diários oficiais; não importa treino/modelos."""
import io
import zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256, identidade, conferir_arquivos
from .pipeline import baixar, BASE

REG = RAIZ/'registros/cryptomamba_diario/dados'
COLUNAS = ['open_time','open','high','low','close','volume','close_time','quote_volume','count','taker_volume','taker_quote','ignore']


def validar(q):
    esperado = np.arange(1577836800000,1767225600000,86400000,dtype=np.int64)
    np.testing.assert_array_equal(q.open_time,esperado)
    np.testing.assert_array_equal(q.close_time,esperado+86399999)
    x=q[['open','high','low','close','volume']].to_numpy(float)
    if not np.isfinite(x).all() or (x[:,:4]<=0).any() or (x[:,4]<0).any():
        raise ValueError('OHLCV diário inválido.')
    if (q.high<q[['open','low','close']].max(axis=1)).any() or (q.low>q[['open','high','close']].min(axis=1)).any():
        raise ValueError('Extremos inconsistentes.')


def coletar():
    REG.mkdir(parents=True,exist_ok=True)
    if (REG/'execucao.json').exists():
        return carregar()[0]
    p=RAIZ/'dados/mercado/cryptomamba_diario'/agora().replace(':','').replace('+','_')
    p.mkdir(parents=True,exist_ok=False);partes=[];fontes=[]
    try:
        for mes in pd.date_range('2020-01-01','2025-12-01',freq='MS',tz='UTC'):
            nome=f'BTCUSDT-1d-{mes:%Y-%m}.zip'
            url=BASE+'klines/BTCUSDT/1d/'+nome
            checksum=baixar(url+'.CHECKSUM');esperado=checksum.decode().split()[0]
            raw=baixar(url);dest=p/'brutos'/nome;dest.parent.mkdir(exist_ok=True)
            dest.write_bytes(raw);dest.with_suffix('.zip.CHECKSUM').write_bytes(checksum)
            if sha256(dest)!=esperado:raise ValueError('Checksum remoto divergente.')
            z=zipfile.ZipFile(io.BytesIO(raw));assert len(z.namelist())==1
            q=pd.read_csv(io.BytesIO(z.read(z.namelist()[0])),header=None)
            if str(q.iloc[0,0])=='open_time':q=q.iloc[1:].copy()
            q.columns=COLUNAS
            for c in COLUNAS:q[c]=pd.to_numeric(q[c],errors='raise')
            for c in ('open_time','close_time','count'):q[c]=q[c].astype('int64')
            ini=int(mes.timestamp()*1000);fim=int((mes+pd.offsets.MonthBegin()).timestamp()*1000)
            np.testing.assert_array_equal(q.open_time,np.arange(ini,fim,86400000))
            partes.append(q);fontes.append({'url':url,'sha256':esperado,'arquivo':dest.relative_to(p).as_posix()})
            salvar_json(REG/'estado.json',{'situacao':'coletando','utc':agora(),'arquivos':len(fontes),'total':72,'pasta':p.relative_to(RAIZ).as_posix()})
            print('DIARIO',len(fontes),'/72',flush=True)
        q=pd.concat(partes,ignore_index=True);validar(q);q.to_parquet(p/'diario.parquet',index=False)
        contrato={'origens':fontes,'linhas':len(q),'inicio':'2020-01-01','fim_exclusivo':'2026-01-01','mercado':'BTCUSDT USD-M','fonte_codigo_sha256':sha256(__file__)}
        salvar_json(p/'manifesto.json',{'id':identidade(contrato)[:20],'contrato':contrato,'arquivos':{a.relative_to(p).as_posix():sha256(a) for a in p.rglob('*') if a.is_file()}})
        ptr={'id':identidade(contrato)[:20],'pasta':p.relative_to(RAIZ).as_posix(),'manifesto_sha256':sha256(p/'manifesto.json')}
        salvar_json(REG/'execucao.json',ptr);salvar_json(REG/'estado.json',{'situacao':'concluido_conferido','utc':agora(),'execucao':ptr,'linhas':len(q)})
        return ptr
    except BaseException:
        import traceback
        salvar_json(p/'incidente.json',{'utc':agora(),'erro':traceback.format_exc()});raise


def carregar():
    ptr=ler_json(REG/'execucao.json');p=RAIZ/ptr['pasta']
    assert sha256(p/'manifesto.json')==ptr['manifesto_sha256']
    conferir_arquivos(p,ler_json(p/'manifesto.json')['arquivos'])
    q=pd.read_parquet(p/'diario.parquet');validar(q)
    return ptr,q


if __name__=='__main__':coletar()
