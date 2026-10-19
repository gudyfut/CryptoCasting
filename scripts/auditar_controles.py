"""Reconstrói comprar/manter e verifica controles sem modificar as execuções."""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(RAIZ))
from barreiras.arquivos import ler_json,salvar_json,sha256,agora
from barreiras.configuracao import FOLDS
from barreiras.estatistica import incerteza_financeira


def construir_controle(minutos,primeiro_minuto,entrada,inicio,fim):
    a=int(pd.Timestamp(inicio).timestamp()//60)-primeiro_minuto
    b=int(pd.Timestamp(fim).timestamp()//60)-primeiro_minuto
    saida=b-1;precos=minutos[entrada:saida+1]
    curva=np.full(b-a,10000.);pior=curva.copy();exposto=np.zeros(b-a,bool)
    observavel=np.isfinite(precos[:,:4]).all() and precos[0,5]>0 and precos[-1,5]>0
    entrada_valida=np.isfinite(precos[0,0]) and precos[0,5]>0
    if entrada_valida:
        quantidade=10000./(precos[0,0]*1.0005*1.001)
        curva[entrada-a:]=quantidade*precos[:,3]*.9995*.999
        pior[entrada-a:]=quantidade*precos[:,2]*.9995*.999
        curva[-1]=quantidade*precos[-1,0]*.9995*.999
        pior[-1]=curva[-1]
        exposto[entrada-a:-1]=True
    else:
        curva[entrada-a:]=np.nan;pior[entrada-a:]=np.nan
    q=pd.DataFrame({'minuto_utc':np.arange(a,b)+primeiro_minuto,'patrimonio':curva,
                    'pior_marca_observavel':pior,'exposto':exposto})
    if not observavel:
        return {'status':'nao_auditavel','retorno_liquido':None},q
    pico=np.maximum.accumulate(np.r_[10000.,curva])[1:]
    return {'status':'auditavel','capital_final':float(curva[-1]),
            'retorno_liquido':float(curva[-1]/10000.-1),'drawdown_maximo':float((1-curva/pico).max())},q


def retorno_entre_pontas(minutos,primeiro_minuto,entrada,fim):
    """Complemento para saída fixa; não resolve estratégias dependentes do percurso."""
    saida=int(pd.Timestamp(fim).timestamp()//60)-primeiro_minuto-1
    resultado={'metodo':'comprar_manter_com_saida_fixa_pontas_observadas',
        'status':'pontas_nao_observadas','retorno_liquido':None,'capital_final':None,
        'drawdown_maximo':None,'taxa_por_lado':.001,'slippage_por_lado':.0005}
    if not 0<=entrada<saida<len(minutos):
        return resultado
    resultado.update(entrada_utc=pd.to_datetime(primeiro_minuto+entrada,unit='m',utc=True).isoformat(),
        saida_utc=pd.to_datetime(primeiro_minuto+saida,unit='m',utc=True).isoformat())
    inicio_preco,fim_preco=float(minutos[entrada,0]),float(minutos[saida,0])
    if not (np.isfinite(inicio_preco) and np.isfinite(fim_preco) and inicio_preco>0 and fim_preco>0
            and minutos[entrada,5]>0 and minutos[saida,5]>0):
        return resultado
    capital=10000.*fim_preco/inicio_preco*.9995*.999/(1.0005*1.001)
    resultado.update(status='pontas_observadas',preco_entrada=inicio_preco,preco_saida=fim_preco,
        capital_final=float(capital),retorno_liquido=float(capital/10000.-1))
    return resultado


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('diretorio',type=Path)
    args=parser.parse_args();raiz=args.diretorio; ciclo=ler_json(raiz/'ciclo.json')
    dataset=RAIZ/'dados/processados'/f"barreiras_{ciclo['assinatura']['dataset']}"
    meta=ler_json(dataset/'dataset.json');destino=raiz/'consolidacao/controles';destino.mkdir(parents=True,exist_ok=True)
    controles={};verificacoes=[];mapas={}
    for p in sorted(raiz.glob('*/estado.json')):
        estado=ler_json(p)
        if estado['status']!='concluida_auditada':
            continue
        if estado['id_ciclo']!=ciclo['id']:
            raise ValueError('Identidade divergente.')
        celula=estado['celula'];par=celula['par'];fold=celula['fold'];chave=par+'_'+fold
        if par not in mapas:
            arquivo=dataset/par/'minutos.npy'
            if sha256(arquivo)!=meta['arquivos'][f'{par}/minutos.npy']:
                raise ValueError('Minutos do dataset foram alterados.')
            mapas[par]=np.load(arquivo,mmap_mode='r')
        hashes=ler_json(p.parent/'integridade.json')
        for nome in ('mamba','lstm','ar1'):
            rel=f'{nome}/previsoes_operacional.parquet';arquivo=p.parent/rel
            if sha256(arquivo)!=hashes[rel] or sha256(p.parent/nome/'financeiro.json')!=hashes[f'{nome}/financeiro.json']:
                raise ValueError('Artefato financeiro foi alterado.')
            previsoes=pd.read_parquet(arquivo,columns=['entrada_indice','origem_utc'])
            entrada=int(previsoes.entrada_indice.iloc[0])
            if chave not in controles:
                limites=FOLDS[fold].limites()
                resultado,curva=construir_controle(mapas[par],meta['primeiro_minuto'],entrada,limites[2],limites[3])
                arquivo_curva=destino/f'{chave}.parquet';curva.to_parquet(arquivo_curva,index=False)
                controles[chave]={'par':par,'fold':fold,'entrada_indice':entrada,'resultado':resultado,
                    'curva':arquivo_curva.name,'sha256':sha256(arquivo_curva),
                    'complemento_pontas':retorno_entre_pontas(mapas[par],meta['primeiro_minuto'],entrada,limites[3]),
                    'incerteza':incerteza_financeira(curva) if resultado['status']=='auditavel' else {'status':'nao_auditavel','intervalos':None}}
            controle=controles[chave]
            if controle['entrada_indice']!=entrada:
                raise ValueError('Comprar/manter começou em origens diferentes entre contextos/modelos.')
            oficial=ler_json(p.parent/nome/'financeiro.json')['comprar_manter'];esperado=controle['resultado']
            if esperado['status']=='auditavel' and not np.isclose(esperado['retorno_liquido'],
                    controle['complemento_pontas']['retorno_liquido'],rtol=1e-10,atol=1e-12):
                raise ValueError('Retorno entre pontas diverge do controle integral observado.')
            if oficial['status']!=esperado['status']:
                raise ValueError('Status do controle divergiu.')
            for campo in ('retorno_liquido','capital_final','drawdown_maximo'):
                if esperado.get(campo) is None:
                    if oficial.get(campo) is not None:
                        raise ValueError('Controle publicou métrica de percurso não auditável.')
                elif not np.isclose(esperado[campo],oficial[campo],rtol=1e-10,atol=1e-12):
                    raise ValueError(f'Métrica do controle divergiu: {campo}')
            verificacoes.append({'execucao':estado['id'],'modelo':nome,'controle':chave,'status':'aprovado'})
    concatenados=[];pontas_concatenadas=[]
    for par in ciclo['assinatura']['configuracao']['pares']:
        folds=ciclo['assinatura']['configuracao']['folds']
        disponiveis=[controles.get(par+'_'+f) for f in folds]
        valido=all(r and r['resultado']['status']=='auditavel' for r in disponiveis)
        registro={'par':par,'status':'auditavel' if valido else 'incompleto_ou_nao_auditavel','retorno_liquido':None}
        if valido:
            capital=10000.;partes=[]
            for r in disponiveis:
                q=pd.read_parquet(destino/r['curva']);q['patrimonio']*=capital/10000.;q['pior_marca_observavel']*=capital/10000.
                capital=float(q.patrimonio.iloc[-1]);partes.append(q)
            curva=pd.concat(partes,ignore_index=True);arquivo=destino/f'{par}_concatenado.parquet';curva.to_parquet(arquivo,index=False)
            picos=np.maximum.accumulate(np.r_[10000.,curva.patrimonio])[1:]
            registro.update(retorno_liquido=capital/10000.-1,drawdown_maximo=float((1-curva.patrimonio.to_numpy()/picos).max()),curva=arquivo.name,sha256=sha256(arquivo))
        concatenados.append(registro)
        pontas=[r['complemento_pontas'] if r else None for r in disponiveis]
        pontas_validas=all(r and r['status']=='pontas_observadas' for r in pontas)
        pontas_concatenadas.append({'par':par,'folds_esperados':folds,
            'status':'pontas_observadas' if pontas_validas else 'incompleto_ou_pontas_nao_observadas',
            'retorno_liquido':float(np.prod([1+r['retorno_liquido'] for r in pontas])-1) if pontas_validas else None,
            'drawdown_maximo':None})
    salvar_json(destino/'auditoria.json',{'id_ciclo':ciclo['id'],'verificado_utc':agora(),
        'script_sha256':sha256(Path(__file__)),'verificacoes':verificacoes,'controles':list(controles.values()),
        'concatenados':concatenados,'complemento_pontas_concatenadas':pontas_concatenadas,
        'caixa':{'retorno_liquido':0.,'drawdown_maximo':0.},
        'nota_complemento_pontas':'Análise descritiva posterior: saída fixa permite conferir retorno entre preços observados, mesmo com lacuna intermediária. Não reconstitui risco, não preenche preços e não altera os estados do contrato executado. Inaplicável às políticas de barreiras, cuja saída depende do percurso.',
        'nota':'Curvas com lacunas preservam NaN e não sustentam métricas integrais. Nenhum preço foi interpolado.'})
    print(f'{len(verificacoes)} controles conferidos, {len(controles)} trajetórias únicas.')


if __name__=='__main__':
    main()
