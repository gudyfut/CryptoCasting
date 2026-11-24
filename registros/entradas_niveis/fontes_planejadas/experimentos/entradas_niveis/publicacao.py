"""Conferência, médias de oito seeds, contrastes e carteiras; nunca retreina."""
import contextlib
from pathlib import Path

import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256
from treinamento.preservacao import conferir
from avaliacao.metricas import calcular
from avaliacao.publicacao import conferir_previsoes
from experimentos.huber_blocos.publicacao import auditar_ajuste, media_metricas, janela_operacional
from backtest_carteira.simulador import simular
from backtest_carteira.auditoria import conferir as conferir_carteira
from backtest_carteira.mercado import carregar as carregar_minutos
from .dados import REG
from .estatisticas import PARES, contraste


def resumo_grupo(rs):
    m=media_metricas(rs)
    m['mse_por_seed']=[r['mse'] for r in rs]
    return m


def publicar():
    from .ciclo import conferir_execucao, predecessora
    if (REG/'fechamento.json').exists():raise FileExistsError('Ciclo já encerrado; não repetir publicação.')
    p,f,xs=conferir_execucao();c=f['contrato']['configuracao']
    assert ler_json(p/'progresso.json')['status']=='concluido' and not ler_json(p/'processo.json')['ativo']
    import fcntl
    with (p/'publicacao.lock').open('a+b') as trava:
        fcntl.flock(trava,fcntl.LOCK_EX|fcntl.LOCK_NB)
        pred,pf,pub,herdados=predecessora(c)
        n=len(list((p/'publicacoes').glob('tentativa_*')))+1
        dest=p/'publicacoes'/f'tentativa_{n:03d}';dest.mkdir(parents=True)
        previsoes={};resultados={};auditorias={};medias={};perdas={parte:{} for parte in ('validacao','teste')}
        origens_teste={};arquivos_origem={}
        for b in c['blocos']:
            medias[b]={parte:{} for parte in ('validacao','teste')}
            for parte in perdas:perdas[parte][b]={}
            for variante in c['variantes']:
                for seed in c['seeds']:
                    if variante=='atual':
                        raiz=pred/'celulas'/f'{b}_mse_{seed}';cfg=pf['contrato']['receitas'][b]['mse'];ff=pf
                    else:
                        raiz=p/'celulas'/f'{b}_{variante}_{seed}';cfg=f['contrato']['receitas'][b][variante];ff=f
                    concluidas=list(raiz.glob('tentativa_*/conclusao.json'));assert len(concluidas)==1;t=concluidas[0].parent
                    key=f'{b}_{variante}_{seed}';conferir(t)
                    auditorias[key]=auditar_ajuste(t,ff,xs[b][variante],cfg)
                    r=ler_json(t/'resultado.json');resultados[key]=dict(r,tentativa_origem=t.relative_to(RAIZ).as_posix(),herdado=variante=='atual')
                    arquivos_origem[(t/'conclusao.json').relative_to(RAIZ).as_posix()]=sha256(t/'conclusao.json')
                    for parte in ('validacao','teste','operacional'):
                        q=pd.read_parquet(t/f'previsoes_{parte}.parquet')
                        conferir_previsoes(q,xs[b][variante]._conjunto.partes[parte],r['metricas'].get(parte))
                        previsoes[b,variante,seed,parte]=q
                        if parte!='operacional':
                            calc=calcular(q.alvo,q.previsao)
                            for k in ('mse','rmse','mae','vies'):
                                assert calc[k]==r['metricas'][parte][k]
                for parte in ('validacao','teste'):
                    rs=[resultados[f'{b}_{variante}_{s}']['metricas'][parte] for s in c['seeds']]
                    medias[b][parte][variante]=resumo_grupo(rs)
                    qs=[previsoes[b,variante,s,parte] for s in c['seeds']]
                    for q in qs:
                        pd.testing.assert_frame_equal(q.drop(columns='previsao'),qs[0].drop(columns='previsao'),check_exact=True)
                    perdas[parte][b][variante]=np.stack([(q.previsao-q.alvo).to_numpy()**2 for q in qs])
                    datas=pd.DatetimeIndex(qs[0].origem_utc)
                    if 'origens' in perdas[parte][b]:
                        assert perdas[parte][b]['origens'].equals(datas)
                    perdas[parte][b]['origens']=datas
            for v in c['variantes_novas']:
                t=p/'controles'/f'B1_{v}_42'/'tentativa_001'
                if b=='B1':auditorias[f'controle_{v}']=auditar_ajuste(t,f,xs[b][v],f['contrato']['receitas'][b][v],True)
        globais={};contrastes={}
        for parte in ('validacao','teste'):
            globais[parte]={}
            for variante in c['variantes']:
                campos=('mse','rmse','mae','vies','acuracia_direcional','acerto_balanceado_direcional')
                g={k:float(np.mean([medias[b][parte][variante][k] for b in c['blocos']])) for k in campos}
                naive=float(np.mean([resultados[f'{b}_{variante}_{c["seeds"][0]}']['metricas'][parte]['mse_naive'] for b in c['blocos']]))
                g.update(mse_naive=naive,habilidade_mse=1-g['mse']/naive,blocos=4,seeds_por_bloco=8)
                globais[parte][variante]=g
            contrastes[parte]={f'{a}_menos_{z}':contraste(perdas[parte],a,z,replicas=c['bootstrap']['replicas']) for a,z in PARES}
        # Importa somente A/MSE e benchmarks da publicação já conferida.
        carteiras={}
        for key,rs in herdados['carteiras'].items():
            partes=key.split('/')
            if partes[1] not in ('mse','benchmark'):continue
            if partes[1]=='mse':partes[1]='atual'
            carteiras['/'.join(partes)]=dict(rs,herdado=True,publicacao_origem=pub.relative_to(RAIZ).as_posix(),chave_origem=key)
        assert len(carteiras)==216
        cb=pf['contrato']['carteira'];minutos,primeiro=carregar_minutos(RAIZ/cb['pasta'],cb['contrato']);opcfg=cb['contrato']['configuracao']
        novas=0
        for b in c['blocos']:
            for variante in c['variantes_novas']:
                for seed in c['seeds']:
                    q=janela_operacional(previsoes[b,variante,seed,'operacional'],c['blocos'][b]['teste'][1])
                    for politica in c['politicas']:
                        for custo in c['cenarios']:
                            r,o,cur,di,si=simular(q,minutos,primeiro,opcfg,politica,custo)
                            ver=conferir_carteira(q,minutos,primeiro,opcfg,politica,custo,r,o,di)
                            key=f'{b}/{variante}/{seed}/{politica}/{custo}';d=dest/'carteiras'/key;d.mkdir(parents=True)
                            for nome,valor in (('resumo',r),('ordens',o),('sinais',si),('verificacao',ver)):
                                salvar_json(d/f'{nome}.json',valor)
                            cur.to_parquet(d/'curva.parquet',index=False);di.to_parquet(d/'diarios.parquet',index=False)
                            carteiras[key]=dict(r,herdado=False);novas+=1
                            salvar_json(p/'publicacao_progresso.json',{'fase':'carteiras','novas_concluidas':novas,'total_novas':384,'utc':agora()})
        assert novas==384 and len(carteiras)==600 and len(resultados)==96
        opmedias={}
        for b in c['blocos']:
            opmedias[b]={}
            for variante in c['variantes']:
                for pol in c['politicas']:
                    for custo in c['cenarios']:
                        rs=[carteiras[f'{b}/{variante}/{s}/{pol}/{custo}'] for s in c['seeds']]
                        m={k:float(np.mean([r[k] for r in rs])) for k in ('retorno_liquido','drawdown_minuto_close','exposicao_media','capital_final','comissoes_usdt','slippage_usdt')}
                        m.update(desvio_retorno_seeds=float(np.std([r['retorno_liquido'] for r in rs],ddof=1)),
                            seeds_lucrativas=sum(r['retorno_liquido']>0 for r in rs))
                        opmedias[b][f'{variante}/{pol}/{custo}']=m
        r={'utc':agora(),'execucao':f['id'],'principais_novos':64,'controles_reais':2,'referencias_herdadas':32,
            'por_ajuste':resultados,'auditoria':auditorias,'medias_por_bloco':medias,'medias_globais':globais,
            'contrastes':contrastes,'carteiras':carteiras,'medias_operacionais_por_bloco':opmedias,
            'simulacoes_novas':384,'simulacoes_herdadas':216,'arquivos_origem':arquivos_origem,
            'limites':['Retrospectivo2024/2025; oito seeds não garantem certeza.',
                'Três contrastes fixos; IC98,333% principal Bonferroni,14dias; sensibilidades7/28.',
                'Mesmas origens, alvo e cinco canais; sem timestamp, indicadores ou novas buscas.',
                'Comparação de entradas sob receita fixa; não demonstra desempenho ótimo de cada representação.',
                'Médias de modelos individuais, não ensemble; carteiras independentes por bloco.',
                'Não há retomada automática após falha nem repetição até passar/lucrar.']}
        salvar_json(dest/'resultados.json',r)
        salvar_json(dest/'manifesto.json',{'arquivos':{q.relative_to(dest).as_posix():sha256(q) for q in dest.rglob('*') if q.is_file()}})
        # Conferência nova, sem confiar no cache da preparação ou publicação anterior.
        for nome,h in ler_json(dest/'manifesto.json')['arquivos'].items():assert sha256(dest/nome)==h
        conferir_execucao()
        rel=relatar(r)
        salvar_json(p/'publicacao.json',{'pasta':dest.relative_to(p).as_posix(),'manifesto_sha256':sha256(dest/'manifesto.json')})
        fim={'situacao':'concluido_conferido','utc':agora(),'execucao':ler_json(REG/'execucao.json'),
            'principais_novos':64,'controles_reais':2,'referencias_herdadas':32,'simulacoes_novas':384,'simulacoes_herdadas':216,
            'publicacao':dest.relative_to(RAIZ).as_posix(),'relatorio':rel,'manifesto_sha256':sha256(dest/'manifesto.json'),
            'decisoes':{k:v['decisao'] for k,v in contrastes['teste'].items()},'promocao_automatica':False}
        salvar_json(REG/'fechamento.json',fim);salvar_json(REG/'estado.json',fim)
        cat=ler_json(RAIZ/'registros/catalogo_estudos.json')
        cat.setdefault('rodadas_ohlcv',[]).append({'chave':c['ciclo'],'situacao':'concluido_conferido',
            'execucao':f['id'],'estado':'registros/entradas_niveis/estado.json','protocolo':'docs/protocolo_entradas_niveis.md',
            'ajustes_neurais_novos_concluidos':66,'referencias_herdadas':32,'publicacao':fim['publicacao'],'relatorio':rel})
        salvar_json(RAIZ/'registros/catalogo_estudos.json',cat)
        with (RAIZ/'docs/andamento.md').open('a',encoding='utf-8') as doc:
            doc.write(f'\n## Entradas em nível encerradas\n\nExecução `{f["id"]}`:64ajustes novos+2controles,32referências herdadas. [Resultados](resultados_entradas_niveis.md). Sem promoção ou nova busca automática.\n')
        return fim


