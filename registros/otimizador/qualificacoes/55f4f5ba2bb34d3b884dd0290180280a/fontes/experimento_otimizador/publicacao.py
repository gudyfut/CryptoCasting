"""Comparação posterior, sem repetir treino: seis novas séries e59herdadas."""
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
from experimento_cryptomamba.publicacao import resumir, metricas_preco
from backtest_carteira.simulador import simular, COLUNAS
from backtest_carteira.auditoria import conferir as conferir_carteira
from backtest_carteira.mercado import carregar


def diagnostico(q):
    a=q.previsao.to_numpy(float);y=q.alvo.to_numpy(float)
    return {'n':len(a),'desvio_previsao':float(a.std()),'desvio_alvo':float(y.std()),
            'amplitude':float(a.max()-a.min()),'distintas':len(np.unique(a)),
            'correlacao':float(np.corrcoef(a,y)[0,1]) if len(np.unique(a))>1 and a.std()>0 and y.std()>0 else None}


def auditar_checkpoint(t,f,partes):
    import torch
    conferir(t);r=ler_json(t/'resultado.json');s=ler_json(t/'selecao.json')
    pacote=torch.load(t/s['arquivo'],map_location='cpu',weights_only=True)
    assert r['recarga_exata'] and r['parametros']==139317
    assert pacote['vinculo']['execucao']==f['id']
    assert pacote['modelo']['configuracao']==f['contrato']['configuracao']
    assert pacote['modelo']['configuracao']['otimizador']['nome']=='AdamW'
    assert list(pacote['modelo']['pesos']['adaptacao_temporal.weight'].shape)==[14,168]
    assert sum(v.numel() for v in pacote['modelo']['pesos'].values())==139317
    melhor=min(ler_json(t/'epocas.json'),key=lambda e:(e['mse_validacao'],e['epoca']))
    assert melhor['epoca']==s['epoca']==r['epoca_selecionada']
    assert melhor['mse_validacao']==s['mse_validacao']==r['metricas']['validacao']['mse']
    grupos=ler_json(t/'grupos_otimizador.json')
    marcados=[v for v in grupos if v['nome'].endswith(('A_log','.D'))]
    assert len(marcados)==24 and all(g['weight_decay']==0. for g in marcados)
    conf={b:conferir_previsoes(pd.read_parquet(t/f'previsoes_{b}.parquet'),partes[b],r['metricas'].get(b)) for b in partes}
    return {'epoca':s['epoca'],'recarga_exata':True,'conferencia':conf,
            'norma_pesos':math.sqrt(sum(float((v.double()**2).sum()) for v in pacote['modelo']['pesos'].values()))}


