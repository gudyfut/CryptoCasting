"""Complemento causal de um minuto; preserva a coleta publicada de 2024–2025."""
import json
import pandas as pd
from infraestrutura.artefatos import RAIZ,agora,ler_json,salvar_json,sha256,identidade,conferir_arquivos
from .pipeline import baixar,carregar,validar_candles

def preparar():
    registro=RAIZ/'registros/mercado_futuros/contexto.json'
    if registro.exists():raise RuntimeError('Complemento ja publicado.')
    pai=ler_json(RAIZ/'registros/mercado_futuros/execucao.json');inicio=1704067140000
    pasta=RAIZ/'dados/mercado/futuros_um/contexto'/agora().replace(':','').replace('+','_');pasta.mkdir(parents=True)
    fontes={p.relative_to(RAIZ).as_posix():sha256(p) for p in (RAIZ/'mercado_futuros').glob('*.py')}
    origens=[]
    for tipo in ['klines','markPriceKlines']:
        url=f'https://fapi.binance.com/fapi/v1/{tipo}?symbol=BTCUSDT&interval=1m&startTime={inicio}&endTime={inicio+59999}&limit=1'
        raw=baixar(url);valores=json.loads(raw);assert len(valores)==1 and valores[0][0]==inicio
        (pasta/(tipo+'.json')).write_bytes(raw)
        origens.append({'url':url,'arquivo':tipo+'.json','sha256':sha256(pasta/(tipo+'.json'))})
    contrato={'pai':pai,'fontes':fontes,'origens':origens,'motivo':'Preco conhecido antes da primeira origem de 2024; nao muda dados de 2024–2025.'}
    codigo=identidade(contrato)[:20]
    salvar_json(pasta/'manifesto.json',{'id':codigo,'contrato':contrato,'arquivos':{p.name:sha256(p) for p in pasta.iterdir() if p.is_file()}})
    ptr={'id':codigo,'pasta':pasta.relative_to(RAIZ).as_posix(),'manifesto_sha256':sha256(pasta/'manifesto.json')}
    carregar_contexto(ptr);salvar_json(registro,ptr);print(ptr)

def carregar_contexto(ptr):
    p=RAIZ/ptr['pasta'];assert sha256(p/'manifesto.json')==ptr['manifesto_sha256'];m=ler_json(p/'manifesto.json');conferir_arquivos(p,m['arquivos'])
    negocio,marca,funding=carregar(m['contrato']['pai']);saida=[]
    for tipo,q in [('klines',negocio),('markPriceKlines',marca)]:
        extra=pd.DataFrame(ler_json(p/(tipo+'.json')),columns=q.columns).astype(q.dtypes.to_dict())
        completo=pd.concat([extra,q],ignore_index=True);validar_candles(completo,1704067140000,1767225600000,tipo=='klines');saida.append(completo)
    return *saida,funding

if __name__=='__main__':preparar()