def relatar(r):
    linhas=['# Entradas relativas, cruas e níveis padronizados','',
        f'Execução `{r["execucao"]}`. Oito seeds por versão/bloco; quatro blocos,64ajustes novos+2controles e32referências MSE herdadas.',
        '', '[Protocolo](protocolo_entradas_niveis.md), [estado](../registros/entradas_niveis/estado.json).',
        '', '## Médias das oito seeds por bloco','',
        '| Bloco | Parte | Atual MSE | Crua MSE | Níveis padronizados MSE |','|---|---|---:|---:|---:|']
    for b,partes in r['medias_por_bloco'].items():
        for parte,m in partes.items():
            linhas.append(f'| {b} | {parte} | {m["atual"]["mse"]:.10f} | {m["crua"]["mse"]:.10f} | {m["niveis_padronizados"]["mse"]:.10f} |')
    linhas+=['','## Médias com peso igual entre os quatro blocos','',
        '| Parte | Variante | MSE | RMSE×100 | MAE×100 | Habilidade Naive |','|---|---|---:|---:|---:|---:|']
    for parte,gs in r['medias_globais'].items():
        for v,m in gs.items():
            linhas.append(f'| {parte} | {v} | {m["mse"]:.10f} | {100*m["rmse"]:.4f} | {100*m["mae"]:.4f} | {100*m["habilidade_mse"]:+.3f}% |')
    linhas+=['','## Contrastes predefinidos de teste','',
        '| Contraste | Diferença MSE | IC98,333% principal | Interpretação |','|---|---:|---|---|']
    for k,t in r['contrastes']['teste'].items():
        linhas.append(f'| {k} | {t["diferenca_mse"]:.10g} | {t["intervalos"]["14"]["ic_bonferroni_98_333"]} | {t["decisao"]} |')
    linhas+=['','## Smart com custos base: média de oito carteiras independentes','',
        '| Bloco | Atual | Crua | Níveis padronizados |','|---|---:|---:|---:|']
    for b,m in r['medias_operacionais_por_bloco'].items():
        vals=[100*m[f'{v}/smart/base']['retorno_liquido'] for v in ('atual','crua','niveis_padronizados')]
        linhas.append(f'| {b} | {vals[0]:+.2f}% | {vals[1]:+.2f}% | {vals[2]:+.2f}% |')
    linhas+=['','Todos os resultados por seed, dispersões, decisões, sensibilidades7/28, custos, risco e referências operacionais estão na publicação estruturada. Controles reais não entram nas médias.',
        '', *r['limites']]
    p=RAIZ/'docs/resultados_entradas_niveis.md'
    if p.exists():raise FileExistsError('Relatório já existe; preservar e usar revisão de leitura.')
    p.write_text('\n'.join(linhas)+'\n',encoding='utf-8')
    return p.relative_to(RAIZ).as_posix()