def publicar(p,f,partes,novas,refs,pub_ant):
    cfg=f['contrato']['configuracao'];ss=cfg['seeds']
    dest=p/'publicacoes'/f'tentativa_{len(list((p/"publicacoes").glob("tentativa_*")))+1:03d}';dest.mkdir(parents=True)
    anteriores=ler_json(pub_ant/'resultados.json');res={k:dict(v,origem_ajuste='herdado') for k,v in anteriores['por_ajuste'].items()}
    prev={};auditoria={};diags={};conf={}
    for k,t in refs.items():
        for b in partes:
            q=pd.read_parquet(t/f'previsoes_{b}.parquet');prev[k,b]=q
            conferir_previsoes(q,partes[b],res[k]['metricas'].get(b))
    minutos,primeiro=carregar_minutos(RAIZ/cfg['mercado_pasta'],cfg['par'])
    for s,t in novas.items():
        k=f'cryptomamba_adamw_{s}';rr=ler_json(t/'resultado.json')
        auditoria[k]=auditar_checkpoint(t,f,partes);conf[k]={};precos={};diags[k]={}
        for b in partes:
            q=pd.read_parquet(t/f'previsoes_{b}.parquet');prev[k,b]=q
            conf[k][b]=conferir_previsoes(q,partes[b],rr['metricas'].get(b))
            if b!='operacional':
                precos[b]=metricas_preco(q);diags[k][b]=diagnostico(q)
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
    assert len(res)==65 and len(novas)==6
    grupos={'adamw_seis':[f'cryptomamba_adamw_{s}' for s in ss],
            'adam_seis':[f'cryptomamba_{s}' for s in ss],
            'mamba16_seis':[f'estado16_{s}' for s in ss],
            'adamw_tres':[f'cryptomamba_adamw_{s}' for s in ss[:3]],
            'adam_tres':[f'cryptomamba_{s}' for s in ss[:3]],
            'mamba16_tres':[f'estado16_{s}' for s in ss[:3]],
            'lstm_tres':[f'lstm_{s}' for s in ss[:3]],'naive':['naive'],'arima':['arima']}
    medias={};contrastes={}
    for b in ('validacao','teste'):
        medias[b]={};perdas={}
        for nome,ks in grupos.items():
            medias[b][nome]=resumir(ks,res,prev,b)
            perdas[nome]=np.mean([(prev[k,b].previsao.to_numpy()-prev[k,b].alvo.to_numpy())**2 for k in ks],axis=0)
        contrastes[b]={f'{a}_menos_{z}':contraste_temporal(partes[b].origem_utc,perdas[a],perdas[z],cfg['bootstrap'])
                       for a,z in [('adamw_seis','adam_seis'),('adamw_seis','mamba16_seis'),('adamw_seis','naive'),('adamw_tres','lstm_tres')]}
    v=contrastes['validacao']['adamw_seis_menos_adam_seis']
    principal={'media_mse_menor':medias['validacao']['adamw_seis']['metricas']['mse']<medias['validacao']['adam_seis']['metricas']['mse'],
               'ic95_principal_inteiramente_favoravel':v['ic95']['14'][1]<0,'promocao_automatica':False}
    # Mesmas regras e preços do backtest encerrado; somente novas previsões.
    bp=ler_json(RAIZ/'registros/backtest_carteira/execucao_atual.json');pb=RAIZ/bp['pasta'];cb=ler_json(pb/'congelamento.json')['contrato']
    minutos_b,primeiro_b=carregar(pb,cb);carteiras={};constantes={}
    for s in ss:
        k=f'cryptomamba_adamw_{s}'
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
    r={'utc':agora(),'execucao':f['id'],'novos':6,'herdados':59,'por_ajuste':res,'medias':medias,
       'contrastes':contrastes,'criterio_primario':principal,'diagnosticos':diags,'auditoria_checkpoint':auditoria,
       'carteiras':carteiras,'constantes_validacao':constantes,
       'referencia_carteira':{'arquivo':(pb/'resultados/comparacao.json').relative_to(RAIZ).as_posix(),'sha256':sha256(pb/'resultados/comparacao.json')},
       'limites':['Retrospectivo:2024 seleção/2025 previamente conhecido; não holdout novo ou walk-forward.',
                  'Decay nominal igual não iguala regularização efetiva; efeito total da troca Adam→AdamW.',
                  'Médias de seeds individuais, não ensemble; não escolher por retorno Spot.',
                  '54simulações Smart secundárias, sem regra/política nova; custos/filtros são cenários.']}
    salvar_json(dest/'resultados.json',r);salvar_json(dest/'conferencia_metricas.json',conf)
    salvar_json(dest/'manifesto.json',{'arquivos':{q.relative_to(dest).as_posix():sha256(q) for q in dest.rglob('*') if q.is_file()}})
    salvar_json(p/'publicacao.json',{'pasta':dest.relative_to(p).as_posix(),'manifesto_sha256':sha256(dest/'manifesto.json')})
    return dest,r


