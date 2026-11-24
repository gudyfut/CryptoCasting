"""Publicação nova: pares do mesmo bloco, sem reaproveitar pesos do futuro."""
import contextlib
import math
import os
import traceback
from uuid import uuid4
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256
from treinamento.preservacao import conferir, publicar as selar
from treinamento.avaliar import avaliar
from avaliacao.publicacao import conferir_previsoes
from analises.agregacao import metricas_preco
from analises.metricas import analisar
from backtest_carteira.simulador import simular, COLUNAS
from backtest_carteira.auditoria import conferir as conferir_carteira
from backtest_carteira.mercado import carregar as carregar_minutos
from .estatisticas import contraste
from .dados import Verificador


def janela_operacional(q, fim):
    # Corte exclusivamente pelo calendário conhecido; nunca pelo alvo observado.
    t=pd.DatetimeIndex(q.origem_utc);fim=pd.Timestamp(fim)
    return q.loc[t+pd.Timedelta(hours=24)<fim,COLUNAS].copy()


def grade_operacoes(c):
    for b in c['blocos']:
        for perda in c['variantes']:
            for seed in c['seeds']:
                for politica in c['politicas']:
                    for custo in c['cenarios']:yield b,perda,seed,politica,custo
        for politica in ('comprar_manter','caixa'):
            for custo in c['cenarios']:yield b,'benchmark',None,politica,custo


def auditar_ajuste(t,f,x,cfg,controle=False):
    import torch
    conferir(t);r=ler_json(t/'resultado.json');sel=ler_json(t/'selecao.json')
    assert sha256(t/sel['arquivo'])==sel['sha256'] and r['recarga_exata'] and r['parametros']==20257
    p=torch.load(t/sel['arquivo'],map_location='cpu',weights_only=True);v=p['vinculo']
    assert v['execucao']==f['id'] and v['identidade_consumo']==x.especificacao.identidade
    assert v['configuracao']==cfg and v['controle']==controle
    w=p['modelo']['pesos'];assert sum(q.numel() for q in w.values())==20257 and list(w['projecao.weight'].shape)==[32,5]
    estados=[q for k,q in w.items() if k.endswith('A_log')]
    assert len(estados)==2 and all(list(q.shape)==[64,16] for q in estados)
    es=ler_json(t/'epocas.json');melhor=min(es,key=lambda e:(e['mse_validacao'],e['epoca']))
    assert melhor['epoca']==sel['epoca']==r['epoca_selecionada']
    assert melhor['mse_validacao']==sel['mse_validacao']==r['metricas']['validacao']['mse']
    best=float('inf');parada=0
    for i,e in enumerate(es):
        if e['mse_validacao']<best:best=e['mse_validacao'];parada=0
        else:parada+=1
        if i<len(es)-1:assert parada<10
        if cfg['variante']=='huber':
            assert e['taxa_aprendizado']==.0002 and 'perda_treino_padronizada' in e
            assert r['perda']==cfg['perda']
        else:assert 'mse_treino_padronizado' in e and 'perda_treino_padronizada' not in e
    assert len(es)<=100
    if len(es)<100:assert parada==10
    assert cfg['treino']['taxa_aprendizado']==.0002
    return {'epoca':sel['epoca'],'epocas_executadas':len(es),'parametros':20257,'recarga_exata':True,
        'selecao_mse_conferida':True,'perda':cfg['perda'],'taxa_constante_por_fonte_e_configuracao':True}


def media_metricas(rs):
    campos=('mse','rmse','mae','vies','acuracia_direcional','acerto_balanceado_direcional','habilidade_mse')
    d={k:float(np.mean([r[k] for r in rs])) for k in campos}
    d['n_origens_por_seed']=rs[0]['n'];d['n_seeds']=len(rs)
    d['mse_desvio_seeds']=float(np.std([r['mse'] for r in rs],ddof=1)) if len(rs)>1 else None
    return d


