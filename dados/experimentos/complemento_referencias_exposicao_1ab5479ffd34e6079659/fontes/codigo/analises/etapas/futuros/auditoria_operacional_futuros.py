"""Conferência posterior de elegibilidade; não executa simulações nem treinos.

Implementa diretamente as regras do desenho, inclusive crescimento exatamente
zero (zero não é dado ausente). Compara o veredito às publicações do executor.
"""
from pathlib import Path
import numpy as np
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,agora,sha256


def conferir_contratos():
    """Confronta artefatos salvos; não importa o preparador nem o treinador."""
    import pandas as pd
    ptr=ler_json(RAIZ/'registros/operacional_futuros/execucao.json');p=RAIZ/ptr['pasta']
    jobs=ler_json(p/'ajustes.json');origens={};alvos={};escalas={};linhas=[]
    for j in jobs:
        if j['status']!='concluido':continue
        d=RAIZ/j['pasta'];c=ler_json(d/'contrato_dados.json');s=ler_json(d/'ajuste/escalas.json')
        conclusao=ler_json(d/'ajuste/conclusao.json');historico=ler_json(d/'ajuste/progresso.json')['historico']
        melhor=min(historico,key=lambda h:h['mse_validacao'])
        assert conclusao['epoca']==melhor['epoca'] and conclusao['recarga_exata']
        assert conclusao['epocas_executadas']==len(historico)
        assert np.isclose(conclusao['metricas']['validacao']['mse'],melhor['mse_validacao'],rtol=1e-12,atol=1e-15)
        familia=j['receita']['familia_alvo'];dim=1 if familia=='terminal' else 2
        assert c['dimensao_alvo']==dim and c['contexto']==j['receita']['contexto_horas']
        assert len(s['media_entrada'])==len(s['escala_entrada'])==len(c['canais'])
        assert len(s['media_alvo'])==len(s['escala_alvo'])==dim
        assert s['ultimo_candle_suporte_ms']<c['origens']['treino']['ultima_ms']
        anterior=None
        for fase,meta in c['origens'].items():
            chave_fase='avaliacao' if fase=='comparacao' and fase not in j['recorte'] else fase
            inicio,fim=[int(pd.Timestamp(t,tz='UTC').timestamp()*1000) for t in j['recorte'][chave_fase]]
            assert inicio<=meta['primeira_ms']<=meta['ultima_ms']
            assert meta['ultima_ms']+1442*60000<fim
            assert meta['ultima_ms']-meta['primeira_ms']==(meta['n']-1)*3600000
            if anterior is not None:assert anterior+1442*60000<meta['primeira_ms']
            anterior=meta['ultima_ms']
            if fase=='treino':continue
            z=np.load(d/'ajuste'/(fase+'.npz'))
            assert z['previsoes'].shape==z['alvos'].shape==(meta['n'],dim)
            assert np.isfinite(z['previsoes']).all() and np.isfinite(z['alvos']).all()
            assert np.array_equal(z['origens_ms'],np.arange(meta['primeira_ms'],meta['ultima_ms']+1,3600000))
            chave=(j['recorte']['id'],fase)
            if chave in origens:assert np.array_equal(origens[chave],z['origens_ms'])
            else:origens[chave]=z['origens_ms'].copy()
            chave_alvo=chave+(familia,tuple(j['receita']['barreiras_payoff']))
            if chave_alvo in alvos:assert np.array_equal(alvos[chave_alvo],z['alvos'])
            else:alvos[chave_alvo]=z['alvos'].copy()
        chave_escala=(j['recorte']['id'],familia,tuple(j['receita']['barreiras_payoff']))
        escala=(s['media_alvo'],s['escala_alvo'])
        if chave_escala in escalas:assert escala==escalas[chave_escala]
        else:escalas[chave_escala]=escala
        linhas.append({'job':j['id'],'controle':j['controle'],'canais':len(c['canais']),'dimensao_alvo':dim,'conferido':True})
    return {'utc':agora(),'execucao':ptr,'ajustes':linhas,'conferido':True,
        'criterio':'Checkpoint de menor MSE V, origens iguais, purga de 1442 minutos, dimensões finitas, alvos e escalas iguais entre receitas de mesma tarefa/barreiras; leitura sem novos ajustes.'}


