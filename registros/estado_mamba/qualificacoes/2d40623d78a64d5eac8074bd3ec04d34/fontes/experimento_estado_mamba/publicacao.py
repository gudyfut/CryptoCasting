"""Extensão: pareamento em três seeds; seis descrevem estabilidade."""
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,sha256,agora
from avaliacao.publicacao import conferir_previsoes,contraste_temporal
from avaliacao.mercado import carregar_minutos
from avaliacao.spot import simular


def publicar(pasta,cfg,partes,tentativas,referencias):
    raiz=pasta/'publicacoes'
    destino=raiz/f'tentativa_{len(list(raiz.glob("tentativa_*")))+1:03d}'
    destino.mkdir(parents=True)
    minutos,primeiro=carregar_minutos(RAIZ/cfg['mercado_pasta'],cfg['par'])
    resumo={};previsoes={};conferencias={}
    todos={**{f'estado8_{s}':t for s,t in tentativas.items()},**referencias}
    for chave,t in todos.items():
        r=ler_json(t/'resultado.json');conferencias[chave]={}
        for b in ('validacao','teste','operacional'):
            q=pd.read_parquet(t/f'previsoes_{b}.parquet')
            conferencias[chave][b]=conferir_previsoes(q,partes[b],r['metricas'].get(b))
            previsoes[chave,b]=q
        spot={}
        for nome,agravado in [('base',False),('agravado',True)]:
            s,ops,curva=simular(previsoes[chave,'operacional'],minutos,primeiro,cfg['divisao']['teste'][1],cfg['operacao'],agravado=agravado)
            spot[nome]=s
            # Marcas de caixa depois da saída da posição anterior ficam no horário de liquidação.
            for ponto in curva:
                data=pd.Timestamp(ponto['tempo_utc'])
                if data.minute==0:
                    ponto['tempo_utc']=(data+pd.Timedelta(minutes=cfg['operacao']['latencia_minutos'])).isoformat()
            salvar_json(destino/chave/f'operacoes_{nome}.json',ops)
            salvar_json(destino/chave/f'curva_{nome}.json',curva)
        bruto=previsoes[chave,'operacional'].copy()
        f,s=cfg['operacao']['taxa'],cfg['operacao']['slippage']
        limiar=np.log((1+s)*(1+f)/((1-s)*(1-f)))
        bruto['previsao']=(bruto.previsao>limiar).astype(float)
        spot['bruto_mesmos_sinais']=simular(bruto,minutos,primeiro,cfg['divisao']['teste'][1],dict(cfg['operacao'],taxa=0.,slippage=0.))[0]
        trimestres={}
        q=previsoes[chave,'teste'];tri=pd.DatetimeIndex(q.origem_utc).quarter
        for n in range(1,5):
            v=q.loc[tri==n]
            trimestres[str(n)]={'n':len(v),'mse':float(np.mean((v.previsao-v.alvo)**2)),'mse_naive':float(np.mean(v.alvo**2))}
        resumo[chave]={'metricas':r['metricas'],'spot':spot,'trimestres':trimestres,
                      'origem_ajuste':'novo' if chave.startswith('estado8_') else 'herdado_R0'}
    grupos={'estado8_pareadas':[f'estado8_{s}' for s in cfg['seeds_pareadas']],
            'estado16_pareadas':[f'estado16_{s}' for s in cfg['seeds_pareadas']],
            'estado8_seis':[f'estado8_{s}' for s in cfg['seeds']],
            'lstm_herdada':[f'lstm_{s}' for s in cfg['seeds_pareadas']],
            'naive':['naive'],'arima':['arima']}
    medias={};contrastes={}
    for b in ('validacao','teste'):
        perdas={g:np.mean([(previsoes[k,b].previsao.to_numpy()-previsoes[k,b].alvo.to_numpy())**2 for k in ks],axis=0) for g,ks in grupos.items()}
        medias[b]={g:{'mse':float(v.mean()),'mse_por_seed':{k:resumo[k]['metricas'][b]['mse'] for k in grupos[g]},
                       'habilidade_naive':float(1-v.mean()/perdas['naive'].mean())} for g,v in perdas.items()}
        comparacoes=[('estado8_pareadas','estado16_pareadas'),('estado8_seis','naive'),('estado8_pareadas','lstm_herdada')]
        contrastes[b]={f'{a}_menos_{z}':contraste_temporal(partes[b].origem_utc,perdas[a],perdas[z],cfg['bootstrap']) for a,z in comparacoes}
    salvar_json(destino/'conferencia_metricas.json',conferencias)
    salvar_json(destino/'resultados.json',{'utc':agora(),'natureza':cfg['exposicao'],'por_ajuste':resumo,'medias':medias,'contrastes':contrastes,
        'principal':'estado8_pareadas_menos_estado16_pareadas, mesmas seeds17/42/2026',
        'limites':['seis seeds da candidata não constituem comparação pareada com três da referência',
                   'sem repetição completa de seed em mercado nesta extensão; orçamento seis ajustes',
                   'política e contabilidade R0 mantidas; auditoria Binance é análise separada',
                   'períodos já consultados; avaliação retrospectiva, não holdout intocado']})
    salvar_json(destino/'manifesto.json',{'arquivos':{q.relative_to(destino).as_posix():sha256(q) for q in destino.rglob('*') if q.is_file()}})
    salvar_json(pasta/'publicacao.json',{'pasta':destino.relative_to(pasta).as_posix(),'manifesto_sha256':sha256(destino/'manifesto.json')})
