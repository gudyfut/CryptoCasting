"""Publicação separada do huber: seis novas séries e53herdadas."""
import math
import traceback
from uuid import uuid4
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256, conferir_arquivos
from treinamento.preservacao import conferir
from avaliacao.publicacao import conferir_previsoes, contraste_temporal
from avaliacao.mercado import carregar_minutos
from avaliacao.spot import simular as spot_r0
from analises.agregacao import resumir, metricas_preco
from analises.metricas import analisar
from backtest_carteira.simulador import simular, COLUNAS
from backtest_carteira.auditoria import conferir as conferir_carteira
from backtest_carteira.mercado import carregar


def auditar_checkpoint(t,f,partes):
    import torch
    from .perda import POLITICA
    conferir(t);r=ler_json(t/'resultado.json');sel=ler_json(t/'selecao.json')
    pacote=torch.load(t/sel['arquivo'],map_location='cpu',weights_only=True)
    assert r['recarga_exata'] and r['parametros']==20257
    assert pacote['vinculo']['execucao']==f['id'] and pacote['vinculo']['configuracao']==f['contrato']['configuracao']
    pesos=pacote['modelo']['pesos'];assert pacote['modelo']['familia']=='mamba'
    assert list(pesos['projecao.weight'].shape)==[32,5] and sum(v.numel() for v in pesos.values())==20257
    estados=[v for k,v in pesos.items() if k.endswith('A_log')];assert len(estados)==2 and all(list(v.shape)==[64,16] for v in estados)
    epocas=ler_json(t/'epocas.json');melhor=min(epocas,key=lambda e:(e['mse_validacao'],e['epoca']))
    assert melhor['epoca']==sel['epoca']==r['epoca_selecionada']
    assert melhor['mse_validacao']==sel['mse_validacao']==r['metricas']['validacao']['mse']
    assert r['perda']==POLITICA==f['contrato']['configuracao']['perda']
    # Reconstrução da seleção/parada por MSE, sem usar a perda Huber de treino.
    best=float('inf');parada=0
    for e in epocas:
        assert e['taxa_aprendizado']==.0002
        assert math.isfinite(e['perda_treino_padronizada']) and e['perda_treino_padronizada']>=0
        assert 'mse_treino_padronizado' not in e
        if e['mse_validacao']<best:best=e['mse_validacao'];parada=0
        else:parada+=1
        if e is not epocas[-1]:assert parada<10
    assert len(epocas)<=100
    if len(epocas)<100:assert parada==10
    conf={b:conferir_previsoes(pd.read_parquet(t/f'previsoes_{b}.parquet'),partes[b],r['metricas'].get(b))
          for b in ('validacao','teste','operacional')}
    return {'epoca':sel['epoca'],'recarga_exata':True,'conferencia':conf,'taxa_constante_conferida':True,
            'selecao_mse_reconstruida':True,'perda':POLITICA}


