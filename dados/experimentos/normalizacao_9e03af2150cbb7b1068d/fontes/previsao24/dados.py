"""Transformação causal; o alvo terminal só exige preço nas duas pontas."""
from pathlib import Path
import numpy as np
import pandas as pd
from .arquivos import RAIZ, agora, identidade, ler_json, salvar_json, sha256, verificar_arquivos
from .coleta import ler_mes
from .configuracao import PARES, FOLDS

def construir_horas(minutos, primeiro_minuto):
    if primeiro_minuto % 60 or len(minutos) % 60 or minutos.ndim != 2 or minutos.shape[1] != 6:
        raise ValueError('Grade de minutos desalinhada.')
    blocos = minutos.reshape(-1,60,6)
    completas = np.isfinite(blocos).all(axis=(1,2))
    o = blocos[:,0,0].copy()
    h = np.max(blocos[:,:,1],axis=1)
    l = np.min(blocos[:,:,2],axis=1)
    c = blocos[:,-1,3].copy()
    v = np.sum(blocos[:,:,4],axis=1)
    for a in (o,h,l,c,v):
        a[~completas] = np.nan
    q = pd.DataFrame({'origem_utc':pd.to_datetime(primeiro_minuto+(np.arange(len(c))+1)*60,unit='m',utc=True),
                      'indice_hora':np.arange(len(c)), 'open':o,'high':h,'low':l,'close':c,'volume':v})
    q['retorno'] = np.log(q['close']/q['close'].shift(1))
    q['preco_destino'] = q['close'].shift(-24)
    q['destino_utc'] = q['origem_utc']+pd.Timedelta(hours=24)
    q['alvo'] = np.log(q['preco_destino']/q['close'])
    q['causal'] = q['retorno'].notna().rolling(336,min_periods=336).sum().eq(336)
    q['observavel'] = q['causal'] & np.isfinite(q['alvo'])
    return q