def publicar(p,f,consumos):
    c=f['contrato']['configuracao'];dest=p/'publicacoes'/f'tentativa_{len(list((p/"publicacoes").glob("tentativa_*")))+1:03d}';dest.mkdir(parents=True)
    resultados={};previsoes={};auditoria={};diags={};naives={};medias={};perdas={b:{} for b in ('validacao','teste')}
    for b,x in consumos.items():
        partes=x._conjunto.partes;cfg=f['contrato']['receitas'][b]['mse']
        base=p/'baselines'/b/'naive';ant=sorted(base.glob('tentativa_*'));prontas=[q for q in ant if (q/'conclusao.json').exists()]
        if len(prontas)>1:raise ValueError('Baselines concluídas ambíguas.')
        if prontas:t=prontas[0];conferir(t)
        else:
            t=base/f'tentativa_{len(ant)+1:03d}';t.mkdir(parents=True)
            avaliar(x,partes,'naive',cfg,t,{'execucao':f['id'],'bloco':b,'modelo':'naive'});selar(t)
        naives[b]=ler_json(t/'resultado.json')
        for parte in ('validacao','teste','operacional'):
            q=pd.read_parquet(t/f'previsoes_{parte}.parquet');conferir_previsoes(q,partes[parte],naives[b]['metricas'].get(parte));previsoes[b,'naive',None,parte]=q
        medias[b]={parte:{} for parte in ('validacao','teste')}
        for perda in c['variantes']:
            cfg=f['contrato']['receitas'][b][perda]
            for seed in c['seeds']:
                chave=f'{b}_{perda}_{seed}';ts=list((p/'celulas'/chave).glob('tentativa_*/conclusao.json'));assert len(ts)==1;t=ts[0].parent
                auditoria[chave]=auditar_ajuste(t,f,x,cfg);r=ler_json(t/'resultado.json')
                resultados[chave]=dict(r,tentativa_origem=t.relative_to(RAIZ).as_posix());diags[chave]={}
                for parte in ('validacao','teste','operacional'):
                    q=pd.read_parquet(t/f'previsoes_{parte}.parquet');conferir_previsoes(q,partes[parte],r['metricas'].get(parte));previsoes[b,perda,seed,parte]=q
                    if parte!='operacional':
                        e=[float(v)-float(y) for v,y in zip(q.previsao,q.alvo)]
                        assert math.isclose(math.fsum(a*a for a in e)/len(e),r['metricas'][parte]['mse'],rel_tol=1e-12)
                        diags[chave][parte]=analisar(q,previsoes[b,perda,seed,'validacao'],previsoes[b,'naive',None,parte])
                        resultados[chave].setdefault('metricas_preco',{})[parte]=metricas_preco(q)
            for parte in ('validacao','teste'):
                medias[b][parte][perda]=media_metricas([resultados[f'{b}_{perda}_{s}']['metricas'][parte] for s in c['seeds']])
                perdas[parte].setdefault(b,{'origens':partes[parte].origem_utc})[perda]=np.stack([
                    (previsoes[b,perda,s,parte].previsao.to_numpy()-previsoes[b,perda,s,parte].alvo.to_numpy())**2 for s in c['seeds']])
        for parte in ('validacao','teste'):medias[b][parte]['naive']=naives[b]['metricas'][parte]
    assert len(resultados)==c['ajustes_principais']
    globais={};contrastes={}
    for parte in ('validacao','teste'):
        globais[parte]={}
        for perda in c['variantes']:
            campos=('mse','rmse','mae','vies','acuracia_direcional','acerto_balanceado_direcional')
            g={k:float(np.mean([medias[b][parte][perda][k] for b in c['blocos']])) for k in campos}
            base=float(np.mean([naives[b]['metricas'][parte]['mse'] for b in c['blocos']]))
            g.update(mse_naive=base,habilidade_mse=1-g['mse']/base,blocos=len(c['blocos']),seeds_por_bloco=len(c['seeds']))
            globais[parte][perda]=g
        contrastes[parte]=contraste(perdas[parte],c['bootstrap'])
    v=contrastes['teste'];primario={'media_mse_menor':globais['teste']['huber']['mse']<globais['teste']['mse']['mse'],
        'ic95_seeds_tempo_14_inteiramente_favoravel':v['ic95_seeds_e_tempo'][str(c['bootstrap']['principal'])][1]<0,
        'promocao_automatica':False,'natureza':'Avaliação retrospectiva ampliada; não substitui o fechamento da exploração anterior.'}
    # Controles reais não entram nas médias, mas seus checkpoints também são auditados.
    for perda in c['variantes']:
        b=c['controle_bloco'];key=f'{b}_{perda}_{c["controle_seed"]}'
        ts=list((p/'controles'/key).glob('tentativa_*/conclusao.json'));assert len(ts)==1
        auditoria['controle_'+key]=auditar_ajuste(ts[0].parent,f,consumos[b],f['contrato']['receitas'][b][perda],True)
    cb=f['contrato']['carteira'];minutos,primeiro=carregar_minutos(RAIZ/cb['pasta'],cb['contrato']);opcfg=cb['contrato']['configuracao']
    carteiras={}
    for b,perda,seed,politica,custo in grade_operacoes(c):
        q=previsoes[b,'naive',None,'operacional'] if perda=='benchmark' else previsoes[b,perda,seed,'operacional']
        q=janela_operacional(q,c['blocos'][b]['teste'][1])
        r,o,cur,d,si=simular(q,minutos,primeiro,opcfg,politica,custo)
        ver=conferir_carteira(q,minutos,primeiro,opcfg,politica,custo,r,o,d)
        key=f'{b}/{perda}/{seed if seed is not None else "benchmark"}/{politica}/{custo}';dd=dest/'carteiras'/key;dd.mkdir(parents=True)
        for n,valor in [('resumo',r),('ordens',o),('sinais',si),('verificacao',ver)]:salvar_json(dd/f'{n}.json',valor)
        cur.to_parquet(dd/'curva.parquet',index=False);d.to_parquet(dd/'diarios.parquet',index=False);carteiras[key]=r
        salvar_json(p/'publicacao_progresso.json',{'fase':'carteiras','concluidas':len(carteiras),'total':c['simulacoes_total'],'utc':agora()})
    assert len(carteiras)==c['simulacoes_total']
    opmedias={}
    for b in c['blocos']:
        opmedias[b]={}
        for perda in c['variantes']:
            for pol in c['politicas']:
                for custo in c['cenarios']:
                    rs=[carteiras[f'{b}/{perda}/{s}/{pol}/{custo}'] for s in c['seeds']]
                    m={k:float(np.mean([r[k] for r in rs])) for k in ('retorno_liquido','capital_final','drawdown_minuto_close','exposicao_media','comissoes_usdt','slippage_usdt','ordens_executadas')}
                    m.update(seeds_lucrativas=sum(r['retorno_liquido']>0 for r in rs),retorno_desvio_seeds=float(np.std([r['retorno_liquido'] for r in rs],ddof=1)))
                    opmedias[b][f'{perda}/{pol}/{custo}']=m
    r={'utc':agora(),'execucao':f['id'],'ajustes_principais':len(resultados),'controles_reais':2,'naives':naives,
        'por_ajuste':resultados,'medias_por_bloco':medias,'medias_globais':globais,'contrastes':contrastes,'criterio_primario':primario,
        'auditoria_checkpoint':auditoria,'diagnosticos':diags,'carteiras':carteiras,'medias_operacionais_por_bloco':opmedias,
        'limites':['2024/2025 já consultados; seleção retrospectiva, sem certeza ou holdout novo.',
            'Pesos iguais entre blocos, médias de oito modelos individuais; não ensemble.',
            'Carteiras independentes por bloco, reset10.000USDT; não somar retornos como retorno acumulado.',
            'Última sessão completa excluída pelo calendário em cada bloco; saída terminal do motor mais1minuto.',
            'Sem novos LSTM/ARIMA; referências antigas não são reutilizadas com pesos do futuro.',
            '66 ajustes reais (64 principais+2 controles),408simulações e4Naive; nenhuma busca extra.']}
    salvar_json(dest/'resultados.json',r)
    salvar_json(dest/'manifesto.json',{'arquivos':{q.relative_to(dest).as_posix():sha256(q) for q in dest.rglob('*') if q.is_file()}})
    salvar_json(p/'publicacao.json',{'pasta':dest.relative_to(p).as_posix(),'manifesto_sha256':sha256(dest/'manifesto.json')})
    return dest,r