def publicar(p,f,partes,novas,refs,pub_ant):
    cfg=f['contrato']['configuracao'];ss=cfg['seeds']
    dest=p/'publicacoes'/f'tentativa_{len(list((p/"publicacoes").glob("tentativa_*")))+1:03d}';dest.mkdir(parents=True)
    anteriores=ler_json(pub_ant/'resultados.json');res={k:dict(anteriores['por_ajuste'][k],origem_ajuste='herdado') for k in refs}
    prev={};auditoria={};diags={};conf={}
    for k,t in refs.items():
        for b in ('validacao','teste','operacional'):
            q=pd.read_parquet(t/f'previsoes_{b}.parquet');prev[k,b]=q
            conferir_previsoes(q,partes[b],res[k]['metricas'].get(b))
    minutos,primeiro=carregar_minutos(RAIZ/cfg['mercado_pasta'],cfg['par'])
    for s,t in novas.items():
        k=f'mamba16_huber_{s}';rr=ler_json(t/'resultado.json')
        auditoria[k]=auditar_checkpoint(t,f,partes);conf[k]={};precos={};diags[k]={}
        for b in ('validacao','teste','operacional'):
            q=pd.read_parquet(t/f'previsoes_{b}.parquet');prev[k,b]=q
            conf[k][b]=conferir_previsoes(q,partes[b],rr['metricas'].get(b))
            if b!='operacional':
                precos[b]=metricas_preco(q);diags[k][b]=analisar(q,prev[k,'validacao'],prev['naive',b])
                erro=[float(a)-float(y) for a,y in zip(q.previsao,q.alvo)]
                mse=math.fsum(e*e for e in erro)/len(erro)
                if not math.isclose(mse,rr['metricas'][b]['mse'],rel_tol=1e-12):raise ValueError('MSE independente divergente.')
        spot={}
        for perfil,agr in [('base',False),('agravado',True)]:
            rr0,ops,curva=spot_r0(prev[k,'operacional'],minutos,primeiro,cfg['divisao']['teste'][1],cfg['operacao'],agravado=agr)
            spot[perfil]=rr0;salvar_json(dest/k/f'operacoes_{perfil}.json',ops);salvar_json(dest/k/f'curva_{perfil}.json',curva)
        bruto=prev[k,'operacional'].copy();taxa,slip=cfg['operacao']['taxa'],cfg['operacao']['slippage']
        limiar=np.log((1+slip)*(1+taxa)/((1-slip)*(1-taxa)));bruto['previsao']=(bruto.previsao>limiar).astype(float)
        spot['bruto_mesmos_sinais']=spot_r0(bruto,minutos,primeiro,cfg['divisao']['teste'][1],dict(cfg['operacao'],taxa=0.,slippage=0.))[0]
        res[k]={'metricas':rr['metricas'],'metricas_preco':precos,'spot':spot,'tentativa_origem':t.relative_to(RAIZ).as_posix(),'origem_ajuste':'novo'}
    assert len(res)==59 and len(novas)==6
    grupos={'huber_seis':[f'mamba16_huber_{s}' for s in ss],
            'mamba16_seis':[f'estado16_{s}' for s in ss],
            'huber_tres':[f'mamba16_huber_{s}' for s in ss[:3]],
            'mamba16_tres':[f'estado16_{s}' for s in ss[:3]],
            'lstm_tres':[f'lstm_{s}' for s in ss[:3]],'naive':['naive'],'arima':['arima']}
    medias={};contrastes={}
    for b in ('validacao','teste'):
        medias[b]={};perdas={}
        for nome,ks in grupos.items():
            medias[b][nome]=resumir(ks,res,prev,b)
            perdas[nome]=np.mean([(prev[k,b].previsao.to_numpy()-prev[k,b].alvo.to_numpy())**2 for k in ks],axis=0)
        contrastes[b]={f'{a}_menos_{z}':contraste_temporal(partes[b].origem_utc,perdas[a],perdas[z],cfg['bootstrap'])
                       for a,z in [('huber_seis','mamba16_seis'),('huber_seis','naive'),('huber_tres','lstm_tres')]}
    v=contrastes['validacao']['huber_seis_menos_mamba16_seis']
    principal={'media_mse_menor':medias['validacao']['huber_seis']['metricas']['mse']<medias['validacao']['mamba16_seis']['metricas']['mse'],
               'ic95_principal_inteiramente_favoravel':v['ic95']['14'][1]<0,'promocao_automatica':False}
    # Mesmas regras e preços do backtest encerrado; somente novas previsões.
    bp=ler_json(RAIZ/'registros/backtest_carteira/execucao_atual.json');pb=RAIZ/bp['pasta'];cb=ler_json(pb/'congelamento.json')['contrato']
    minutos_b,primeiro_b=carregar(pb,cb);carteiras={};constantes={}
    for s in ss:
        k=f'mamba16_huber_{s}'
        q=prev[k,'validacao'];constantes[k]=float(q.loc[pd.DatetimeIndex(q.origem_utc).hour==0].previsao.mean())
        for b in ('validacao','teste'):
            for custo in ('ideal','base','agravado'):
                for pol in (['smart','smart_constante'] if b=='teste' else ['smart']):
                    q=prev[k,b][COLUNAS].copy()
                    if pol=='smart_constante':q['previsao']=constantes[k]
                    rr,o,cur,d,si=simular(q,minutos_b,primeiro_b,cb['configuracao'],'smart',custo)
                    ver=conferir_carteira(q,minutos_b,primeiro_b,cb['configuracao'],'smart',custo,rr,o,d)
                    chave=f'{b}/{custo}/{pol}/{k}';dd=dest/'carteira'/chave;dd.mkdir(parents=True)
                    salvar_json(dd/'resumo.json',rr);salvar_json(dd/'ordens.json',o);salvar_json(dd/'sinais.json',si);salvar_json(dd/'verificacao.json',ver)
                    cur.to_parquet(dd/'curva.parquet',index=False);d.to_parquet(dd/'diarios.parquet',index=False)
                    carteiras[chave]=rr
    assert len(carteiras)==54
    r={'utc':agora(),'execucao':f['id'],'novos':6,'herdados':53,'por_ajuste':res,'medias':medias,
       'contrastes':contrastes,'criterio_primario':principal,'diagnosticos':diags,'auditoria_checkpoint':auditoria,
       'carteiras':carteiras,'constantes_validacao':constantes,
       'referencia_carteira':{'arquivo':(pb/'resultados/comparacao.json').relative_to(RAIZ).as_posix(),'sha256':sha256(pb/'resultados/comparacao.json')},
       'limites':['Retrospectivo:2024 seleção/2025 previamente conhecido; não holdout novo ou walk-forward.',
                  'Troca somente da perda supervisionada; Huber não estima necessariamente a média condicional. Seleção por MSE mantida.',
                  'Médias de seeds individuais, não ensemble; não escolher por retorno Spot.',
                  '54simulações Smart secundárias, sem regra/política nova; custos/filtros são cenários.']}
    salvar_json(dest/'resultados.json',r);salvar_json(dest/'conferencia_metricas.json',conf)
    salvar_json(dest/'manifesto.json',{'arquivos':{q.relative_to(dest).as_posix():sha256(q) for q in dest.rglob('*') if q.is_file()}})
    salvar_json(p/'publicacao.json',{'pasta':dest.relative_to(p).as_posix(),'manifesto_sha256':sha256(dest/'manifesto.json')})
    return dest,r


