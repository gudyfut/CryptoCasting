"""Comparação pareada predefinida; separa herança, novos ajustes e simulação."""
from pathlib import Path
import numpy as np
import pandas as pd
from previsao24.arquivos import RAIZ,agora,ler_json,salvar_json,sha256,identidade,verificar_arquivos
from previsao24.configuracao import FOLDS
from previsao24.metricas import calcular
from previsao24.financeiro import simular
from manutencao.consolidar_resultados import diario,intervalo_blocos,curva_publicada
from .ciclo import indice


def perto(a,b):
    if a is None or b is None:
        if a is not b: raise ValueError('Ausência convertida em valor.')
    else: np.testing.assert_allclose(a,b,rtol=1e-10,atol=1e-12)


def auditar_financeiro(q,minutos,primeiro,c,r,ordens):
    p=c['operacao']; t=q['origem_utc']
    limiar=np.log((1+p['slippage'])*(1+p['taxa'])/((1-p['slippage'])*(1-p['taxa'])))
    previstos=q.loc[(t.dt.hour==p['hora_utc'])&(t.dt.minute==0)&(q['previsao']>limiar),'origem_utc'].map(lambda v:v.isoformat()).tolist()
    if previstos!=[o['origem_utc'] for o in ordens]: raise ValueError('Ordens diferentes dos sinais causais.')
    capital=p['capital']; custos=0.; agravado=r['cenario']!='base'
    taxa=p['taxa_agravada'] if agravado else p['taxa']; s=p['slippage_agravado'] if agravado else p['slippage']
    for o in ordens:
        perto(o['capital_entrada'],capital)
        entrada=int(pd.Timestamp(o['origem_utc']).timestamp()//60)+p['latencia_minutos']; saida=entrada+1440
        if o['entrada_minuto']!=entrada or o['saida_minuto']!=saida: raise ValueError('Horário incorreto.')
        a,b=entrada-primeiro,saida-primeiro
        valido=0<=a<b<len(minutos) and np.isfinite(minutos[[a,b],0]).all() and (minutos[[a,b],5]>0).all()
        if capital is None or not valido:
            if o['status']!='nao_auditavel' or o['capital_saida'] is not None: raise ValueError('Ausência omitida.')
            capital=None; continue
        if o['status']!='pontas_observadas' or o['preco_entrada']!=float(minutos[a,0]) or o['preco_saida']!=float(minutos[b,0]): raise ValueError('Preço de execução divergente.')
        quantidade=capital/(minutos[a,0]*(1+s)*(1+taxa)); novo=quantidade*minutos[b,0]*(1-s)*(1-taxa)
        custo=capital-quantidade*minutos[a,0]+quantidade*minutos[b,0]-novo
        perto(o['quantidade'],quantidade); perto(o['capital_saida'],novo); perto(o['custos'],custo); perto(o['retorno_liquido'],novo/capital-1)
        capital=novo; custos+=custo
    perto(r['capital_final'],capital); perto(r['custos_observados'],custos)
    perto(r['retorno_liquido'],capital/p['capital']-1 if capital is not None else None)
    if r['entradas_planejadas']!=len(ordens): raise ValueError('Contagem financeira divergente.')
    return len(ordens)


def consolidar(destino):
    e=ler_json(destino/'execucao.json'); c=e['assinatura']['configuracao_treino']
    base=RAIZ/e['referencia_caminho']; dados=RAIZ/e['dataset_caminho']; manifesto=ler_json(dados/'dataset.json')
    novos=indice(destino); antigos=indice(base)
    if len(novos)!=384 or len(antigos)!=832: raise ValueError('Grade incompleta.')
    publicacoes=[]
    for fase in ('desenvolvimento','avaliacao'):
        if not (destino/f'{fase}_concluido.json').exists(): raise ValueError('Fase incompleta.')
        folds=c['folds_desenvolvimento'] if fase=='desenvolvimento' else c['folds_avaliacao']
        pasta=destino/'analises'/fase
        if (pasta/'publicacao.json').exists():
            p=ler_json(pasta/'publicacao.json'); verificar_arquivos(pasta,p['arquivos']); publicacoes.append(ler_json(pasta/'resumo.json')); continue
        pasta.mkdir(parents=True,exist_ok=True)
        registros={}; linhas=[]; fontes={}
        for variante,origem in (('herdado',antigos),('corrigido',novos)):
            for local in origem.values():
                x=ler_json(local/'tentativa.json')['celula']
                if x['fold'] not in folds: continue
                nome='mamba_corrigido' if variante=='corrigido' else 'mamba_original' if x['modelo']=='mamba' else x['modelo']
                auditoria=ler_json(local/'auditoria.json'); verificar_arquivos(local,auditoria['arquivos'])
                fontes[local.relative_to(RAIZ).as_posix()]=sha256(local/'auditoria.json')
                q=pd.read_parquet(local/'previsoes_teste.parquet'); metrica=calcular(q['alvo'],q['previsao'])
                r=ler_json(local/'resultado.json')
                for k,v in metrica.items(): perto(v,r['metricas']['teste'][k])
                erro=q['previsao'].to_numpy()-q['alvo'].to_numpy(); perto(np.dot(erro,erro)/len(erro),metrica['mse'])
                chave=(x['par'],x['fold'],x.get('contexto'),x.get('seed'),nome)
                if chave in registros: raise ValueError('Resultado duplicado.')
                registros[chave]=(q,local,r)
                linhas.append({**x,'modelo':nome,'origem_resultado':variante,**metrica,'epoca':r.get('epoca_selecionada'),'epocas_executadas':r.get('epocas_executadas'),'segundos':r.get('segundos'),'parametros':r.get('parametros')})
        if len(linhas)!=608: raise ValueError('Esperados 416 herdados + 192 corrigidos por fase.')
        pd.DataFrame(linhas).to_csv(pasta/'metricas_por_ajuste.csv',index=False)
        modelos=('mamba_original','mamba_corrigido','lstm','arima','naive'); escores={}; tempos={}; medias=[]; pares=[]
        for fold in folds:
            for par in c['pares']:
                for w in c['contextos']:
                    for nome in modelos:
                        itens=[registros[par,fold,w,s,nome] for s in c['seeds']] if nome in modelos[:3] else [registros[par,fold,None,None,nome]]
                        q=itens[0][0]
                        if fold in tempos: pd.testing.assert_series_equal(tempos[fold],q['origem_utc'])
                        tempos[fold]=q['origem_utc']
                        controle=registros[par,fold,w,c['seeds'][0],'mamba_original'][0]
                        for b,_,_ in itens:
                            pd.testing.assert_frame_equal(b.drop(columns='previsao'),controle.drop(columns='previsao'))
                        escores[par,fold,w,nome]=np.mean([(b.previsao.to_numpy()-b.alvo.to_numpy())**2 for b,_,_ in itens],axis=0)
                        media={k:float(np.mean([r['metricas']['teste'][k] for _,_,r in itens])) for k in ('mse','mae','habilidade_mse','vies','acuracia_direcional','acerto_balanceado_direcional')}
                        medias.append({'par':par,'fold':fold,'contexto':w,'modelo':nome,**media,'rmse':float(np.sqrt(media['mse']))})
                    for seed in c['seeds']:
                        _,_,a=registros[par,fold,w,seed,'mamba_original']; _,_,b=registros[par,fold,w,seed,'mamba_corrigido']
                        m0=a['metricas']['teste']['mse']; m1=b['metricas']['teste']['mse']
                        pares.append({'par':par,'fold':fold,'contexto':w,'seed':seed,'mse_original':m0,'mse_corrigido':m1,'diferenca':m1-m0,'variacao_relativa':m1/m0-1,'epoca_original':a['epoca_selecionada'],'epoca_corrigida':b['epoca_selecionada']})
        quadro=pd.DataFrame(medias); pd.DataFrame(pares).to_csv(pasta/'comparacoes_pareadas.csv',index=False); quadro.to_csv(pasta/'metricas_medias_seeds.csv',index=False)
        globais=[]
        for nome in modelos:
            q=quadro[quadro.modelo==nome]
            m={k:float(q[k].mean()) for k in ('mse','mae','habilidade_mse','vies','acuracia_direcional','acerto_balanceado_direcional')}
            globais.append({'modelo':nome,**m,'rmse':float(np.sqrt(m['mse']))})
        contrastes=[]
        for nome in ('mamba_original','lstm','naive','arima'):
            dias=[]; valores=[]
            for fold in folds:
                delta=np.mean([escores[p,fold,w,'mamba_corrigido']-escores[p,fold,w,nome] for p in c['pares'] for w in c['contextos']],axis=0)
                dias.append(diario(tempos[fold],delta,fold)); valores.append(float(delta.mean()))
            contraste={'referencia':nome,'diferenca_mse':float(np.mean(valores)),
                       'intervalos':[intervalo_blocos(dias,d,c['bootstrap']['replicas'],c['bootstrap']['seed']) for d in c['bootstrap']['dias']]}
            g={x['modelo']:x['mse'] for x in globais}; perto(contraste['diferenca_mse'],g['mamba_corrigido']-g[nome])
            contraste['variacao_relativa']=g['mamba_corrigido']/g[nome]-1; contrastes.append(contraste)
        contextos=[]
        for nome in modelos[:2]:
            for w in c['contextos'][1:]:
                dias=[]; valores=[]
                for fold in folds:
                    delta=np.mean([escores[p,fold,24,nome]-escores[p,fold,w,nome] for p in c['pares']],axis=0)
                    dias.append(diario(tempos[fold],delta,fold)); valores.append(float(delta.mean()))
                contextos.append({'modelo':nome,'contexto_comparado':w,'diferenca_mse':float(np.mean(valores)),
                                 'intervalos':[intervalo_blocos(dias,d,c['bootstrap']['replicas'],c['bootstrap']['seed']) for d in c['bootstrap']['dias']]})
        estabilidade=[]; tabela=pd.DataFrame(linhas)
        for nome in modelos[:3]:
            q=tabela[tabela.modelo==nome]; por_seed=[{'seed':int(s),'mse':float(g.mse.mean())} for s,g in q.groupby('seed')]
            estabilidade.append({'modelo':nome,'por_seed':por_seed,'desvio_mse':float(np.std([s['mse'] for s in por_seed]))})
        grupos={f:quadro.groupby(['modelo',f])[['mse','mae','habilidade_mse']].mean().reset_index().to_dict('records') for f in ('par','contexto','fold')}
        financeiro=[]; ordens_conferidas=0
        anterior=ler_json(RAIZ/'registros/analises'/e['assinatura']['referencia']/fase/'resumo.json')
        for par in c['pares']:
            minutos=np.load(dados/par/'minutos.npy',mmap_mode='r')
            for w in c['contextos']:
                for seed in c['seeds']:
                    trechos=[]
                    for fold in folds:
                        _,local,_=registros[par,fold,w,seed,'mamba_corrigido']
                        q=pd.read_parquet(local/'previsoes_operacional.parquet')
                        q=q.loc[(q.origem_utc+pd.Timedelta(hours=24,minutes=1))<pd.Timestamp(FOLDS[fold][2],tz='UTC')]; trechos.append(q)
                    operacionais=pd.concat(trechos,ignore_index=True)
                    for agravado in (False,True):
                        r,ordens,curva=simular(operacionais,minutos,manifesto['primeiro_minuto'],FOLDS[folds[-1]][2],c['operacao'],agravado=agravado)
                        ordens_conferidas+=auditar_financeiro(operacionais,minutos,manifesto['primeiro_minuto'],c,r,ordens)
                        original=[v for v in anterior['financeiro'] if v['modelo']=='mamba' and v['par']==par and v['contexto']==w and v['seed']==seed and v['cenario']==r['cenario']]
                        if len(original)!=1: raise ValueError('Par financeiro não encontrado.')
                        arquivo=f'operacoes/{par}_W{w}_S{seed}_{r["cenario"]}.json'
                        item={'par':par,'contexto':w,'seed':seed,'modelo':'mamba_corrigido',**r,'retorno_original':original[0]['retorno_liquido'],'arquivo':arquivo}
                        item['diferenca_retorno']=r['retorno_liquido']-original[0]['retorno_liquido'] if r['retorno_liquido'] is not None and original[0]['retorno_liquido'] is not None else None
                        salvar_json(pasta/arquivo,{'estrategia':item,'ordens':ordens,'curva':curva_publicada(curva,c,folds)})
                        financeiro.append(item)
            del minutos
        pd.DataFrame(financeiro).to_csv(pasta/'financeiro.csv',index=False)
        resumo={'fase':fase,'classificacao':'retrospectiva_periodos_expostos','execucao':e['id'],'referencia':e['assinatura']['referencia'],'utc':agora(),
                'ajustes_novos':192,'resultados_herdados':416,'modelos':globais,'contrastes':contrastes,'contextos':contextos,'grupos':grupos,
                'estabilidade':estabilidade,'financeiro':financeiro,'fontes':fontes,'pares':pares,'ordens_conferidas':ordens_conferidas,
                'codigo_analise_sha256':sha256(Path(__file__))}
        salvar_json(pasta/'resumo.json',resumo)
        arquivos={p.relative_to(pasta).as_posix():sha256(p) for p in sorted(pasta.rglob('*')) if p.is_file() and p.name not in ('publicacao.json','auditoria.json')}
        salvar_json(pasta/'publicacao.json',{'utc':agora(),'arquivos':arquivos})
        salvar_json(pasta/'auditoria.json',{'status':'aprovado','utc':agora(),'resultados':len(linhas),'pares':len(pares),'cenarios_financeiros':len(financeiro),'ordens_conferidas':ordens_conferidas,'publicacao_sha256':sha256(pasta/'publicacao.json'),
                                          'escopo':'Artefatos e alinhamento, MSE independente, igualdade das médias/contrastes, sinais/horários/preços e contabilidade financeira. Intervalos seguem implementação congelada já verificada; diagnósticos retrospectivos.'})
        publicacoes.append(resumo)
        print(f'PUBLICADO {fase}: 192 novos, 416 herdados, {ordens_conferidas} ordens conferidas.',flush=True)
    escrever_relatorio(destino,publicacoes)


def escrever_relatorio(destino,publicacoes):
    e=ler_json(destino/'execucao.json')
    linhas=['# Resultados do experimento de penalização do Mamba','',
            f'Execução `{e["id"]}`. Referência preservada `{e["assinatura"]["referencia"]}`. Relatório gerado em {agora()} (UTC).',
            '', 'Estudo retrospectivo pareado em períodos já consultados. A única intervenção é retirar weight decay dos parâmetros marcados pelo Mamba. Foram 384 ajustes corrigidos; LSTM, ARIMA, Naive e os Mamba originais são referências herdadas. Dois controles originais foram reexecutados para conferência de reprodução e não contam como novos pares independentes.',
            '', 'A confirmação de preservação antes/depois fica em `preservacao_depois.json` na pasta desta execução; o estado global está em `progresso.json`. A existência deste relatório indica consolidação das duas fases, não substitui o recibo de fechamento.',
            '', 'Protocolo: [experimento controlado](protocolo_penalizacao_mamba.md). A mudança não garante melhora nem rentabilidade.']
    for a in publicacoes:
        linhas+=['',f'## {"Desenvolvimento de 2023" if a["fase"]=="desenvolvimento" else "Avaliação retrospectiva de 2024–2025"}','',
                 '| Modelo | MSE médio | RMSE × 100 | MAE × 100 |','|---|---:|---:|---:|']
        for m in a['modelos']: linhas.append(f'| {m["modelo"]} | {m["mse"]:.10f} | {100*m["rmse"]:.4f} | {100*m["mae"]:.4f} |')
        linhas+=['','MSE menor indica menor erro quadrático. RMSE/MAE ×100 estão em pontos de log-retorno, não em acurácia. As seeds são médias de escores, não um ensemble.','',
                 '| Comparação do corrigido com | Diferença MSE | Variação relativa | IC 95% de 14 dias |','|---|---:|---:|---|']
        for k in a['contrastes']:
            ic=next(i for i in k['intervalos'] if i['dias']==14)
            linhas.append(f'| {k["referencia"]} | {k["diferenca_mse"]:.10g} | {100*k["variacao_relativa"]:+.4f}% | [{ic["inferior"]:.10g}; {ic["superior"]:.10g}] |')
        principal=a['contrastes'][0]; ic=next(i for i in principal['intervalos'] if i['dias']==14)
        leitura='favorece a correção' if ic['superior']<0 else 'favorece o original' if ic['inferior']>0 else 'inclui zero e não distingue claramente as duas políticas'
        linhas+=['',f'O intervalo principal {leitura}. A diferença é corrigido menos referência: negativa favorece o corrigido. Os contrastes com outras famílias são secundários. Intervalos condicionais aos modelos e períodos, com 2.000 reamostragens de blocos; sensibilidades de sete e 28 dias constam do JSON.']
        base=[v for v in a['financeiro'] if v['cenario']=='base' and v['retorno_liquido'] is not None]
        if base: linhas+=['',f'Na simulação Spot com custos base, {len(base)} estratégias tiveram retorno auditável. Mediana corrigida: {100*float(np.median([v["retorno_liquido"] for v in base])):.2f}%; mediana dos pares originais: {100*float(np.median([v["retorno_original"] for v in base if v["retorno_original"] is not None])):.2f}%. Estratégias correlacionadas, sem carteira combinada e sem escolha retrospectiva da vencedora.']
        caminho=(destino/'analises'/a['fase']).relative_to(RAIZ).as_posix()
        linhas+=['',f'Evidências: `{caminho}/resumo.json`, `comparacoes_pareadas.csv`, `metricas_por_ajuste.csv`, `financeiro.csv`, `publicacao.json` e `auditoria.json`.']
    linhas+=['','## Limites da conclusão','',
             'A correção mantém arquitetura, entrada, dados, partições, seeds e regra de seleção de época. A época selecionada pode mudar como consequência do tratamento. Não houve busca adicional. Comparações por moeda, contexto e seed são exploratórias e estão integralmente reportadas nos arquivos, sem seleção de subconjuntos favoráveis.',
             '', 'Os resultados de 2024–2025 já haviam sido vistos quando esta hipótese foi definida. Congelar a extensão não desfaz essa exposição; uma nova alegação confirmatória requer dados não usados nas decisões. Este experimento não mede a melhor configuração possível de Mamba/LSTM nem certifica execução financeira real.']
    (RAIZ/'docs/resultados_penalizacao_mamba.md').write_text('\n'.join(linhas)+'\n',encoding='utf-8')