def relatar(r):
    def n(v):return f'{v:.10f}'.replace('.',',')
    def pct(v):return f'{100*v:+.2f}%'.replace('.',',')
    linhas=['# Adam → AdamW no CryptoMamba adaptado','',
        f'Execução `{r["execucao"]}`: seis ajustes novos, 59 referências herdadas e 54 novas simulações Smart. [Protocolo](protocolo_otimizador_cryptomamba.md), [estado](../registros/otimizador/estado.json).',
        '', '## Comparação preditiva','',
        'Única diferença científica: otimizador. O Mamba16 já usava AdamW e é referência auxiliar; o par controlado é CryptoMamba/AdamW contra CryptoMamba/Adam. Médias individuais, não ensemble.',
        '', '| Parte | Modelo | Seeds | MSE | RMSE | MAE |','|---|---|---:|---:|---:|---:|']
    for b in ('validacao','teste'):
        for nome,g in r['medias'][b].items():
            m=g['metricas'];linhas.append(f'| {b} | {nome} | {g["n_seeds"]} | {n(m["mse"])} | {n(m["rmse"])} | {n(m["mae"])} |')
    linhas+=['','## Contraste primário e incerteza','','| Parte | Diferença MSE AdamW−Adam | IC95% de 14 dias |','|---|---:|---|']
    for b in ('validacao','teste'):
        v=r['contrastes'][b]['adamw_seis_menos_adam_seis'];linhas.append(f'| {b} | {v["diferenca_mse_a_menos_b"]:.10g} | {v["ic95"]["14"]} |')
    favoravel=r['criterio_primario']['media_mse_menor'] and r['criterio_primario']['ic95_principal_inteiramente_favoravel']
    linhas+=['','O critério primário '+('foi atendido neste contraste retrospectivo.' if favoravel else 'não foi atendido; não há evidência suficiente pelo critério fixado para substituir a versão anterior.'),
        'A diferença entre Adam/AdamW inclui regularização efetiva diferente mesmo com decay nominal igual. Nenhuma promoção automática por MSE de teste ou lucro.',
        '', '## Seeds, constância e operação','', '| Seed | MSE validação | MSE teste | Previsões distintas teste | Desvio previsão teste | Smart base teste |','|---|---:|---:|---:|---:|---:|']
    for s in (17,42,2026,7,123,31415):
        k=f'cryptomamba_adamw_{s}';v=r['por_ajuste'][k];d=r['diagnosticos'][k]['teste'];op=r['carteiras'][f'teste/base/smart/{k}']
        linhas.append(f'| {s} | {n(v["metricas"]["validacao"]["mse"])} | {n(v["metricas"]["teste"]["mse"])} | {d["distintas"]} | {n(d["desvio_previsao"])} | {pct(op["retorno_liquido"])} |')
    linhas+=['','## Carteira Smart: médias de seis seeds','','| Parte | Cenário | Regra | Retorno | Queda máxima média | Exposição |','|---|---|---|---:|---:|']
    for b in ('validacao','teste'):
        for custo in ('ideal','base','agravado'):
            for pol in (['smart','smart_constante'] if b=='teste' else ['smart']):
                vs=[r['carteiras'][f'{b}/{custo}/{pol}/cryptomamba_adamw_{s}'] for s in (17,42,2026,7,123,31415)]
                linhas.append(f'| {b} | {custo} | {pol} | {pct(np.mean([v["retorno_liquido"] for v in vs]))} | {pct(np.mean([v["drawdown_minuto_close"] for v in vs]))} | {pct(np.mean([v["exposicao_media"] for v in vs]))} |')
    linhas+=['', 'Comparar aos números preservados do [backtest anterior](resultados_backtest_carteira.md), com os mesmos instantes e regras. Smart 2% não é stop. Não escolher uma seed lucrativa. SpotR0 separado consta dos resultados estruturados; não misturar sua contabilidade com a carteira retida.',
        '', '## Preservação e limites','',
        'Qualificação sintética, recarga exata, checkpoints, seleção por validação, métricas por origem, livro Smart e hashes anteriores foram conferidos. As tentativas e publicações anteriores continuam em seus caminhos. 2024/2025 já conhecidos: exploração retrospectiva, sem novo holdout ou walk-forward. Não há garantia de lucro ou execução real. Mais seeds não corrigem toda seleção adaptativa. [Estado, recibos e publicação](../registros/otimizador/estado.json).']
    p=RAIZ/'docs/resultados_otimizador_cryptomamba.md'
    if p.exists():raise FileExistsError('Relatório existente; preservar.')
    p.write_text('\n'.join(linhas)+'\n',encoding='utf-8');return p.relative_to(RAIZ).as_posix()