def relatar(r):
    linhas=['# Mamba16: MSE versus perda Huber','',
        f'Execução `{r["execucao"]}`: seis novos ajustes,53referências herdadas e54carteiras Smart secundárias. [Protocolo](protocolo_perda_huber.md), [estado](../registros/perda_huber/estado.json).',
        '', '## Comparação preditiva','',
        'Médias aritméticas de métricas de modelos individuais, não ensemble. A referência é Mamba16/AdamW/MSE com taxa constante0,0002. Dados, arquitetura, otimizador, taxa e critério de parada iguais; somente a perda de treinamento mudou para 2×Huber(delta1 padronizado). Seleção de checkpoint e primário continuam MSE global de validação em retorno real.',
        '', '| Parte | Modelo | Seeds | MSE | RMSE×100 | MAE×100 | Habilidade Naive |','|---|---|---:|---:|---:|---:|---:|']
    for b in ('validacao','teste'):
        for nome,g in r['medias'][b].items():
            m=g['metricas'];linhas.append(f'| {b} | {nome} | {g["n_seeds"]} | {m["mse"]:.10f} | {m["rmse"]*100:.4f} | {m["mae"]*100:.4f} | {m["habilidade_mse"]*100:+.3f}% |')
    linhas+=['','## Critério primário e incerteza','','| Parte | Diferença MSE huber−constante | IC95%14dias |','|---|---:|---|']
    for b in ('validacao','teste'):
        v=r['contrastes'][b]['huber_seis_menos_mamba16_seis'];linhas.append(f'| {b} | {v["diferenca_mse_a_menos_b"]:.10g} | {v["ic95"]["14"]} |')
    favoravel=r['criterio_primario']['media_mse_menor'] and r['criterio_primario']['ic95_principal_inteiramente_favoravel']
    linhas+=['','O critério primário '+('foi atendido neste contraste retrospectivo.' if favoravel else 'não foi atendido: não há evidência suficiente pelo critério fixado para substituir a referência.'),
        'Não selecionar variante/seed/época pelo teste ou pelo lucro. A taxa permaneceu constante. Huber muda a estimativa favorecida pela perda e a dinâmica de gradientes; melhorar MAE ou lucro e piorar MSE é um compromisso, não vitória no critério principal.',
        '', '## Todas as seeds e diagnóstico diário','',
        '| Seed | MSE validação | MSE teste | P95 erro×100 | Vitórias vs Naive | Spearman00UTC | Smart base teste |','|---|---:|---:|---:|---:|---:|---:|']
    for s in (17,42,2026,7,123,31415):
        k=f'mamba16_huber_{s}';d=r['diagnosticos'][k]['teste']['origens00utc'];m=r['por_ajuste'][k]['metricas'];op=r['carteiras'][f'teste/base/smart/{k}'];rho='indefinida' if d['spearman'] is None else f'{d["spearman"]:.4f}'
        linhas.append(f'| {s} | {m["validacao"]["mse"]:.10f} | {m["teste"]["mse"]:.10f} | {d["p95_erro_absoluto"]*100:.4f} | {d["vitorias_referencia"]*100:.2f}% | {rho} | {op["retorno_liquido"]*100:+.2f}% |')
    linhas+=['','## Carteira Smart: média de seis modelos','','| Parte | Custos | Política | Retorno | Queda máxima média | Exposição |','|---|---|---|---:|---:|']
    for b in ('validacao','teste'):
        for custo in ('ideal','base','agravado'):
            for pol in (['smart','smart_constante'] if b=='teste' else ['smart']):
                vs=[r['carteiras'][f'{b}/{custo}/{pol}/mamba16_huber_{s}'] for s in (17,42,2026,7,123,31415)]
                vals=[float(np.mean([v[c] for v in vs]))*100 for c in ('retorno_liquido','drawdown_minuto_close','exposicao_media')]
                linhas.append(f'| {b} | {custo} | {pol} | {vals[0]:+.2f}% | {vals[1]:.2f}% | {vals[2]:.2f}% |')
    linhas+=['','Comparar com o [backtest anterior](resultados_backtest_carteira.md), no mesmo calendário e regras. Smart2% não é stop. Os resultados SpotR0, com contabilidade histórica própria, estão na publicação estruturada e não substituem as carteiras retidas.',
        '', '## Evidências e limitações','',
        'Taxa constante, contrato da perda e seleção/parada por MSE foram conferidos, assim como métricas e lançamentos das54carteiras. Recarga exata e capacidade20.257 verificadas; nenhum resultado anterior foi sobrescrito. MSE de todas as origens horárias não é o MSE do subconjunto00UTC. Vitórias contra Naive são de erro absoluto, não acerto direcional. Os diagnósticos descritivos não alteram o primário: [diagnóstico das previsões anteriores](diagnostico_previsoes.md). Resultados por trimestre, faixas causais de previsão, correlações e erros estão na publicação.',
        '', '2024 participou da seleção de checkpoints;2025 já foi consultado. Estudo exploratório retrospectivo, sem novo holdout ou walk-forward. Mais seeds não eliminam seleção adaptativa. Sem garantia de lucro/fills reais/backup externo; nenhuma promoção ou hipótese seguinte é automática. [Registros e publicação](../registros/perda_huber/estado.json).']
    p=RAIZ/'docs/resultados_perda_huber.md'
    if p.exists():raise FileExistsError('Relatório já existe; preservar.')
    p.write_text('\n'.join(linhas)+'\n',encoding='utf-8');return p.relative_to(RAIZ).as_posix()


