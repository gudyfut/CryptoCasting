"""Avaliacao final sem chamadas ao agente ou ao treinador."""
import math
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, ler_json, salvar_json, sha256, agora, conferir_arquivos
from .contrato import SEEDS, FINAIS

def intervalo(blocos, base):
    diarios=[];pontos=[]
    for b in FINAIS:
        q=blocos[b];dif=q['candidata']-q[base];pontos.append(float(dif.mean()))
        t=q['origens'];n=pd.Series(1,index=t).resample('D').sum().to_numpy()
        soma=np.stack([pd.Series(v,index=t).resample('D').sum().to_numpy() for v in dif])
        diarios.append((soma,n))
    ints={}
    for largura in [7,14,28]:
        rng=np.random.default_rng(20261104+largura);amostras=[]
        for _ in range(2000):
            seeds=rng.integers(0,8,8);valores=[]
            for soma,n in diarios:
                ini=rng.integers(0,len(n),math.ceil(len(n)/largura))
                ix=((ini[:,None]+np.arange(largura))%len(n)).ravel()[:len(n)]
                valores.append(float(soma[seeds][:,ix].sum()/(8*n[ix].sum())))
            amostras.append(float(np.mean(valores)))
        ints[str(largura)]={'ic95':np.quantile(amostras,[.025,.975]).tolist(),
                            'ic97_5_bonferroni_dois_contrastes':np.quantile(amostras,[.0125,.9875]).tolist()}
    return {'diferenca_mse':float(np.mean(pontos)),'intervalos':ints,
            'limite':'Condicional aos modelos/periodos conhecidos; nao corrige selecao adaptativa inteira.'}

