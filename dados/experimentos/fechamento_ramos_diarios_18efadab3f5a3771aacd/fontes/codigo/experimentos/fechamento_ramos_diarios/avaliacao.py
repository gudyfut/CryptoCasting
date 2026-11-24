"""Mesmo método aprovado, generalizado por símbolo e pelas quatro células fixas."""
from copy import deepcopy
import io
import json
import zipfile
import numpy as np
from infraestrutura.artefatos import RAIZ, salvar_json, ler_json, agora, sha256
from experimentos.alvo_retorno_diario.metricas import metricas_retorno
from .contratos import receita, organizar


def medir(y, p):
    y,p=np.asarray(y,np.float64),np.asarray(p,np.float64)
    m=metricas_retorno(y,p)
    ativo=p!=0;alta=y>0;queda=y<0
    recalls=[float(np.mean(p[alta]>0)) if alta.any() else None,
             float(np.mean(p[queda]<0)) if queda.any() else None]
    m.update(desvio_previsao=float(p.std()),desvio_real=float(y.std()),
             fracao_previsao_alta=float(np.mean(p>0)),fracao_previsao_queda=float(np.mean(p<0)),
             fracao_abstencao=float(np.mean(~ativo)),
             recall_alta=recalls[0],recall_queda=recalls[1],
             acerto_balanceado=float(np.mean(recalls)) if ativo.any() and all(v is not None for v in recalls) else None,
             correlacao=float(np.corrcoef(y,p)[0,1]) if y.std()>0 and p.std()>0 else None)
    if not ativo.any():
        m['acerto_sinal']=None
    return m


def agregar(metricas):
    resultado={}
    for k in metricas[0]:
        valores=[m[k] for m in metricas]
        if all(isinstance(v,(int,float)) for v in valores):
            resultado[k]={'media':float(np.mean(valores)),
                          'desvio_seeds':float(np.std(valores,ddof=1)),
                          'minimo':float(min(valores)),'maximo':float(max(valores))}
        else:resultado[k]={'media':None,'limite':'Pelo menos uma seed sem medida definida.'}
    return resultado


def ajustar_linear(dados, grade):
    treino=dados['treino'];validacao=dados['validacao']
    x=treino['x'].reshape(len(treino['y']),-1).astype(np.float64);y=treino['y']
    xv=validacao['x'].reshape(len(validacao['y']),-1).astype(np.float64)
    media=x.mean(axis=0);base=float(y.mean());xc=x-media;yc=y-base
    candidatos=[];coeficientes=[]
    for penalizacao in grade:
        coef=np.linalg.solve(xc.T@xc/len(x)+penalizacao*np.eye(x.shape[1]),xc.T@yc/len(x))
        erro=float(np.mean(((xv-media)@coef+base-validacao['y'])**2))
        candidatos.append({'lambda':penalizacao,'mse_validacao':erro});coeficientes.append(coef)
    melhor=min(range(len(grade)),key=lambda i:candidatos[i]['mse_validacao'])
    return {'lambda':grade[melhor],'coeficientes':coeficientes[melhor].tolist(),
            'media_x':media.tolist(),'media_y':base,'candidatos':candidatos,
            'objetivo':'MSE_medio+lambda_norma2; intercepto não penalizado',
            'selecao':'validação; primeiro em empate; nenhum teste acessado'}


def prever_linear(x, ajuste):
    return (x.reshape(len(x),-1).astype(np.float64)-ajuste['media_x'])@np.asarray(ajuste['coeficientes'])+ajuste['media_y']


def intervalo(diferencas, bloco, cfg, reamostrar_seeds):
    a=np.asarray(diferencas,dtype=np.float64)
    if a.ndim==1:a=a[None,:]
    assert np.isfinite(a).all() and a.shape[1]>=bloco
    rng=np.random.default_rng(cfg['seed']);n=a.shape[1];replicas=[]
    for _ in range(cfg['replicas']):
        ids=(rng.integers(0,n-bloco+1,int(np.ceil(n/bloco)))[:,None]+np.arange(bloco)).ravel()[:n]
        seeds=rng.integers(0,len(a),len(a)) if reamostrar_seeds else np.arange(len(a))
        replicas.append(float(a[seeds][:,ids].mean()))
    return {'media':float(a.mean()),'ic95':np.quantile(replicas,[.025,.975]).tolist(),
            'bloco':bloco,'replicas':cfg['replicas'],'reamostrar_seeds':reamostrar_seeds}


