"""Exportação de previsões auditadas, sem treinamento ou seleção de resultados."""
import gzip
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from previsao24.arquivos import RAIZ,ler_json,salvar_json,sha256,verificar_arquivos,identidade,agora
from previsao24.configuracao import FOLDS

def exportar():
    ponteiro=ler_json(RAIZ/'registros/execucao_atual.json')
    execucao=RAIZ/ponteiro['caminho']
    registro=ler_json(execucao/'execucao.json')
    c=registro['assinatura']['configuracao']
    dataset=RAIZ/registro['dataset_caminho']
    destino=RAIZ/'dados/portal'
    destino.mkdir(parents=True,exist_ok=True)
    (destino/'series').mkdir(exist_ok=True)
    salvar_json(destino/'metodologia.json',{'configuracao':c,'periodos':FOLDS,'dataset':ler_json(dataset/'dataset.json')})
    metricas=[]
    modelos={}
    fontes={}
    for p in sorted(execucao.glob('celulas/*/tentativa_*/tentativa.json')):
        tentativa=ler_json(p)
        if tentativa['status']!='auditada':
            continue
        celula=tentativa['celula']
        if celula['fold'].startswith('B') and not celula['fold'].startswith('DB') and not (execucao/'congelamento.json').exists():
            raise ValueError('Resultado de avaliação sem congelamento.')
        auditoria=ler_json(p.parent/'auditoria.json')
        verificar_arquivos(p.parent,auditoria['arquivos'])
        resultado=ler_json(p.parent/'resultado.json')
        linha={**celula,**resultado['metricas']['teste'],'fase':'desenvolvimento' if celula['fold'].startswith('DB') else 'avaliacao',
               'epoca':resultado.get('epoca_selecionada'),'segundos':resultado.get('segundos'),
               'parametros':resultado.get('parametros'),'ordem':resultado.get('ordem')}
        metricas.append(linha)
        chave=(celula['par'],celula['fold'],celula.get('contexto'),celula.get('seed'),celula['modelo'])
        if chave in modelos:
            raise ValueError('Duas tentativas auditadas para a mesma célula; não escolher silenciosamente.')
        modelos[chave]=pd.read_parquet(p.parent/'previsoes_teste.parquet')
        fontes[p.parent.relative_to(RAIZ).as_posix()]=sha256(p.parent/'auditoria.json')
    series=[]
    grupos=sorted({k[:4] for k in modelos if k[2] is not None})
    horas_cache={}
    for par,fold,w,seed in grupos:
        if par not in horas_cache:
            horas_cache[par]=pd.read_parquet(dataset/par/'horas.parquet')
        horas=horas_cache[par]
        presentes={m:modelos[(par,fold,w,seed,m)] for m in ('lstm','mamba') if (par,fold,w,seed,m) in modelos}
        presentes.update({m:modelos[(par,fold,None,None,m)] for m in ('naive','arima') if (par,fold,None,None,m) in modelos})
        referencia=next(iter(presentes.values()))
        for q in presentes.values():
            if not q['origem_utc'].equals(referencia['origem_utc']) or not q['alvo'].equals(referencia['alvo']):
                raise ValueError('Exportação não pode alinhar por número de linha.')
        chave={'par':par,'fold':fold,'contexto':w,'seed':seed}
        id_serie=identidade(chave)[:20]
        origens=[]
        # A igualdade de timestamps foi verificada; arrays permanecem na ordem comum.
        for i,r in referencia.iterrows():
            origens.append({'tempo':int(r['origem_utc'].timestamp()),'destino':int(r['destino_utc'].timestamp()),
                            'preco':float(r['close']),'preco_real':float(r['preco_destino']),'retorno_real':float(r['alvo']),
                            'previsoes':{m:float(q.iloc[i]['previsao']) for m,q in presentes.items()}})
        a=pd.Timestamp(FOLDS[fold][1],tz='UTC')-pd.Timedelta(hours=336)
        b=pd.Timestamp(FOLDS[fold][2],tz='UTC')
        recorte=horas.loc[horas['origem_utc'].ge(a)&horas['origem_utc'].le(b)]
        precos=[]
        for r in recorte.itertuples(index=False):
            preco={'time':int(r.origem_utc.timestamp())}
            if np.isfinite(r.close):
                preco.update(open=r.open,high=r.high,low=r.low,close=r.close,volume=r.volume)
            precos.append(preco)
        corpo={'id':id_serie,**chave,'modelos':list(presentes),'origens':origens,'precos':precos,
               'convencao_tempo':'Candles identificados pelo fechamento exclusivo UTC; forecast em t para t+24h.'}
        serializado=json.dumps(corpo,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()
        # Nome imutável por conteúdo: leitores do índice anterior continuam válidos.
        versao=identidade(corpo)[:20]
        caminho=destino/'series'/f'{id_serie}_{versao}.json.gz'
        temporario=caminho.with_suffix('.parcial')
        temporario.write_bytes(gzip.compress(serializado,mtime=0))
        temporario.replace(caminho)
        series.append({'id':id_serie,**chave,'modelos':list(presentes),'n':len(origens),'sha256':sha256(caminho),
                       'arquivo':f'series/{caminho.name}','fase':'desenvolvimento' if fold.startswith('DB') else 'avaliacao'})
    salvar_json(destino/'resumo.json',{'versao':'retorno24-1.0','gerado_utc':agora(),'execucao':ponteiro['id'],'dataset':ponteiro['dataset'],
                                     'configuracao':c,'desenvolvimento_completo':(execucao/'desenvolvimento_concluido.json').exists(),
                                     'avaliacao_completa':(execucao/'avaliacao_concluido.json').exists(),
                                     'metricas':metricas,'series':series,'fontes':fontes,'exportador_sha256':sha256(Path(__file__))})
    print(f'{len(metricas)} resultados auditados; {len(series)} séries exportadas.',flush=True)

if __name__=='__main__':
    exportar()
