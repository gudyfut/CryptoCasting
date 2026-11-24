"""Comparacao pareada; simula somente os32 modelos crus novos."""
import math
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, ler_json, salvar_json, sha256, conferir_arquivos, agora
from .contrato import ORIGEM, ASTRA, CRUA, SEEDS, FINAIS, conferir_execucao

def intervalo(blocos,esquerda,direita,replicas=2000):
    diarios=[];pontos=[]
    for b in FINAIS:
        q=blocos[b];dif=q[esquerda]-q[direita];pontos.append(float(dif.mean()))
        t=q['origens'];n=pd.Series(1,index=t).resample('D').sum().to_numpy()
        soma=np.stack([pd.Series(v,index=t).resample('D').sum().to_numpy() for v in dif])
        diarios.append((soma,n))
    ints={}
    for largura in [7,14,28]:
        rng=np.random.default_rng(20261104+largura);amostras=[]
        for _ in range(replicas):
            seeds=rng.integers(0,8,8);valores=[]
            for soma,n in diarios:
                ini=rng.integers(0,len(n),math.ceil(len(n)/largura))
                ix=((ini[:,None]+np.arange(largura))%len(n)).ravel()[:len(n)]
                valores.append(float(soma[seeds][:,ix].sum()/(8*n[ix].sum())))
            amostras.append(float(np.mean(valores)))
        ints[str(largura)]={'ic95':np.quantile(amostras,[.025,.975]).tolist(),
            'ic98_333_bonferroni_tres_contrastes':np.quantile(amostras,[.05/6,1-.05/6]).tolist()}
    return {'diferenca_mse':float(np.mean(pontos)),'esquerda':esquerda,'direita':direita,
        'intervalos':ints,'limite':'Condicional aos periodos/receitas ja conhecidos; nao corrige selecao adaptativa anterior.'}