def publicar(pasta):
    f=ler_json(pasta/'congelamento.json');finalista=ler_json(pasta/'finalista.json')
    assert finalista['receita']
    assert sha256(pasta/'finalista.json')==ler_json(pasta/'fase_final.json')['finalista_sha256']
    assert not (pasta/'publicacao.json').exists(),'Publicacao concluida nao pode ser repetida.'
    for b in FINAIS:
        for v in ['referencia','candidata']:
            for s in SEEDS:
                d=pasta/'final'/v/f'{b}_{s}'
                conferir_arquivos(d,ler_json(d/'conclusao.json')['arquivos'])
    dest=pasta/'publicacoes'/f'tentativa_{len(list((pasta/"publicacoes").glob("tentativa_*")))+1:03}'
    dest.mkdir(parents=True,exist_ok=False)
    metricas={};perdas={};previsoes={}
    for b in FINAIS:
        perdas[b]={};metricas[b]={}
        observado=None
        for v in ['referencia','candidata']:
            rs=[];erros=[]
            for s in SEEDS:
                d=pasta/'final'/v/f'{b}_{s}'
                conferir_arquivos(d,ler_json(d/'conclusao.json')['arquivos'])
                r=ler_json(d/'resultado.json');q=pd.read_parquet(d/'previsoes_teste.parquet')
                if observado is None:observado=q.drop(columns='previsao')
                else:pd.testing.assert_frame_equal(observado,q.drop(columns='previsao'))
                e=(q.previsao-q.alvo).to_numpy(float)
                assert math.isclose(math.fsum(float(x)**2 for x in e)/len(e),r['teste']['mse'],rel_tol=1e-12)
                rs.append(r);erros.append(e*e);previsoes[b,v,s]=q
            perdas[b][v]=np.stack(erros)
            metricas[b][v]={k:float(np.mean([r['teste'][k] for r in rs])) for k in rs[0]['teste'] if k!='n'}
            metricas[b][v]['mse_por_seed']=[r['teste']['mse'] for r in rs]
        perdas[b]['origens']=pd.DatetimeIndex(observado.origem_utc)
        perdas[b]['naive']=np.tile(observado.alvo.to_numpy(float)**2,(8,1))
        mn=float(perdas[b]['naive'].mean())
        metricas[b]['naive']={'mse':mn,'rmse':math.sqrt(mn),'mae':float(np.abs(observado.alvo).mean())}
    globais={v:{k:float(np.mean([metricas[b][v][k] for b in FINAIS])) for k in metricas['B1'][v]
                if k!='mse_por_seed'} for v in ['referencia','candidata','naive']}
    contrastes={v:intervalo(perdas,v) for v in ['referencia','naive']}
    from backtest_carteira.mercado import carregar
    from backtest_carteira.simulador import simular,COLUNAS
    from backtest_carteira.auditoria import conferir
    cb=ler_json(RAIZ/'dados/experimentos/backtest_carteira_8ec8a66648313caa48e3/congelamento.json')
    cfg=cb['contrato']['configuracao']
    for item in cb['contrato']['mercado_partes']:
        # A origem do mapa fornece o SHA publicado dos minutos; verificar pelo manifesto abaixo.
        assert (RAIZ/cfg['mercado_pasta']/item['arquivo']).is_file()
    mp=RAIZ/cfg['mercado_pasta'];man=ler_json(mp/'manifesto.json')
    conferir_arquivos(mp,man['arquivos'])
    minutos,primeiro=carregar(RAIZ,cb['contrato'])
    carteiras={}
    for b in FINAIS:
        series=[(v,str(s),previsoes[b,v,s][COLUNAS]) for v in ['referencia','candidata'] for s in SEEDS]
        base=previsoes[b,'referencia',SEEDS[0]][COLUNAS].copy();base['previsao']=0.
        series += [('benchmark','benchmark',base)]
        for v,s,q in series:
            politicas=['comprar_manter','caixa'] if v=='benchmark' else ['smart','diaria24']
            for pol in politicas:
                for custo in ['ideal','base','agravado']:
                    resumo,ordens,curva,diarios,sinais=simular(q,minutos,primeiro,cfg,pol,custo)
                    audit=conferir(q,minutos,primeiro,cfg,pol,custo,resumo,ordens,diarios)
                    key=f'{b}/{v}/{s}/{pol}/{custo}';d=dest/'carteiras'/key;d.mkdir(parents=True)
                    for nome,valor in [('resumo',resumo),('ordens',ordens),('sinais',sinais),('auditoria',audit)]:
                        salvar_json(d/f'{nome}.json',valor)
                    curva.to_parquet(d/'curva.parquet',index=False);diarios.to_parquet(d/'diarios.parquet',index=False)
                    carteiras[key]=resumo
                    salvar_json(pasta/'progresso_publicacao.json',{'utc':agora(),'simulacoes':len(carteiras),'total':408})
    assert len(carteiras)==408
    op={}
    for b in FINAIS:
        op[b]={}
        for v in ['referencia','candidata']:
            for pol in ['smart','diaria24']:
                for custo in ['ideal','base','agravado']:
                    rs=[carteiras[f'{b}/{v}/{s}/{pol}/{custo}'] for s in SEEDS]
                    op[b][f'{v}/{pol}/{custo}']={k:float(np.mean([r[k] for r in rs])) for k in
                        ['retorno_liquido','drawdown_minuto_close','exposicao_media','comissoes_usdt','slippage_usdt','ordens_executadas']}
    resultado={'utc':agora(),'execucao':f['id'],'finalista':finalista,'medias_por_bloco':metricas,
        'medias_globais':globais,'contrastes':contrastes,'carteiras':carteiras,'medias_operacionais':op,
        'limites':['2024/2025 ja consultados; retrospectivo, nao holdout intocado.',
                  'Busca adaptativa: comparacao de receitas, nao ablacao de um fator.',
                  'Referencia nova usa o mesmo aquecimento336 e implementacao; nao substituir resultados anteriores.',
                  'Cada carteira inicia10000USDT por bloco; nao compor retornos entre blocos.',
                  'MSE e lucro distintos; nenhuma promocao automatica.']}
    salvar_json(dest/'resultados.json',resultado)
    linhas=['# Busca adaptativa assistida por Astra — resultados','',f'Execucao `{f["id"]}`. Comparacao retrospectiva apos congelar finalista.','',
        '| Versao | MSE teste medio | MAE teste medio |','|---|---:|---:|']
    for v in ['referencia','candidata','naive']:
        linhas.append(f'| {v} | {globais[v]["mse"]:.10g} | {globais[v].get("mae",float("nan")):.6g} |')
    linhas+=['','Intervalos, seeds e todas as carteiras em `publicacao/resultados.json` da execucao.','',*resultado['limites']]
    texto='\n'.join(linhas)+'\n'
    (dest/'relatorio.md').write_text(texto,encoding='utf-8')
    salvar_json(dest/'manifesto.json',{'arquivos':{p.relative_to(dest).as_posix():sha256(p) for p in dest.rglob('*') if p.is_file()}})
    p=RAIZ/'docs/resultados_busca_astra.md'
    if not p.exists():p.write_text(texto,encoding='utf-8')
    salvar_json(pasta/'publicacao.json',{'utc':agora(),'pasta':dest.relative_to(RAIZ).as_posix(),
        'manifesto_sha256':sha256(dest/'manifesto.json'),'simulacoes':408})
    return resultado

def publicar_posteriormente():
    """Recuperar somente publicacao, preservando tentativa incompleta; nao chama treino."""
    import msvcrt
    reg=RAIZ/'registros/busca_astra';ptr=ler_json(reg/'execucao.json');p=RAIZ/ptr['pasta']
    assert not ler_json(p/'processo.json')['ativo'],'Coordenador precisa estar encerrado.'
    from .ciclo import conferir
    f=conferir(p,ptr)
    with (reg/'coordenador.lock').open('a+b') as lock:
        lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        publicar(p)
        conferir_arquivos(RAIZ,ler_json(reg/'preservacao_antes.json')['arquivos'])
        fechamento={'utc':agora(),'situacao':'concluido_conferido','execucao':ptr,
                    'publicacao_posterior':True,'novos_treinos_na_publicacao':0,'preservacao_conferida':True}
        salvar_json(p/'fechamento.json',fechamento);salvar_json(reg/'fechamento.json',fechamento)
        salvar_json(reg/'estado.json',fechamento)
