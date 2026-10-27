"""Conferência independente das médias publicadas e decisões/contas financeiras."""
import argparse
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from previsao24.arquivos import RAIZ,ler_json,salvar_json,sha256,verificar_arquivos,agora
from previsao24.configuracao import FOLDS
from previsao24.dados import verificar_dataset

def proximo(a,b):
    if a is None or b is None:
        if a is not b:
            raise ValueError('Ausência convertida em resultado numérico.')
    elif not np.isclose(a,b,rtol=1e-10,atol=1e-12):
        raise ValueError(f'Recálculo independente divergente: {a} != {b}')

def auditar(fase):
    ponteiro=ler_json(RAIZ/'registros/execucao_atual.json')
    pasta=RAIZ/ponteiro['caminho']
    execucao=ler_json(pasta/'execucao.json')
    verificar_arquivos(RAIZ,execucao['assinatura']['fontes'])
    destino=RAIZ/'registros/analises'/ponteiro['id']/fase
    publicacao=ler_json(destino/'publicacao.json')
    verificar_arquivos(destino,publicacao['arquivos'])
    a=ler_json(destino/'resumo.json')
    dados=RAIZ/execucao['dataset_caminho']
    manifesto=verificar_dataset(dados)
    if manifesto['id']!=a['dataset'] or manifesto['id']!=execucao['assinatura']['dataset'] or sha256(dados/'dataset.json')!=a['dataset_manifesto_sha256']:
        raise ValueError('Dataset da publicação alterado ou incompatível.')
    c=a['configuracao']
    folds=c['folds_desenvolvimento'] if fase=='desenvolvimento' else c['folds_avaliacao']
    linhas=[]
    operacionais={}
    candidatos=0
    for relativo,hash_auditoria in a['fontes'].items():
        local=RAIZ/relativo
        if sha256(local/'auditoria.json')!=hash_auditoria:
            raise ValueError('Fonte da consolidação alterada.')
        verificar_arquivos(local,ler_json(local/'auditoria.json')['arquivos'])
        x=ler_json(local/'tentativa.json')['celula']
        q=pd.read_parquet(local/'previsoes_teste.parquet')
        e=q['previsao'].to_numpy()-q['alvo'].to_numpy()
        mse=float(np.dot(e,e)/len(e))
        m0=float(np.dot(q['alvo'],q['alvo'])/len(q))
        publicados=[r for r in a['ajustes'] if all(r.get(k)==x.get(k) for k in ('par','fold','modelo','contexto','seed'))]
        if len(publicados)!=1:
            raise ValueError('Diagnóstico sem ajuste único correspondente.')
        publicado=publicados[0]
        for coluna,sufixo in (('previsao','previsao'),('alvo','alvo')):
            valores=q[coluna].to_numpy()
            media=float(np.sum(valores)/len(valores))
            desvio=float(np.linalg.norm(valores-media)/np.sqrt(len(valores)))
            proximo(publicado['media_'+sufixo],media)
            proximo(publicado['desvio_'+sufixo],desvio)
        linhas.append({**x,'mse':mse,'mae':float(np.abs(e).sum()/len(e)),'habilidade_mse':1-mse/m0 if m0 else None})
        operacionais[x['par'],x['fold'],x.get('contexto'),x.get('seed'),x['modelo']]=pd.read_parquet(local/'previsoes_operacional.parquet')
        if x['modelo']=='arima':
            candidatos+=len(ler_json(local/'candidatos.json')['candidatos'])
    esperado=len(c['pares'])*len(folds)*(len(c['contextos'])*len(c['seeds'])*2+2)
    if len(linhas)!=esperado or candidatos!=len(c['pares'])*len(folds)*len(c['arima']['ordens']):
        raise ValueError('Inventário de ajustes/candidatos incompleto.')
    for media in a['metricas']:
        celula=[r for r in linhas if r['par']==media['par'] and r['fold']==media['fold'] and r['modelo']==media['modelo'] and r.get('contexto',media['contexto'])==media['contexto']]
        n=len(c['seeds']) if media['modelo'] in ('lstm','mamba') else 1
        if len(celula)!=n:
            raise ValueError('Número de seeds/referências incorreto.')
        for chave in ('mse','mae','habilidade_mse'):
            proximo(media[chave],float(np.mean([r[chave] for r in celula])))
        proximo(media['rmse'],np.sqrt(media['mse']))
    for modelo in a['modelos']:
        medias=[r for r in a['metricas'] if r['modelo']==modelo['modelo']]
        for chave in ('mse','mae','habilidade_mse'):
            proximo(modelo[chave],float(np.mean([r[chave] for r in medias])))
    for familia in a['estabilidade']:
        escores=[]
        for seed in familia['por_seed']:
            itens=[r for r in linhas if r['modelo']==familia['modelo'] and r.get('seed')==seed['seed']]
            valor=float(np.mean([r['mse'] for r in itens]))
            escores.append(valor)
            proximo(seed['mse'],valor)
            proximo(seed['habilidade_mse'],float(np.mean([r['habilidade_mse'] for r in itens])))
        proximo(familia['mse_desvio_entre_seeds'],float(np.std(escores)))
    for contraste in a['contrastes']:
        primeiro,segundo=contraste['contraste'].split('_menos_')
        globais={r['modelo']:r['mse'] for r in a['modelos']}
        proximo(contraste['diferenca'],globais[primeiro]-globais[segundo])
    p=c['operacao']
    limiar=np.log((1+p['slippage'])*(1+p['taxa'])/((1-p['slippage'])*(1-p['taxa'])))
    ordens_conferidas=0
    precos_por_par={par:np.load(dados/par/'minutos.npy',mmap_mode='r') for par in c['pares']}
    for estrategia in a['financeiro']:
        minutos=precos_por_par[estrategia['par']]
        registro=ler_json(destino/estrategia['arquivo'])
        previstos=[]
        modelo='naive' if estrategia['modelo']=='compra_diaria' else estrategia['modelo']
        for fold in folds:
            q=operacionais[estrategia['par'],fold,estrategia['contexto'],estrategia['seed'],modelo]
            t=q['origem_utc']
            calendario=(t.dt.hour==p['hora_utc'])&(t.dt.minute==0)&((t+pd.Timedelta(hours=24,minutes=p['latencia_minutos']))<pd.Timestamp(FOLDS[fold][2],tz='UTC'))
            sinal=True if estrategia['controle'] else q['previsao']>limiar
            previstos.extend(q.loc[calendario&sinal,'origem_utc'].map(lambda v:v.isoformat()).tolist())
        ordens=registro['ordens']
        if previstos!=[o['origem_utc'] for o in ordens] or len(ordens)!=estrategia['entradas_planejadas']:
            raise ValueError('Operações não correspondem às decisões causais/calendarizadas.')
        agravado=estrategia['cenario']!='base'
        taxa=p['taxa_agravada'] if agravado else p['taxa']
        slippage=p['slippage_agravado'] if agravado else p['slippage']
        capital=p['capital']
        custo_total=0.
        for o in ordens:
            proximo(o['capital_entrada'],capital)
            entrada=int(pd.Timestamp(o['origem_utc']).timestamp()//60)+p['latencia_minutos']
            saida=entrada+1440
            if o['entrada_minuto']!=entrada or o['saida_minuto']!=saida:
                raise ValueError('Horários de execução não correspondem à política.')
            e,v=entrada-manifesto['primeiro_minuto'],saida-manifesto['primeiro_minuto']
            pontas_validas=(0<=e<v<len(minutos) and np.isfinite(minutos[[e,v],0]).all() and (minutos[[e,v],5]>0).all())
            if capital is None or not pontas_validas:
                if o['status']!='nao_auditavel' or o['capital_saida'] is not None:
                    raise ValueError('Ausência de preço/capital convertida em operação auditável.')
                capital=None
                continue
            if o['status']!='pontas_observadas':
                raise ValueError('Operação observável indevidamente descartada.')
            if o['preco_entrada']!=float(minutos[e,0]) or o['preco_saida']!=float(minutos[v,0]):
                raise ValueError('Preços publicados diferem dos minutos de execução.')
            fator=(o['preco_saida']/o['preco_entrada'])*((1-slippage)/(1+slippage))*((1-taxa)/(1+taxa))
            novo=capital*fator
            proximo(o['capital_saida'],novo)
            proximo(o['retorno_liquido'],fator-1)
            quantidade=capital/(o['preco_entrada']*(1+slippage)*(1+taxa))
            proximo(o['quantidade'],quantidade)
            custo=capital-quantidade*o['preco_entrada']+quantidade*o['preco_saida']-novo
            proximo(o['custos'],custo)
            custo_total+=custo
            capital=novo
        proximo(estrategia['capital_final'],capital)
        proximo(estrategia['custos_observados'],custo_total)
        proximo(estrategia['retorno_liquido'],capital/p['capital']-1 if capital is not None else None)
        curva=registro['curva']
        tempos=[r['tempo_utc'] for r in curva]
        if tempos!=sorted(set(tempos)):
            raise ValueError('Curva publicada não é temporalmente única e ordenada.')
        proximo(curva[0]['capital'],p['capital'])
        proximo(curva[-1]['capital'],capital)
        ordens_conferidas+=len(ordens)
    recibo={'status':'aprovado','utc':agora(),'fase':fase,'execucao':ponteiro['id'],'ajustes':len(linhas),'candidatos_arima':candidatos,
            'cenarios_financeiros':len(a['financeiro']),'ordens_conferidas':ordens_conferidas,'publicacao_sha256':sha256(destino/'publicacao.json'),
            'auditor_sha256':sha256(Path(__file__)),'escopo':'Hashes do dataset e previsões, MSE independente, médias/contrastes, decisões causais, preços/horários de execução, contabilidade e cronologia da curva. Não substitui auditoria dos checkpoints nem certifica execução financeira real.'}
    salvar_json(destino/'auditoria_publicacao.json',recibo)
    print(recibo,flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--fase',choices=['desenvolvimento','avaliacao'],required=True)
    auditar(parser.parse_args().fase)