def resumir_previsoes():
    """Diagnóstico descritivo posterior, sem alterar a seleção econômica."""
    ptr=ler_json(RAIZ/'registros/operacional_futuros/execucao.json');p=RAIZ/ptr['pasta']
    grupos={};linhas=[]
    for j in ler_json(p/'ajustes.json'):
        if j['status']!='concluido' or j['controle']:continue
        d=RAIZ/j['pasta']/'ajuste';z=np.load(d/'comparacao.npz');s=ler_json(d/'escalas.json')
        y=z['alvos'];pred=z['previsoes'];erro=pred-y
        r={'receita':j['receita_id'],'recorte':j['recorte']['id'],'seed':j['seed'],
           'familia':j['receita']['familia_alvo'],'n':len(y),'dimensao':y.shape[1],
           'mse':float(np.mean(erro**2)),'rmse':float(np.sqrt(np.mean(erro**2))),
           'mae':float(np.mean(abs(erro))),'mse_zero':float(np.mean(y**2)),
           'mse_media_treino':float(np.mean((y-np.array(s['media_alvo']))**2))}
        linhas.append(r);grupos.setdefault(j['receita_id'],[]).append(r)
    resumos=[]
    metricas=['mse','rmse','mae','mse_zero','mse_media_treino']
    for nome,rs in grupos.items():
        medias={k:float(np.mean([x[k] for x in rs])) for k in metricas}
        por_seed=[]
        for seed in sorted({x['seed'] for x in rs}):
            ls=[x for x in rs if x['seed']==seed]
            por_seed.append({'seed':seed,'celulas':len(ls),**{k:float(np.mean([x[k] for x in ls])) for k in metricas}})
        resumos.append({'receita':nome,'familia':rs[0]['familia'],'celulas':len(rs),'medias':medias,
            'habilidade_razao_mse_zero':1-medias['mse']/medias['mse_zero'],
            'habilidade_razao_mse_media_treino':1-medias['mse']/medias['mse_media_treino'],
            'por_seed':por_seed})
    return {'utc':agora(),'execucao':ptr,'conferido':True,'celulas':linhas,'resumos':resumos,
        'natureza':'Diagnóstico posterior, sem modificar gates. Média igual entre células concluídas; verificar cobertura antes de comparar. Não misturar MSE terminal com MSE de payoff; média de treino é controle descritivo adicional, sem operações novas.'}