def posprocessar():
    from .ciclo import REG,SEEDS,conferir_execucao
    if (REG/'fechamento.json').exists():raise ValueError('Encerrado; não repetir pós-processamento.')
    p,f,consumo,partes,refs=conferir_execucao()
    assert ler_json(p/'progresso.json')['status']=='concluido' and not ler_json(p/'processo.json')['ativo']
    assert set(ler_json(p/'progresso.json')['concluidos'])==set(SEEDS)
    try:
        novas={}
        for s in SEEDS:
            ts=[t for t in (p/'celulas'/f'mamba16_huber_{s}').glob('tentativa_*') if (t/'conclusao.json').exists()]
            assert len(ts)==1;conferir(ts[0]);novas[s]=ts[0]
        pub,r=publicar(p,f,partes,novas,refs,RAIZ/f['contrato']['publicacao_anterior'])
        conferir_arquivos(pub,ler_json(pub/'manifesto.json')['arquivos'])
        guard=ler_json(REG/'preservacao_antes.json')['arquivos'];conferir_arquivos(RAIZ,guard)
        rel=relatar(r)
        fim={'situacao':'concluido_conferido','utc':agora(),'execucao':ler_json(REG/'execucao.json'),
             'novos':6,'herdados':53,'simulacoes_smart':54,'preservados':len(guard),
             'publicacao':pub.relative_to(RAIZ).as_posix(),'manifesto_sha256':sha256(pub/'manifesto.json'),
             'relatorio':rel,'criterio_primario':r['criterio_primario'],'proxima_acao':'Interpretar; sem promoção ou novos treinos automáticos.'}
        salvar_json(REG/'fechamento.json',fim);salvar_json(REG/'estado.json',fim)
        cat=ler_json(RAIZ/'registros/catalogo_estudos.json')
        for row in cat.get('rodadas_ohlcv',[]):
            if row.get('execucao')==f['id']:row.update(situacao='concluido_conferido',ajustes_neurais_novos_concluidos=6,publicacao=fim['publicacao'],relatorio=rel)
        cat['etapa_atual']['situacao']='mamba16_perda_huber_concluido_conferido';cat['etapa_atual']['perda_huber']=fim
        salvar_json(RAIZ/'registros/catalogo_estudos.json',cat)
        doc=RAIZ/'docs/andamento.md';t=doc.read_text(encoding='utf-8-sig')
        nota=f'## Perda Huber Mamba16 concluída e conferida\n\nExecução `{f["id"]}`: seis ajustes e53referências herdadas,54carteiras Smart. Taxa constante, perda supervisionada, seleção por MSE, checkpoint/recarga, métricas, ordens e preservação conferidos. [Resultados](resultados_perda_huber.md), [estado](../registros/perda_huber/estado.json). Sem promoção automática ou novos treinos;2024/2025 retrospectivos.\n\n'
        doc.write_text(t.replace('# Andamento do CryptoCasting\n','# Andamento do CryptoCasting\n\n'+nota,1),encoding='utf-8')
        return fim
    except BaseException:
        salvar_json(REG/'incidentes'/f'{uuid4().hex}.json',{'utc':agora(),'fase':'posprocessamento_sem_treino','erro':traceback.format_exc()});raise