def publicar(p,ptr):
    f=conferir_execucao(p,ptr)
    assert not (p/'publicacao.json').exists()
    assert (p/'controle_astra.json').exists() and (p/'controle_crua.json').exists()
    jobs=ler_json(p/'ajustes.json');assert len(jobs)==34 and all(j['status']=='concluido' for j in jobs)
    origem=RAIZ/f['publicacao_origem']['pasta'];original=ler_json(origem/'resultados.json')
    assert sha256(origem/'manifesto.json')==f['publicacao_origem']['manifesto_sha256']
    conferir_arquivos(origem,ler_json(origem/'manifesto.json')['arquivos'])
    dest=p/'publicacoes'/f'tentativa_{len(list((p/"publicacoes").glob("tentativa_*")))+1:03}'
    dest.mkdir(parents=True,exist_ok=False)
    metricas={};perdas={};previsoes={};series={};recargas=0
    for b in FINAIS:
        metricas[b]={};perdas[b]={};observado=None
        for v,receita in [('astra',ASTRA),('crua',CRUA)]:
            rs=[];erros=[]
            for s in SEEDS:
                if v=='astra':
                    h=f['herancas'][f'{b}_{s}'];d=RAIZ/h['pasta'];assert sha256(d/'conclusao.json')==h['conclusao_sha256']
                else:d=p/'crua'/f'{b}_{s}'
                conferir_arquivos(d,ler_json(d/'conclusao.json')['arquivos'])
                r=ler_json(d/'resultado.json');assert r['seed']==s and r['bloco']==b and r['receita']==receita and r['recarga_exata']
                q=pd.read_parquet(d/'previsoes_teste.parquet')
                if observado is None:observado=q.drop(columns='previsao')
                else:pd.testing.assert_frame_equal(observado,q.drop(columns='previsao'))
                e=(q.previsao-q.alvo).to_numpy(float)
                assert math.isclose(math.fsum(float(x)**2 for x in e)/len(e),r['teste']['mse'],rel_tol=1e-12)
                assert math.isclose(math.fsum(abs(float(x)) for x in e)/len(e),r['teste']['mae'],rel_tol=1e-12)
                ea=ler_json(ORIGEM/'final/candidata'/f'{b}_{s}'/'escalas.json');ec=ler_json(d/'escalas.json')
                for chave in ['contagens','media_alvo','escala_alvo','inicio_comum_indice']:assert ea[chave]==ec[chave]
                rs.append(r);erros.append(e*e);previsoes[b,v,s]=q;recargas+=1
                series[f'{b}/{v}/{s}']={'pasta':d.relative_to(RAIZ).as_posix(),'conclusao_sha256':sha256(d/'conclusao.json'),'herdada':v=='astra'}
            perdas[b][v]=np.stack(erros)
            metricas[b][v]={k:float(np.mean([r['teste'][k] for r in rs])) for k in rs[0]['teste'] if k!='n'}
            metricas[b][v]['mse_por_seed']=[r['teste']['mse'] for r in rs]
        perdas[b]['origens']=pd.DatetimeIndex(observado.origem_utc)
        perdas[b]['naive']=np.tile(observado.alvo.to_numpy(float)**2,(8,1))
        mn=float(perdas[b]['naive'].mean())
        metricas[b]['naive']={'mse':mn,'rmse':math.sqrt(mn),'mae':float(np.abs(observado.alvo).mean())}
    globais={v:{k:float(np.mean([metricas[b][v][k] for b in FINAIS])) for k in metricas['B1'][v] if k!='mse_por_seed'} for v in ['astra','crua','naive']}
    contrastes={f'{a}_menos_{b}':intervalo(perdas,a,b) for a,b in [('astra','crua'),('astra','naive'),('crua','naive')]}
    salvar_json(dest/'metricas.json',{'medias_por_bloco':metricas,'medias_globais':globais,'contrastes':contrastes})
    from backtest_carteira.mercado import carregar
    from backtest_carteira.simulador import simular,COLUNAS
    from backtest_carteira.auditoria import conferir
    cb=ler_json(RAIZ/'dados/experimentos/backtest_carteira_8ec8a66648313caa48e3/congelamento.json');cfg=cb['contrato']['configuracao']
    mp=RAIZ/cfg['mercado_pasta'];conferir_arquivos(mp,ler_json(mp/'manifesto.json')['arquivos'])
    minutos,primeiro=carregar(RAIZ,cb['contrato'])
    carteiras={};vinculos={}
    for key,resumo in original['carteiras'].items():
        partes=key.split('/')
        if partes[1] not in ['candidata','benchmark']:continue
        nova=key.replace('/candidata/','/astra/');carteiras[nova]=resumo
        vinculos[nova]={'herdada':True,'pasta':(origem/'carteiras'/key).relative_to(RAIZ).as_posix()}
        a=ler_json(origem/'carteiras'/key/'auditoria.json');assert a['status']=='conferido'
        assert math.isclose(a['capital_final'],resumo['capital_final'],rel_tol=1e-12)
    assert len(carteiras)==216
    novos=0
    for b in FINAIS:
        for s in SEEDS:
            q=previsoes[b,'crua',s][COLUNAS]
            for pol in ['smart','diaria24']:
                for custo in ['ideal','base','agravado']:
                    resumo,ordens,curva,diarios,sinais=simular(q,minutos,primeiro,cfg,pol,custo)
                    audit=conferir(q,minutos,primeiro,cfg,pol,custo,resumo,ordens,diarios)
                    key=f'{b}/crua/{s}/{pol}/{custo}';d=dest/'carteiras'/key;d.mkdir(parents=True)
                    for nome,valor in [('resumo',resumo),('ordens',ordens),('sinais',sinais),('auditoria',audit)]:salvar_json(d/f'{nome}.json',valor)
                    curva.to_parquet(d/'curva.parquet',index=False);diarios.to_parquet(d/'diarios.parquet',index=False)
                    carteiras[key]=resumo;vinculos[key]={'herdada':False,'pasta':d.relative_to(RAIZ).as_posix()};novos+=1
                    salvar_json(p/'progresso_publicacao.json',{'utc':agora(),'novas':novos,'novas_total':192,'herdadas':216,'total':408})
    assert novos==192 and len(carteiras)==408 and recargas==64
    op={}
    for b in FINAIS:
        op[b]={}
        for v in ['astra','crua']:
            for pol in ['smart','diaria24']:
                for custo in ['ideal','base','agravado']:
                    rs=[carteiras[f'{b}/{v}/{s}/{pol}/{custo}'] for s in SEEDS]
                    op[b][f'{v}/{pol}/{custo}']={k:float(np.mean([r[k] for r in rs])) for k in
                        ['retorno_liquido','drawdown_minuto_close','exposicao_media','comissoes_usdt','slippage_usdt','ordens_executadas']}
    resultado={'utc':agora(),'execucao':ptr,'receitas':{'astra':ASTRA,'crua':CRUA},'series':series,
       'medias_por_bloco':metricas,'medias_globais':globais,'contrastes':contrastes,
       'carteiras':carteiras,'vinculos_carteiras':vinculos,'medias_operacionais':op,
       'limites':['2024/2025 conhecidos; comparacao retrospectiva, sem novo holdout.',
                 'Duas mudancas simultaneas: representacao e contexto. Nao isola efeito individual.',
                 'Medias de oito modelos individuais por bloco; nao ensemble.',
                 'Carteiras independentes, sem compor retornos dos quatro blocos.',
                 'Intervalos condicionais nao corrigem a selecao previa de receitas.',
                 'Sem novas consultas Astra, busca de configuracoes ou promocao automatica.']}
    salvar_json(dest/'resultados.json',resultado)
    linhas=['# Candidata Astra versus OHLCV cru + Huber','','Execução `'+ptr['id']+'`. Mesmos dados, executor científico e oito seeds/quatro blocos.32Astra herdados;32crus novos;dois controles excluídos das médias.','',
            '| Versão | MSE médio teste | RMSE médio | MAE médio |','|---|---:|---:|---:|']
    for v,q in globais.items():linhas.append(f"| {v} | {q['mse']:.10f} | {q['rmse']:.7f} | {q['mae']:.7f} |")
    linhas+=['','## Incerteza','','Diferença negativa favorece o primeiro modelo. IC98,333% ajustado para três contrastes; bootstrap pareado de seeds/dias14.','',
             '| Contraste | Diferença MSE | IC ajustado |','|---|---:|---|']
    for nome,q in contrastes.items():linhas.append(f"| {nome} | {q['diferenca_mse']:.9g} | {q['intervalos']['14']['ic98_333_bonferroni_tres_contrastes']} |")
    linhas+=['','## Operação: média das oito seeds, custos base','','| Bloco | Smart Astra | Smart crua | Diária Astra | Diária crua |','|---|---:|---:|---:|---:|']
    for b in FINAIS:
        vals=[op[b][f'{v}/{pol}/base']['retorno_liquido'] for pol in ['smart','diaria24'] for v in ['astra','crua']]
        linhas.append('| '+b+' | '+' | '.join(f'{100*x:+.2f}%' for x in vals)+' |')
    linhas+=['','192carteiras novas,216herdadas; custos e políticas inalterados. Smart mantém posição; parâmetro2% não é stop-loss. Naive mantém caixa nessas políticas.','',*resultado['limites'],'',
        '[Dados completos](../'+dest.relative_to(RAIZ).as_posix()+'/resultados.json).']
    texto='\n'.join(linhas)+'\n';(dest/'relatorio.md').write_text(texto,encoding='utf-8')
    salvar_json(dest/'manifesto.json',{'arquivos':{q.relative_to(dest).as_posix():sha256(q) for q in dest.rglob('*') if q.is_file()}})
    salvar_json(p/'publicacao.json',{'utc':agora(),'pasta':dest.relative_to(RAIZ).as_posix(),'manifesto_sha256':sha256(dest/'manifesto.json'),'simulacoes_novas':192,'simulacoes_herdadas':216})
    doc=RAIZ/'docs/resultados_comparacao_astra_crua.md'
    if not doc.exists():doc.write_text(texto,encoding='utf-8')