def conferir_calibracao():
    import math
    ptr=ler_json(RAIZ/'registros/operacional_futuros/execucao.json');p=RAIZ/ptr['pasta'];coortes=[]
    for recibo in sorted((p/'avaliacoes').glob('*/*/*/politica_escolhida.json')):
        q=ler_json(recibo);d=recibo.parent;politicas=[];scores={}
        for politica in range(12):
            valores=[];motivos=[]
            for seed in q['seeds']:
                r=ler_json(d/'C'/str(seed)/str(politica)/'resultado.json');z=np.load(d/'C'/str(seed)/str(politica)/'curva.npz')
                e=z['patrimonio'];t=z['segundos_utc'];dias=(t[-1]-t[0])/86400
                dd=float(np.max(1-e/np.maximum.accumulate(e)))
                insolvente=bool((e<=0).any());g=None if insolvente else math.log(e[-1]/e[0])/dias
                calmar=None if g is None or dd<=1e-12 else math.expm1(365*g)/dd
                if r['metricas']['operacoes']<20: motivos.append(f'atividade_seed_{seed}')
                if insolvente or r['metricas']['saida_prudencial']: motivos.append(f'risco_seed_{seed}')
                if calmar is None: motivos.append(f'calmar_indefinido_seed_{seed}')
                valores.append({'seed':seed,'g':g,'calmar':calmar,'retorno':float(e[-1]/e[0]-1),
                                'giro':r['metricas']['giro'],'operacoes':r['metricas']['operacoes']})
            gs=[v['g'] for v in valores];gm=None if any(v is None for v in gs) else float(np.mean(gs))
            if gm is None or gm<=0:motivos.append('crescimento_medio_nao_positivo')
            if not motivos:
                scores[politica]=(float(np.median([v['calmar'] for v in valores])),gm,-float(np.mean([v['giro'] for v in valores])))
            politicas.append({'indice':politica,'motivos_reprovacao':motivos,'crescimento_log_medio':gm,
                'retorno_medio':float(np.mean([v['retorno'] for v in valores])),
                'minimo_operacoes_seed':min(v['operacoes'] for v in valores)})
        escolhida=None
        for i,s in scores.items():
            if escolhida is None or s[0]>scores[escolhida][0]+1e-10 or (abs(s[0]-scores[escolhida][0])<=1e-10 and s[1:]>scores[escolhida][1:]):
                escolhida=i
        if escolhida!=q['indice']:raise ValueError('Política publicada diverge da regra independente: '+str(d))
        coortes.append({'fase':d.parent.parent.name,'receita':q['receita'],'recorte':q['recorte'],
                       'escolhida':escolhida,'politicas':politicas,'coincide':True})
    return {'utc':agora(),'execucao':ptr,'coortes':coortes,'conferido':True,
            'natureza':'Recalcular métricas e decisão C, sem nova simulação ou alteração de critérios.'}


def conferir_curvas():
    from simulacao_operacoes.operacional.mercado import carregar
    ptr=ler_json(RAIZ/'registros/operacional_futuros/execucao.json');p=RAIZ/ptr['pasta']
    mercado,_=carregar(final=(p/'finalista_congelada.json').exists())
    total=0;ativas=0;maior=0.;pontos=0
    for raiz in ('avaliacoes','baselines'):
        for manifesto in sorted((p/raiz).rglob('manifesto.json')):
            cp=manifesto.parent;r=ler_json(cp/'resultado.json');z=np.load(cp/'curva.npz')
            calculada=[10000.];tempos=[float(z['segundos_utc'][0])]
            for tr in r['operacoes']:
                caixa=tr['caixa_antes']-.0005*tr['quantidade']*tr['preco_entrada']
                calculada.append(caixa);tempos.append(tr['entrada_ms']/1000)
                indices=np.arange(tr['entrada'],tr['saida']+(tr['motivo']!='tempo'))
                q=tr['quantidade'];pe=tr['preco_entrada'];s=tr['lado']
                f=np.zeros(len(indices))
                for evento in tr['eventos_funding']:
                    f[indices>=evento['indice']]+=q*evento['por_btc']
                bases=caixa+f
                # Implementação distinta: primeiro gera as duas colunas, depois intercala.
                colunas=np.column_stack([bases+q*s*(mercado.marca[indices,k]-pe)
                    for k in ((1,2) if s==1 else (2,1))])
                calculada.extend(colunas.ravel().tolist())
                tempos.extend(np.repeat(mercado.tempo[indices]/1000,2).tolist())
                calculada.append(tr['caixa_depois']);tempos.append(tr['saida_ms']/1000)
            calculada.append(r['metricas']['capital_final']);tempos.append(float(z['segundos_utc'][-1]))
            a=np.asarray(calculada);t=np.asarray(tempos)
            if a.shape!=z['patrimonio'].shape or not np.array_equal(t,z['segundos_utc']):
                raise ValueError('Dimensões/instantes da marcação divergem: '+str(cp))
            residuo=float(np.max(abs(a-z['patrimonio'])))
            if residuo>1e-7:raise ValueError('Patrimônio intraminuto diverge: '+str(cp))
            maior=max(maior,residuo);total+=1;pontos+=len(a);ativas+=bool(r['operacoes'])
    return {'utc':agora(),'execucao':ptr,'carteiras':total,'carteiras_ativas':ativas,'pontos_recalculados':pontos,
        'residuo_maximo_usdt':maior,'conferido':True,
        'limite':'Reconstrói o envelope conservador convencionado. Não transforma OHLC em ticks observados nem certifica liquidação Binance.'}