def relatar(r):
    ls=['# Mamba16: MSE versus Huber em quatro blocos e oito seeds','',
        f'Execução `{r["execucao"]}`.64ajustes principais+2controles reais;4Naive e408simulações. [Protocolo](protocolo_huber_blocos.md), [estado](../registros/huber_blocos/estado.json).','',
        '2024/2025 já conhecidos: walk-forward retrospectivo com seleção informada por períodos. Cada bloco tem treino/validação anteriores ao teste, pesos e scalers novos. Mais seeds não garantem certeza. Não misturar estas médias com a exploração anterior de divisão única.','',
        '## Previsão: média das oito seeds em cada bloco','',
        '| Bloco | Parte | MSE referência | MSE Huber | Mudança relativa |','|---|---|---:|---:|---:|']
    for b,partes in r['medias_por_bloco'].items():
        for parte,m in partes.items():
            a,z=m['huber']['mse'],m['mse']['mse'];ls.append(f'| {b} | {parte} | {z:.10f} | {a:.10f} | {100*(a/z-1):+.3f}% |')
    ls+=['','## Agregação predefinida','', 'Peso igual entre quatro blocos e oito seeds dentro de cada bloco. RMSE/MAE são médias de métricas individuais, não erro de ensemble.','',
        '| Parte | Variante | MSE | RMSE×100 | MAE×100 | Habilidade Naive |','|---|---|---:|---:|---:|---:|']
    for parte,gs in r['medias_globais'].items():
        for nome,m in gs.items():ls.append(f'| {parte} | {nome} | {m["mse"]:.10f} | {100*m["rmse"]:.4f} | {100*m["mae"]:.4f} | {100*m["habilidade_mse"]:+.3f}% |')
    ct=r['contrastes']['teste'];ls+=['',f'Diferença MSE Huber−MSE: {ct["diferenca_mse_huber_menos_mse"]:.10g}; IC95% principal (seeds pareadas e blocos14dias): {ct["ic95_seeds_e_tempo"]["14"]}.',
        'Critério primário: '+str(r['criterio_primario'])+'. Sem promoção automática; inconclusivo não demonstra igualdade nem ausência universal de previsibilidade.','',
        '## Operação por bloco: custos base','',
        '| Bloco | Política | Retorno referência | Retorno Huber | DD referência | DD Huber |','|---|---|---:|---:|---:|---:|']
    for b,gs in r['medias_operacionais_por_bloco'].items():
        for pol in ('smart','diaria24'):
            a,z=gs[f'huber/{pol}/base'],gs[f'mse/{pol}/base'];ls.append(f'| {b} | {pol} | {100*z["retorno_liquido"]:+.2f}% | {100*a["retorno_liquido"]:+.2f}% | {100*z["drawdown_minuto_close"]:.2f}% | {100*a["drawdown_minuto_close"]:.2f}% |')
    ls+=['','Os cenários ideal/agravado, benchmarks, exposição, taxas, carteiras e diários estão na publicação estruturada. Capital inicial10.000USDT em cada carteira/bloco, long/caixa, sem futuros ou stop. Carteiras não formam um histórico contínuo de dois anos. A comparação usa o mesmo motor, calendário e custos dentro de cada bloco.','',
        'Seleção por MSE de validação, fontes, checkpoints/recarga, reprodução real, métricas e lançamentos conferidos. Scalers são de cada treino. Os controles não entram nas médias. As limitações dos períodos escolhidos, reamostragem e seleção adaptativa permanecem. Não alterar configurações ou simulação para obter lucro.']
    q=RAIZ/'docs/resultados_huber_blocos.md'
    if q.exists():raise FileExistsError('Relatório existente; preservar.')
    q.write_text('\n'.join(ls)+'\n',encoding='utf-8');return q.relative_to(RAIZ).as_posix()