def preparar(manifesto):
    m = ler_json(manifesto)
    if m['inicio']!='2021-01-01' or m['fim']!='2026-01-01' or m['intervalo']!='1m' or tuple(m['pares'])!=PARES:
        raise ValueError('Coleta incompatível com o protocolo.')
    meses = pd.date_range(m['inicio'],m['fim'],freq='MS',tz='UTC')
    registros = {(r['par'],r['mes']):r for r in m['registros']}
    esperado = {(p,f'{a:%Y-%m}') for p in PARES for a in meses[:-1]}
    if len(registros)!=len(m['registros']) or set(registros)!=esperado or any(r['status']!='auditado' for r in registros.values()):
        raise ValueError('Inventário de coleta inválido.')
    assinatura = {'versao':'retorno24-1.0','inicio':m['inicio'],'fim':m['fim'],
                 'brutos':{f'{p}/{mes}':r['sha256'] for (p,mes),r in sorted(registros.items())},
                 'codigo':{p.name:sha256(p) for p in [Path(__file__),RAIZ/'previsao24/coleta.py']}}
    id_dados = identidade(assinatura)[:20]
    destino = RAIZ/'dados/processados'/f'retorno24_{id_dados}'
    if (destino/'dataset.json').exists():
        verificar_dataset(destino)
        return destino
    destino.mkdir(parents=True,exist_ok=True)
    salvar_json(destino/'preparacao.json',{'status':'em_andamento','inicio_utc':agora(),'assinatura':assinatura})
    a,b = (int(t.timestamp()//60) for t in (meses[0],meses[-1]))
    resumo={}
    causal_comum=observavel_comum=None
    for par in PARES:
        pasta=destino/par
        pasta.mkdir(exist_ok=True)
        minutos=np.full((b-a,6),np.nan,dtype=np.float64)
        for inicio,fim in zip(meses[:-1],meses[1:]):
            mes=f'{inicio:%Y-%m}'
            bruto=RAIZ/'dados/brutos/binance_spot_1m'/par/f'{par}-1m-{mes}.zip'
            registro=registros[par,mes]
            if sha256(bruto)!=registro['sha256']:
                raise ValueError('Fonte bruta alterada após auditoria.')
            quadro,auditoria=ler_mes(bruto,inicio,fim)
            for chave,valor in auditoria.items():
                if registro[chave]!=valor:
                    raise ValueError(f'Contagem divergente {par}/{mes}/{chave}')
            minutos[quadro.index.to_numpy()-a]=quadro.to_numpy()
        np.save(pasta/'minutos.npy',minutos,allow_pickle=False)
        horas=construir_horas(minutos,a)
        horas.to_parquet(pasta/'horas.parquet',index=False)
        causal=horas['causal'].to_numpy()
        observavel=horas['observavel'].to_numpy()
        causal_comum=causal if causal_comum is None else causal_comum & causal
        observavel_comum=observavel if observavel_comum is None else observavel_comum & observavel
        resumo[par]={'horas':len(horas),'horas_ausentes':int(horas['close'].isna().sum()),
                     'minutos_ausentes':int((~np.isfinite(minutos[:,0])).sum()),
                     'origens_causais':int(causal.sum()),'origens_observaveis':int(observavel.sum())}
        print(f'{par}: preparado {resumo[par]}',flush=True)
    np.save(destino/'causal_comum.npy',causal_comum,allow_pickle=False)
    np.save(destino/'observavel_comum.npy',observavel_comum,allow_pickle=False)
    arquivos={p.relative_to(destino).as_posix():sha256(p) for p in sorted(destino.rglob('*')) if p.is_file() and p.name!='preparacao.json'}
    salvar_json(destino/'dataset.json',{'id':id_dados,'assinatura':assinatura,'criado_utc':agora(),'primeiro_minuto':a,'fim_minuto':b,
               'resumo':resumo,'arquivos':arquivos,'causal_comum':int(causal_comum.sum()),'observavel_comum':int(observavel_comum.sum())})
    verificar_dataset(destino)
    salvar_json(destino/'preparacao.json',{'status':'auditada','fim_utc':agora(),'id':id_dados})
    salvar_json(RAIZ/'registros/dataset_atual.json',{'id':id_dados,'caminho':destino.relative_to(RAIZ).as_posix()})
    return destino

def verificar_dataset(pasta):
    m=ler_json(Path(pasta)/'dataset.json')
    if identidade(m['assinatura'])[:20]!=m['id']:
        raise ValueError('Identidade do dataset inválida.')
    verificar_arquivos(pasta,m['arquivos'])
    return m

def separar(horas,observavel_comum,fold):
    cortes=[pd.Timestamp(x,tz='UTC') for x in ('2021-01-01',*FOLDS[fold])]
    if len(horas)!=len(observavel_comum) or horas['origem_utc'].duplicated().any() or not horas['origem_utc'].is_monotonic_increasing:
        raise ValueError('Alinhamento/ordem inválidos.')
    blocos={}
    for nome,a,b in zip(('treino','validacao','teste'),cortes[:-1],cortes[1:]):
        mascara=horas['origem_utc'].ge(a)&horas['origem_utc'].lt(b)&horas['destino_utc'].lt(b)&observavel_comum
        q=horas.loc[mascara].copy().reset_index(drop=True)
        if len(q)==0 or not np.isfinite(q['alvo']).all() or not q['causal'].all():
            raise ValueError(f'Partição inválida: {fold}/{nome}')
        blocos[nome]=q
    # Previsões operacionais NÃO dependem de observabilidade do alvo futuro.
    mascara=horas['causal']&horas['origem_utc'].ge(cortes[2])&horas['origem_utc'].lt(cortes[3])
    blocos['operacional']=horas.loc[mascara].copy().reset_index(drop=True)
    return blocos

def ajustar_escalas(horas,treino):
    usados=np.zeros(len(horas),bool)
    for i in treino['indice_hora'].to_numpy():
        if i<335:
            raise ValueError('Contexto incompleto.')
        usados[i-335:i+1]=True
    valores=horas['retorno'].to_numpy(np.float64)
    amostra=valores[usados]
    alvo=treino['alvo'].to_numpy(np.float64)
    if not np.isfinite(amostra).all():
        raise ValueError('Scaler recebeu ausência.')
    media,escala=float(amostra.mean()),float(amostra.std())
    media_y,escala_y=float(alvo.mean()),float(alvo.std())
    escala=escala or 1.0
    escala_y=escala_y or 1.0
    metadados={'media':media,'escala':escala,'media_alvo':media_y,'escala_alvo':escala_y,'retornos_unicos':int(usados.sum()),
               'inicio_entradas':horas.loc[usados,'origem_utc'].min().isoformat(),'fim_entradas':horas.loc[usados,'origem_utc'].max().isoformat(),
               'ultimo_alvo_treino':treino['destino_utc'].max().isoformat()}
    return ((valores-media)/escala).astype(np.float32),metadados
