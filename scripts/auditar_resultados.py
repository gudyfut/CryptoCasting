"""Auditoria suplementar entre registros, arquivos, checkpoints e métricas primárias."""
import argparse
import hashlib
import itertools
import json
from datetime import datetime,timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch


RAIZ=Path(__file__).resolve().parents[1]


def ler(p):
    return json.loads(p.read_text(encoding='utf-8'))


def resumo_hash(objeto):
    return hashlib.sha256(json.dumps(objeto,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def hash_arquivo(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for trecho in iter(lambda:f.read(1024*1024),b''):
            h.update(trecho)
    return h.hexdigest()


def verificar_tentativa(pasta,ciclo):
    r=ler(pasta/'estado.json');c=ciclo['assinatura']['configuracao'];celula=r['celula']
    if r['status']!='concluida_auditada' or r['auditoria']!='aprovado':
        raise ValueError('Tentativa ainda não concluída e auditada.')
    if r['id_ciclo']!=ciclo['id'] or r['dataset']!=ciclo['assinatura']['dataset'] or r['codigo']!=resumo_hash(ciclo['assinatura']['codigo']):
        raise ValueError('Registro mistura identidades.')
    if ler(pasta/'configuracao.json')!=ciclo['assinatura']:
        raise ValueError('Configuração da tentativa diverge do ciclo.')
    if not (pasta/'concluido.json').exists() or ler(pasta/'auditoria.json')['status']!='aprovado':
        raise ValueError('Ausência de conclusão ou auditoria.')
    hashes=ler(pasta/'integridade.json')
    for rel,h in hashes.items():
        p=(pasta/rel).resolve()
        if not p.is_relative_to(pasta.resolve()) or hash_arquivo(p)!=h:
            raise ValueError(f'Arquivo ausente ou alterado: {rel}')
    for rel,h in ciclo['assinatura']['codigo'].items():
        if hash_arquivo(pasta/'fontes'/rel)!=h:
            raise ValueError('Snapshot de fontes diverge da identidade científica.')
    ambiente=ler(pasta/'ambiente.json')
    if any(ambiente[k]!=v for k,v in ciclo['assinatura']['ambiente'].items()):
        raise ValueError('Ambiente diverge da identidade científica.')
    if r['referencia_constante']!=ler(pasta/'referencia_constante.json') or r['comparacoes']!=ler(pasta/'comparacoes.json'):
        raise ValueError('Resumo de referência/contrastes diverge do artefato auditado.')
    fold=celula['fold']
    if fold not in ('DB1','DB2','DB3','DB4'):
        raise ValueError('Resultado fora do desenvolvimento autorizado.')
    inicio=pd.Timestamp('2023-01-01',tz='UTC')+pd.DateOffset(months=3*(int(fold[-1])-1))
    fim=inicio+pd.DateOffset(months=3)
    escalas=ler(pasta/'escalas.json');primeiro=None;relatorio={}
    if pd.Timestamp(escalas['ultima_expiracao_treino'])>=inicio-pd.DateOffset(months=3):
        raise ValueError('Treino cruza a validação.')
    for nome in ('mamba','lstm','ar1'):
        resultado=ler(pasta/nome/'resultado_modelo.json')
        financeiro=ler(pasta/nome/'financeiro.json')
        if resultado!=r['resultados'][nome] or financeiro!=r['financeiro'][nome]:
            raise ValueError('Registro resumido diverge dos resultados auditados.')
        q=pd.read_parquet(pasta/nome/'previsoes_teste.parquet')
        if not q.origem_utc.is_monotonic_increasing or q.origem_utc.duplicated().any():
            raise ValueError('Origens desordenadas ou duplicadas.')
        if not (q.origem_utc.ge(inicio)&q.expiracao_maxima_utc.lt(fim)).all():
            raise ValueError('Previsões violam o calendário ou a purga.')
        if primeiro is None:
            primeiro=q[['origem_utc','classe']]
        elif not primeiro.equals(q[['origem_utc','classe']]):
            raise ValueError('Modelos comparados em populações distintas.')
        probs=q[['p0','p1','p2']].to_numpy(dtype=float);y=q.classe.to_numpy(dtype=int)
        if not np.isfinite(probs).all() or (probs<0).any() or (probs>1).any() or not np.isin(y,[0,1,2]).all() or not np.allclose(probs.sum(axis=1),1,atol=1e-6):
            raise ValueError('Probabilidades inválidas.')
        nll=float(-np.log(np.maximum(probs[np.arange(len(y)),y],1e-7)).mean())
        brier=float(np.square(probs-np.eye(3)[y]).sum(axis=1).mean())
        for chave,valor in [('n',len(y)),('log_loss',nll),('brier',brier)]:
            if not np.isclose(resultado['metricas']['teste'][chave],valor,rtol=1e-10,atol=1e-12):
                raise ValueError(f'Métrica primária divergente: {nome}/{chave}')
        for variante in ('base','custos_agravados','ambiguidade_superior','sem_filtro'):
            f=financeiro[variante];ordens=pd.read_parquet(pasta/nome/f'ordens_{variante}.parquet')
            curva=pd.read_parquet(pasta/nome/f'curva_{variante}.parquet')
            if f['status']=='auditavel':
                if len(ordens)!=f['operacoes'] or not np.isfinite(curva.patrimonio).all():
                    raise ValueError('Contagem ou curva financeira divergente.')
                if not np.isclose(curva.patrimonio.iloc[-1]/10000.-1,f['retorno_liquido'],rtol=1e-10,atol=1e-12):
                    raise ValueError('Retorno financeiro diverge da curva.')
                if len(ordens):
                    if not np.isclose(ordens.lucro.sum(),curva.patrimonio.iloc[-1]-10000.,rtol=1e-10,atol=1e-9):
                        raise ValueError('Lucros do livro não fecham com o caixa.')
            elif f['status']=='nao_auditavel':
                if f['retorno_liquido'] is not None or np.isfinite(curva.patrimonio).all():
                    raise ValueError('Lacuna não está representada no resultado.')
            else:
                raise ValueError('Status financeiro desconhecido.')
        if nome!='ar1':
            cp=torch.load(pasta/nome/'checkpoint.pt',map_location='cpu',weights_only=True)
            epocas=ler(pasta/nome/'epocas.json')
            melhor=min(epocas,key=lambda x:x['validacao_log_loss'])
            if cp['configuracao']!=c or cp['celula']!=celula or cp['escalas']!=escalas or cp['modelo']!=nome:
                raise ValueError('Metadados do checkpoint divergem da execução.')
            if cp['epoca']!=melhor['epoca'] or cp['epoca']!=resultado['epoca_selecionada'] or not resultado['recarga_exata']:
                raise ValueError('Seleção ou recarga do checkpoint inconsistente.')
            if not all(torch.isfinite(p).all() for p in cp['pesos'].values()):
                raise ValueError('Checkpoint contém pesos não finitos.')
        relatorio[nome]={'n':len(y),'log_loss_recalculada':nll,'brier_recalculado':brier,
                         'registro_coincide_com_artefatos':True}
    return {'id':r['id'],'celula':celula,'status':'aprovado','modelos':relatorio}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('diretorio',type=Path);parser.add_argument('--parcial',action='store_true')
    args=parser.parse_args();raiz=args.diretorio.resolve();ciclo=ler(raiz/'ciclo.json')
    if resumo_hash(ciclo['assinatura'])[:20]!=ciclo['id']:
        raise ValueError('Identidade global inválida.')
    c=ciclo['assinatura']['configuracao']
    chaves=('par','contexto','horizonte','fold','seed')
    grade=[dict(zip(chaves,valores)) for valores in itertools.product(c['pares'],c['contextos'],c['horizontes'],c['folds'],c['seeds'])]
    esperadas={resumo_hash(x) for x in grade};auditadas=[];vistas=set()
    for p in sorted(raiz.glob('*/estado.json')):
        r=ler(p)
        if r['status']!='concluida_auditada':
            continue
        chave=resumo_hash(r['celula'])
        if chave not in esperadas or chave in vistas:
            raise ValueError('Célula estranha à grade ou duplicada.')
        auditadas.append(verificar_tentativa(p.parent,ciclo));vistas.add(chave)
    completo=vistas==esperadas
    if not completo and not args.parcial:
        raise ValueError(f'Grade incompleta: {len(vistas)}/{len(esperadas)}. Não certificar conclusão.')
    resultado={'id_ciclo':ciclo['id'],'status':'aprovado' if completo else 'parcial',
        'verificado_utc':datetime.now(timezone.utc).isoformat(),'esperadas':len(esperadas),
        'auditadas':len(auditadas),'script_sha256':hash_arquivo(Path(__file__)),'verificacoes':auditadas}
    destino=raiz/'consolidacao/auditoria_suplementar.json';destino.parent.mkdir(exist_ok=True)
    destino.write_text(json.dumps(resultado,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    print({k:resultado[k] for k in ('status','auditadas','esperadas')})


if __name__=='__main__':
    main()