@contextlib.contextmanager
def trava_publicacao(p):
    import fcntl
    with (p/'publicacao.lock').open('a+b') as q:
        fcntl.flock(q,fcntl.LOCK_EX|fcntl.LOCK_NB)
        salvar_json(p/'processo_publicacao.json',{'pid':os.getpid(),'ativo':True,'utc':agora()})
        try:yield
        finally:
            salvar_json(p/'processo_publicacao.json',{'pid':os.getpid(),'ativo':False,'fim_utc':agora()});fcntl.flock(q,fcntl.LOCK_UN)


def posprocessar():
    from .ciclo import REG,conferir_execucao
    if (REG/'fechamento.json').exists():raise ValueError('Fechamento existente; não repetir.')
    p,f,consumos=conferir_execucao()
    assert ler_json(p/'progresso.json')['status']=='concluido' and not ler_json(p/'processo.json')['ativo']
    with trava_publicacao(p):
        if (REG/'fechamento.json').exists():raise ValueError('Fechamento existente.')
        try:
            dest,r=publicar(p,f,consumos);v=Verificador();v.arquivos_em(dest,ler_json(dest/'manifesto.json')['arquivos'])
            guard=ler_json(REG/'preservacao_antes.json')['arquivos'];v.arquivos_em(RAIZ,guard)
            rel=relatar(r);fim={'situacao':'concluido_conferido','utc':agora(),'execucao':ler_json(REG/'execucao.json'),
                'principais':64,'controles_reais':2,'simulacoes':408,'preservados':len(guard),'publicacao':dest.relative_to(RAIZ).as_posix(),
                'manifesto_sha256':sha256(dest/'manifesto.json'),'relatorio':rel,'criterio_primario':r['criterio_primario'],
                'proxima_acao':'Interpretar e redigir; sem busca, promoção ou treino automático.'}
            salvar_json(REG/'fechamento.json',fim);salvar_json(REG/'estado.json',fim)
            cat=ler_json(RAIZ/'registros/catalogo_estudos.json')
            for row in cat.get('rodadas_ohlcv',[]):
                if row.get('execucao')==f['id']:row.update(situacao='concluido_conferido',ajustes_neurais_novos_concluidos=66,publicacao=fim['publicacao'],relatorio=rel)
            cat['etapa_atual']['situacao']='huber_blocos_concluido_conferido';cat['etapa_atual']['huber_blocos']=fim;salvar_json(RAIZ/'registros/catalogo_estudos.json',cat)
            doc=RAIZ/'docs/andamento.md';t=doc.read_text(encoding='utf-8');nota=f'## Huber em blocos concluído e conferido\n\nExecução `{f["id"]}`:64ajustes principais e2controles reais,4Naive e408simulações. [Relatório](resultados_huber_blocos.md), [estado](../registros/huber_blocos/estado.json). Sem nova rodada automática;2024/2025 retrospectivos.\n\n'
            doc.write_text(t.replace('# Andamento do CryptoCasting\n','# Andamento do CryptoCasting\n\n'+nota,1),encoding='utf-8');return fim
        except BaseException:
            salvar_json(REG/'incidentes'/f'{uuid4().hex}.json',{'utc':agora(),'fase':'publicacao_sem_treino','erro':traceback.format_exc()});raise