def contrastar(matrizes, referencias, cfg, ensemble):
    contrastes={}
    for nome,pesos in cfg['contrastes'].items():
        dif=sum(peso*matrizes[variante] for variante,peso in pesos.items())
        contrastes[nome]={str(b):intervalo(dif,b,cfg['bootstrap'],not ensemble) for b in cfg['bootstrap']['blocos']}
    for variante,a in matrizes.items():
        for ref,b in referencias.items():
            contrastes[f'{variante}_menos_{ref}']={str(bl):intervalo(a-b,bl,cfg['bootstrap'],not ensemble) for bl in cfg['bootstrap']['blocos']}
    return contrastes


def executar(p,c,dados,f,progresso):
    import torch
    from .treinamento import carregar_rede,inferir
    from experimentos.sem_penalizacao_diaria.observacao import observar
    from experimentos.generalizacao_moedas.avaliacao import carregar_mercado
    from simulacao_operacoes.continuidade_diaria.simulador import simular
    from simulacao_operacoes.continuidade_diaria.auditoria_grade import conferir
    pub=p/'publicacao';pub.mkdir(exist_ok=False);(pub/'previsoes').mkdir()
    previsoes={'validacao':{},'teste':{}};precos={'validacao':{},'teste':{}}
    metricas={fase:{} for fase in previsoes}
    caminhos=ler_json(p/'modelos.json')
    for variante in c['variantes']:
        cfg=receita(c,variante);adaptado=organizar(dados,cfg['eixo'])
        for seed in c['seeds']:
            chave=f'{variante}_{seed}';ajuste=RAIZ/caminhos[chave]['pasta']
            rede=carregar_rede(ajuste,cfg)
            observar(rede,adaptado['treino']['x'],pub/'observacoes'/f'{chave}.json',ler_json(ajuste/'selecao.json')['epoca'])
            for fase in previsoes:
                z=dados[fase];ret=inferir(rede,adaptado[fase]['x']);preco=z['ultimo_close']*(1+ret)
                if fase=='validacao':np.testing.assert_array_equal(ret,np.load(ajuste/'validacao.npz')['previsoes'])
                if chave in f['modelos']:
                    antigo=RAIZ/f['modelos'][chave]['previsoes'][fase]
                    with np.load(antigo) as q:
                        for k in ('origens_ms','ultimo_close','fim_alvo_ms'):np.testing.assert_array_equal(z[k],q[k])
                        np.testing.assert_array_equal(z['y'],q['alvo_retorno'])
                        np.testing.assert_array_equal(ret,q['previsoes_retorno']);np.testing.assert_array_equal(preco,q['previsoes'])
                previsoes[fase][chave]=ret;precos[fase][chave]=preco;metricas[fase][chave]=medir(z['y'],ret)
            del rede;torch.cuda.empty_cache()
    ajuste_linear=ajustar_linear({k:dados[k] for k in ('treino','validacao')},c['linear']['lambdas'])
    repeticao=ajustar_linear({k:dados[k] for k in ('treino','validacao')},c['linear']['lambdas'])
    assert ajuste_linear==repeticao
    salvar_json(pub/'linear.json',dict(ajuste_linear,controle_exato=True))
    medias={};ensembles={};contrastes_previsao={}
    for fase in previsoes:
        z=dados[fase];medias[fase]={};ensembles[fase]={}
        for variante in c['variantes']:
            nome=f'{variante}_ensemble'
            # Exatamente a convenção operacional preservada: média de preços.
            precos[fase][nome]=np.mean([precos[fase][f'{variante}_{s}'] for s in c['seeds']],axis=0)
            previsoes[fase][nome]=precos[fase][nome]/z['ultimo_close']-1
            metricas[fase][nome]=medir(z['y'],previsoes[fase][nome])
            medias[fase][variante]=agregar([metricas[fase][f'{variante}_{s}'] for s in c['seeds']])
            ensembles[fase][variante]=metricas[fase][nome]
        previsoes[fase]['naive']=np.zeros(len(z['y']),dtype=np.float64)
        previsoes[fase]['linear']=prever_linear(z['x'],ajuste_linear)
        for ref in ('naive','linear'):
            precos[fase][ref]=z['ultimo_close']*(1+previsoes[fase][ref]);metricas[fase][ref]=medir(z['y'],previsoes[fase][ref])
        for nome,ret in previsoes[fase].items():
            np.savez_compressed(pub/'previsoes'/f'{fase}_{nome}.npz',previsoes_retorno=ret,previsoes=precos[fase][nome],
                                alvo_retorno=z['y'],origens_ms=z['origens_ms'],ultimo_close=z['ultimo_close'],fim_alvo_ms=z['fim_alvo_ms'])
        referencias={r:(previsoes[fase][r]-z['y'])**2 for r in ('naive','linear')}
        individuais={v:np.array([(previsoes[fase][f'{v}_{s}']-z['y'])**2 for s in c['seeds']]) for v in c['variantes']}
        combinados={v:(previsoes[fase][f'{v}_ensemble']-z['y'])**2 for v in c['variantes']}
        contrastes_previsao[fase]={'medias_individuais':contrastar(individuais,referencias,c,False),
                                   'ensemble':contrastar(combinados,referencias,c,True)}
    salvar_json(pub/'previsao.json',{'individuais_e_referencias':metricas,'medias_seeds':medias,
                                    'ensemble':ensembles,'contrastes_mse':contrastes_previsao})
    mercado=carregar_mercado(f['mercado_minuto'])
    antigo=ler_json(RAIZ/f['continuidade']['pasta']/'resultados.json')
    carteiras=[];auditorias=[];reproducoes=[];curvas={};falhas=[]
    with zipfile.ZipFile(pub/'carteiras.zip','x',compression=zipfile.ZIP_DEFLATED) as arquivo:
        for fase in previsoes:
            z=dados[fase]
            for nome,prev in precos[fase].items():
                for custo,slippage in enumerate(c['slippage_cenarios'],1):
                    regras=deepcopy(c['operacoes']);regras['slippage_por_lado']=slippage
                    ident=f'{fase}/{nome}/custo_{custo}'
                    try:
                        resultado,curva=simular(z['origens_ms'],prev,z['ultimo_close'],mercado,regras,'liquida')
                    except ValueError as erro:
                        if 'Violação prudencial' not in str(erro):raise
                        falhas.append({'identidade':ident,'erro':str(erro),'retorno':None})
                        arquivo.writestr(ident+'/falha.json',json.dumps(falhas[-1],ensure_ascii=False));continue
                    auditoria=conferir(resultado,curva,mercado,regras,'liquida',z['origens_ms'],prev,z['ultimo_close'],None)
                    if nome.startswith('A_') or nome=='naive':
                        unidade=nome.removeprefix('A_')
                        esperado=next(r for r in antigo['resultados'] if r['moeda']==c['simbolo'] and r['fase']==fase and r['unidade']==unidade and r['custo']==custo and r['modo']=='liquida')
                        for k,v in esperado['metricas'].items():
                            if v is None:assert resultado['metricas'][k] is None
                            else:np.testing.assert_allclose(resultado['metricas'][k],v,atol=1e-7,rtol=1e-10,err_msg=ident+'/'+k)
                        with zipfile.ZipFile(RAIZ/f['continuidade']['pasta']/'carteiras.zip') as orig:
                            q=np.load(io.BytesIO(orig.read(esperado['membro']+'/curva.npz')))
                            np.testing.assert_allclose(curva['saldos_diarios'],q['saldos_diarios'],atol=1e-7,rtol=1e-10)
                        reproducoes.append(ident)
                    resultado['regras']=regras
                    arquivo.writestr(ident+'/resultado.json',json.dumps(resultado,ensure_ascii=False,allow_nan=False))
                    memoria=io.BytesIO();np.savez_compressed(memoria,origens_ms=z['origens_ms'],**curva)
                    arquivo.writestr(ident+'/curva.npz',memoria.getvalue())
                    carteiras.append({'fase':fase,'unidade':nome,'custo':custo,'membro':ident,'metricas':resultado['metricas']})
                    auditorias.append(dict(identidade=ident,**auditoria));curvas[(fase,nome,custo)]=curva['saldos_diarios']
                    progresso('avaliando',carteiras_concluidas=len(carteiras),carteiras_falhas=len(falhas))
    assert len(carteiras)+len(falhas)==c['carteiras_previstas']
    salvar_json(pub/'falhas_simulacao.json',falhas)
    salvar_json(pub/'auditoria_operacoes.json',{'auditorias':auditorias,'reproducoes_referencia':reproducoes,
                                             'total_reproducoes_previsto':30,'falhas':falhas})
    assert len(reproducoes)==30
    medias_operacoes={};ensemble_operacoes={};contrastes_operacoes={}
    for fase in previsoes:
        medias_operacoes[fase]={};ensemble_operacoes[fase]={};contrastes_operacoes[fase]={}
        for custo in range(1,4):
            chave=str(custo);medias_operacoes[fase][chave]={};ensemble_operacoes[fase][chave]={}
            for v in c['variantes']:
                linhas=[q['metricas'] for q in carteiras if q['fase']==fase and q['custo']==custo and q['unidade'] in [f'{v}_{s}' for s in c['seeds']]]
                medias_operacoes[fase][chave][v]=agregar(linhas) if len(linhas)==3 else {'incompleto':True}
                ensemble_operacoes[fase][chave][v]=next((q['metricas'] for q in carteiras if q['fase']==fase and q['custo']==custo and q['unidade']==f'{v}_ensemble'),None)
            nomes=list(previsoes[fase])
            if all((fase,n,custo) in curvas for n in nomes):
                logs={n:np.diff(np.log(curvas[(fase,n,custo)])) for n in nomes}
                referencias={r:logs[r] for r in ('naive','linear')}
                individuais={v:np.array([logs[f'{v}_{s}'] for s in c['seeds']]) for v in c['variantes']}
                combinados={v:logs[f'{v}_ensemble'] for v in c['variantes']}
                contrastes_operacoes[fase][chave]={'medias_individuais':contrastar(individuais,referencias,c,False),
                                                  'ensemble':contrastar(combinados,referencias,c,True)}
            else:contrastes_operacoes[fase][chave]={'incompleto':True,'motivo':'Falha prudencial preservada; sem excluir carteira da média.'}
    with zipfile.ZipFile(pub/'carteiras.zip') as arquivo:assert arquivo.testzip() is None
    salvar_json(pub/'operacoes.json',{'carteiras':carteiras,'falhas':falhas,'medias_seeds':medias_operacoes,
                                    'ensemble':ensemble_operacoes,'contrastes_log_diario':contrastes_operacoes,
                                    'limites':'2024 seleção;2025 retrospectivo. Ensemble fixo não reamostra seeds; IC exploratório sem correção da busca.'})
    salvar_json(pub/'conferencia.json',{'utc':agora(),'seeds_por_variante':3,'variantes':list(c['variantes']),
        'previsoes_por_fase':{k:len(v) for k,v in previsoes.items()},'carteiras_concluidas':len(carteiras),
        'carteiras_previstas':c['carteiras_previstas'],'falhas_prudenciais':len(falhas),
        'controle_linear_exato':True,'controle_financeiro_A_naive':len(reproducoes),'recargas_validacao_exatas':len(c['variantes'])*len(c['seeds']),
        'previsoes_herdadas_exatas_validacao_teste':len(f['modelos'])*2,'novos_dados2026':False})
    from .diagnostico import diagnosticar
    diagnosticar(p,c,dados)
    return {'carteiras_concluidas':len(carteiras),'falhas_prudenciais':len(falhas)}