def posprocessar():
    from .ciclo import REGISTROS, SEEDS, conferir_execucao
    if (REGISTROS/'fechamento.json').exists():raise ValueError('Ciclo já encerrado; não repetir pós-processamento.')
    p,f,consumo,partes,refs,pub_ant=conferir_execucao()
    assert ler_json(p/'progresso.json')['status']=='concluido' and not ler_json(p/'processo.json')['ativo']
    assert set(ler_json(p/'progresso.json')['concluidos'])==set(SEEDS)
    try:
        novas={}
        for s in SEEDS:
            ts=[t for t in (p/'celulas'/f'cryptomamba_adamw_{s}').glob('tentativa_*') if (t/'conclusao.json').exists()]
            assert len(ts)==1;conferir(ts[0]);novas[s]=ts[0]
        pub,r=publicar(p,f,partes,novas,refs,pub_ant)
        conferir_arquivos(pub,ler_json(pub/'manifesto.json')['arquivos'])
        guard=ler_json(REGISTROS/'preservacao_antes.json')['arquivos'];conferir_arquivos(RAIZ,guard)
        rel=relatar(r)
        fim={'situacao':'concluido_conferido','utc':agora(),'execucao':ler_json(REGISTROS/'execucao.json'),
             'novos':6,'herdados':59,'simulacoes_smart':54,'preservados':len(guard),
             'publicacao':pub.relative_to(RAIZ).as_posix(),'manifesto_sha256':sha256(pub/'manifesto.json'),
             'relatorio':rel,'criterio_primario':r['criterio_primario'],'proxima_acao':'Interpretar; sem promoção ou novo treinamento automático.'}
        salvar_json(REGISTROS/'fechamento.json',fim);salvar_json(REGISTROS/'estado.json',fim)
        cat=ler_json(RAIZ/'registros/catalogo_estudos.json')
        for row in cat.get('rodadas_ohlcv',[]):
            if row.get('execucao')==f['id']:row.update(situacao='concluido_conferido',ajustes_neurais_novos_concluidos=6,publicacao=fim['publicacao'],relatorio=rel)
        cat['etapa_atual']['situacao']='otimizador_cryptomamba_concluido_conferido';cat['etapa_atual']['otimizador_cryptomamba']=fim
        salvar_json(RAIZ/'registros/catalogo_estudos.json',cat)
        doc=RAIZ/'docs/andamento.md';t=doc.read_text(encoding='utf-8-sig')
        nota=f'## Otimizador CryptoMamba concluído e conferido\n\nExecução `{f["id"]}`: seis AdamW novos e59referências herdadas; 54simulações Smart na política anterior, sem nova busca. [Resultados](resultados_otimizador_cryptomamba.md), [estado](../registros/otimizador/estado.json). Fontes/configurações/checkpoints/recarga/métricas e preservação conferidos; Adam original e Mamba16 continuam intactos.2024/2025 retrospectivos; sem promoção automática.\n\n'
        doc.write_text(t.replace('# Andamento do CryptoCasting\n','# Andamento do CryptoCasting\n\n'+nota,1),encoding='utf-8')
        return fim
    except BaseException:
        salvar_json(REGISTROS/'incidentes'/f'{uuid4().hex}.json',{'utc':agora(),'fase':'posprocessamento_sem_treino','erro':traceback.format_exc()});raise