def conferir():
    ptr=ler_json(RAIZ/'registros/operacional_futuros/execucao.json');p=RAIZ/ptr['pasta'];linhas=[]
    for recibo in (p/'avaliacoes').glob('*/*/elegibilidade.json'):
        publicado=ler_json(recibo);fase=recibo.parent.parent.name
        r=[]
        for c in recibo.parent.glob('*/conclusao.json'):r+=ler_json(c)['linhas']
        base=[x for x in r if x['cenario']=='base'];stress=[x for x in r if x['cenario']=='custo2x']
        blocos=sorted({x['recorte'] for x in base});seeds=sorted({x['seed'] for x in base})
        if len(blocos)!=3 or len(seeds)!=(8 if fase=='reforco' else 3):
            raise ValueError('Elegibilidade publicada sem coorte esperada.')
        def media(rs):
            v=[x['metricas']['crescimento_log_diario'] for x in rs]
            return None if any(a is None for a in v) else float(np.mean(v))
        cal=[x['metricas']['calmar'] for x in base]
        score=None if any(x is None for x in cal) else float(np.median(cal))
        bg,sg=media(base),media(stress)
        positivos_b=sum((v:=media([x for x in base if x['recorte']==b])) is not None and v>0 for b in blocos)
        positivos_s=sum((v:=media([x for x in base if x['seed']==s])) is not None and v>0 for s in seeds)
        esperado=(all(not x['metricas']['insolvente'] and not x['metricas']['saida_prudencial'] and x['metricas']['operacoes']>=20 for x in r)
            and bg is not None and bg>0 and sg is not None and sg>0 and score is not None and score>0
            and positivos_b>=2 and (fase!='reforco' or positivos_s>=6))
        zeros=[{'recorte':x['recorte'],'seed':x['seed'],'operacoes':x['metricas']['operacoes']} for x in base
               if x['metricas']['crescimento_log_diario']==0]
        linhas.append({'fase':fase,'receita':recibo.parent.name,'elegivel_recalculado':bool(esperado),
            'elegivel_publicado':publicado['elegivel'],'coincide':bool(esperado)==publicado['elegivel'],
            'recortes_positivos':int(positivos_b),'seeds_positivas':int(positivos_s),'crescimento_zero':zeros})
    return {'utc':agora(),'execucao':ptr,'vereditos':linhas,'todos_coincidem':all(x['coincide'] for x in linhas),
        'observacao':'Executor usa valor or -inf ao contar positividade. Crescimento zero não é ausente; esta conferência usa a regra literal e detecta qualquer efeito no veredito. Células em caixa já falham na atividade mínima, independentemente dessa expressão.'}


if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser();a.add_argument('--destino');a.add_argument('--curvas',action='store_true')
    a.add_argument('--calibracao',action='store_true')
    a.add_argument('--contratos',action='store_true')
    a.add_argument('--previsoes',action='store_true')
    args=a.parse_args();r=resumir_previsoes() if args.previsoes else conferir_contratos() if args.contratos else conferir_calibracao() if args.calibracao else conferir_curvas() if args.curvas else conferir()
    r['fonte_auditor_sha256']=sha256(__file__)
    if args.destino:
        p=RAIZ/args.destino
        if p.exists():raise FileExistsError('Recibo posterior existente não será sobrescrito.')
        salvar_json(p,r)
    print(r)
    if not r.get('todos_coincidem',r.get('conferido',False)):raise SystemExit(2)
