"""Leitura do checkpoint público já inferido; não importa o executor de inferência."""
import importlib.util
from copy import deepcopy
import pandas as pd
from infraestrutura.artefatos import RAIZ,ler_json,sha256
from .adaptadores import conferir_reproducao


def recalcular():
    pasta=RAIZ/'registros/diagnosticos_previsoes/cryptomamba_custos_20261103'
    manifesto=ler_json(pasta/'manifesto_final.json')
    for nome in ['analisar_custos.py','custos_resultados.json']+[f'{m}_{f}_insumos.csv' for m in ('cmamba_nv','cmamba_v') for f in ('val','test')]:
        if sha256(pasta/nome)!=manifesto[nome]:raise ValueError('Fonte pública divergente: '+nome)
    spec=importlib.util.spec_from_file_location('custos_publicos_somente_primitiva',pasta/'analisar_custos.py')
    modulo=importlib.util.module_from_spec(spec);spec.loader.exec_module(modulo)
    antigo=ler_json(pasta/'custos_resultados.json');novo=deepcopy(antigo);ledgers={};n=0
    cenarios={'ideal':{},'taxa_010':{'taxa':.001},'taxa_010_slip_005':{'taxa':.001,'slippage':.0005},
        'taxa_020_slip_010':{'taxa':.002,'slippage':.001},
        'abertura_custos_filtros':{'taxa':.001,'slippage':.0005,'minimo':5.,'passo':.00001,'abertura':True},
        'short_juros_001dia':{'taxa':.001,'slippage':.0005,'juros_dia':.0001},
        'short_juros_005dia':{'taxa':.001,'slippage':.0005,'juros_dia':.0005}}
    for serie,politicas in antigo['series'].items():
        df=pd.read_csv(pasta/f'{serie}_insumos.csv')
        for politica,casos in politicas.items():
            for caso,esperado in casos.items():
                args=deepcopy(cenarios[caso]);r=modulo.simular(df,politica,**args);r.pop('lancamentos');conferir_reproducao(esperado,r)
                if 'slippage' in args:args['slippage']*=.2
                r=modulo.simular(df,politica,**args);ledgers[f'{serie}/{politica}/{caso}']=r.pop('lancamentos')
                novo['series'][serie][politica][caso]=r;n+=1
    return novo,ledgers,{'carteiras':n,'fontes':{str((pasta/k).relative_to(RAIZ).as_posix()):v for k,v in manifesto.items() if k in ['analisar_custos.py','custos_resultados.json'] or k.endswith('_insumos.csv')}}
