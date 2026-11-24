"""Conferência independente, contrastes temporais e política Spot predefinida."""
import math
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, agora, salvar_json, ler_json, sha256
from .spot import simular


def conferir_previsoes(q, esperado, resultado=None):
    colunas = ['origem_utc','destino_utc','indice_candle','close','preco_destino','alvo']
    pd.testing.assert_frame_equal(q[colunas].reset_index(drop=True), esperado[colunas].reset_index(drop=True), check_exact=True)
    if q['origem_utc'].duplicated().any() or not q['origem_utc'].is_monotonic_increasing:
        raise ValueError('Origens duplicadas ou fora de ordem.')
    if not np.isfinite(q['previsao']).all():
        raise ValueError('Previsão não finita.')
    if resultado is not None:
        y, p = q['alvo'].to_numpy(float), q['previsao'].to_numpy(float)
        if not np.isfinite(y).all():
            raise ValueError('Alvo não finito na avaliação preditiva.')
        mse = math.fsum(float(a-b)**2 for a,b in zip(y,p)) / len(y)
        mae = math.fsum(abs(float(a-b)) for a,b in zip(y,p)) / len(y)
        base = math.fsum(float(a)**2 for a in y) / len(y)
        refeito = {'mse': mse, 'mae': mae, 'rmse': math.sqrt(mse), 'mse_naive': base,
                   'vies': math.fsum(float(b-a) for a,b in zip(y,p)) / len(y),
                   'acuracia_direcional': sum(np.sign(a)==np.sign(b) for a,b in zip(y,p))/len(y)}
        refeito['habilidade_mse'] = 1-mse/base if base>0 else None
        recalls=[]
        for sinal,rotulo in [(-1,'queda'),(0,'zero'),(1,'alta')]:
            reais=[i for i,a in enumerate(y) if np.sign(a)==sinal]
            refeito['reais_'+rotulo]=len(reais)
            refeito['previsoes_'+rotulo]=sum(np.sign(a)==sinal for a in p)
            if sinal:
                recall=sum(np.sign(p[i])==sinal for i in reais)/len(reais) if reais else None
                refeito['recall_'+rotulo]=recall
                recalls.append(recall)
        refeito['acerto_balanceado_direcional']=sum(recalls)/2 if all(v is not None for v in recalls) else None
        if resultado['n'] != len(y):
            raise ValueError('Contagem de métricas divergente.')
        for chave, valor in refeito.items():
            if (valor is None and resultado[chave] is not None) or (valor is not None and
                    (resultado[chave] is None or not math.isclose(valor, resultado[chave], rel_tol=1e-11, abs_tol=1e-14))):
                raise ValueError(f'Métrica divergente: {chave}')
        return {k: (int(v) if isinstance(v,np.integer) else v) for k,v in refeito.items()}


def contraste_temporal(origens, perdas_a, perdas_b, cfg):
    diferenca = np.asarray(perdas_a) - np.asarray(perdas_b)
    if len(diferenca) != len(origens) or not np.isfinite(diferenca).all():
        raise ValueError('Contraste pareado inválido.')
    diario = pd.DataFrame({'d': diferenca}, index=pd.DatetimeIndex(origens)).resample('D')['d'].agg(['sum', 'count'])
    soma, n = diario['sum'].to_numpy(), diario['count'].to_numpy()
    intervalos = {}
    for dias in cfg['dias']:
        g = np.random.default_rng(cfg['seed'] + dias)
        amostras = []
        for _ in range(cfg['replicas']):
            inicios = g.integers(0, len(diario), size=math.ceil(len(diario)/dias))
            indices = ((inicios[:,None] + np.arange(dias)) % len(diario)).ravel()[:len(diario)]
            total = n[indices].sum()
            if total == 0:
                raise ValueError('Réplica sem observações.')
            amostras.append(soma[indices].sum()/total)
        intervalos[str(dias)] = np.quantile(amostras, [.025, .975]).tolist()
    return {'diferenca_mse_a_menos_b': float(diferenca.mean()), 'ic95': intervalos,
            'principal_dias': cfg['principal'], 'replicas': cfg['replicas'],
            'metodo': 'blocos circulares de dias corridos; perdas médias entre seeds, não ensemble; condicional aos modelos ajustados'}


def comprar_manter(minutos, primeiro, inicio, fim, p, agravado=False):
    # Mesmas fronteiras máximas da política diária: 01/jan 00:01 até 31/dez 00:01.
    e = int(pd.Timestamp(inicio, tz='UTC').timestamp()//60) + p['latencia_minutos']
    v = int(pd.Timestamp(fim, tz='UTC').timestamp()//60) - 1440 + p['latencia_minutos']
    i,j = e-primeiro,v-primeiro
    f = p['taxa_agravada'] if agravado else p['taxa']
    s = p['slippage_agravado'] if agravado else p['slippage']
    r = {'entrada_minuto': e, 'saida_minuto': v, 'capital_inicial': p['capital']}
    if not (0 <= i < j < len(minutos)) or not np.isfinite(minutos[[i,j],0]).all() or not (minutos[[i,j],5] > 0).all():
        return dict(r, retorno_auditavel=False, risco_auditavel=False, retorno_liquido=None, drawdown=None)
    a,b = minutos[i,0],minutos[j,0]
    quantidade = p['capital']/(a*(1+s)*(1+f))
    capital = quantidade*b*(1-s)*(1-f)
    caminho = minutos[i:j,3]
    observavel = bool(np.isfinite(caminho).all())
    marcas = np.r_[p['capital'], quantidade*caminho*(1-s)*(1-f), capital]
    dd = float(np.max(1-marcas/np.maximum.accumulate(marcas))) if observavel else None
    return dict(r, retorno_auditavel=True, risco_auditavel=observavel, capital_final=float(capital),
                retorno_liquido=float(capital/p['capital']-1), drawdown=dd, entradas_planejadas=1,
                custos_observados=float(quantidade*a*((1+s)*(1+f)-1)+quantidade*b*(1-(1-s)*(1-f))))


def concluir(pasta, c, manifesto, blocos, tentativas):
    # Publicações posteriores interrompidas são preservadas, não reescritas.
    raiz = pasta / 'publicacoes'
    destino = raiz / f'tentativa_{len(list(raiz.glob("tentativa_*")))+1:03d}'
    destino.mkdir(parents=True)
    from .mercado import carregar_minutos
    minutos, primeiro = carregar_minutos(RAIZ / manifesto['mercado'], c['par'])
    predicoes, resumo, auditoria = {}, {}, {}
    for chave, tentativa in tentativas.items():
        resultado = ler_json(tentativa / 'resultado.json')
        auditoria[chave] = {}
        for b in ('validacao', 'teste', 'operacional'):
            q = pd.read_parquet(tentativa / f'previsoes_{b}.parquet')
            auditoria[chave][b] = conferir_previsoes(q, blocos[b], resultado['metricas'].get(b))
            if chave.startswith('controle_'):
                continue
            predicoes[chave,b] = q
        if chave.startswith('controle_'):
            continue
        economico = {}
        for nome, agravado in [('base',False),('agravado',True)]:
            r, operacoes, curva = simular(predicoes[chave,'operacional'], minutos, primeiro,
                                         c['divisao']['teste'][1], c['operacao'], agravado=agravado)
            economico[nome] = r
            # Caixa às 00:00 pode refletir a saída anterior às 00:01; alinhar apresentação.
            for ponto in curva:
                t=pd.Timestamp(ponto['tempo_utc'])
                if t.minute==0:
                    ponto['tempo_utc']=(t+pd.Timedelta(minutes=c['operacao']['latencia_minutos'])).isoformat()
            salvar_json(destino / chave / f'operacoes_{nome}.json', operacoes)
            salvar_json(destino / chave / f'curva_{nome}.json', curva)
        bruto = predicoes[chave,'operacional'].copy()
        f,s = c['operacao']['taxa'],c['operacao']['slippage']
        limiar = np.log((1+s)*(1+f)/((1-s)*(1-f)))
        bruto['previsao'] = (bruto['previsao'] > limiar).astype(float)
        sem_custos = dict(c['operacao'], taxa=0., slippage=0.)
        economico['bruto_mesmos_sinais'] = simular(bruto, minutos, primeiro, c['divisao']['teste'][1], sem_custos)[0]
        resumo[chave] = {'predicao': resultado['metricas'], 'spot': economico}
        for nome in ('base', 'agravado'):
            operacoes = ler_json(destino / chave / f'operacoes_{nome}.json')
            retornos = [o['retorno_liquido'] for o in operacoes if o.get('retorno_liquido') is not None]
            resumo[chave]['spot'][nome]['distribuicao_operacoes_observadas'] = {
                'n': len(retornos), 'ganhos': sum(v > 0 for v in retornos), 'perdas': sum(v < 0 for v in retornos),
                'zeros': sum(v == 0 for v in retornos),
                'mediana': float(np.median(retornos)) if retornos else None,
                'minimo': min(retornos) if retornos else None, 'maximo': max(retornos) if retornos else None,
                'limite': 'somente operações com retorno observável; não estima resultado das indisponíveis'}
        q=predicoes[chave,'teste'].copy()
        q['trimestre']=pd.DatetimeIndex(q['origem_utc']).quarter
        resumo[chave]['diagnostico_trimestres']={str(t): {'n':len(v),'mse':float(np.mean((v.previsao-v.alvo)**2)),
                                                       'mse_naive':float(np.mean(v.alvo**2))}
                                                  for t,v in q.groupby('trimestre')}
    grupos = {'mamba': [f'mamba_{s}' for s in c['seeds']], 'lstm': [f'lstm_{s}' for s in c['seeds']],
              'naive': ['naive'], 'arima': ['arima']}
    agregados, contrastes = {}, {}
    for b in ('validacao','teste'):
        perdas = {m: np.mean([(predicoes[k,b]['previsao'].to_numpy()-predicoes[k,b]['alvo'].to_numpy())**2
                              for k in ks], axis=0) for m,ks in grupos.items()}
        agregados[b] = {m: {'mse_medio_seeds': float(e.mean()),
                            'habilidade_mse': float(1-e.mean()/perdas['naive'].mean()) if perdas['naive'].mean() > 0 else None,
                            'mse_por_seed': {k: resumo[k]['predicao'][b]['mse'] for k in grupos[m]},
                            'desvio_padrao_mse_seeds': float(np.std([resumo[k]['predicao'][b]['mse'] for k in grupos[m]], ddof=1)) if len(grupos[m]) > 1 else None}
                        for m,e in perdas.items()}
        contrastes[b] = {f'{a}_menos_{z}': contraste_temporal(blocos[b]['origem_utc'], perdas[a], perdas[z], c['bootstrap'])
                        for a,z in [('mamba','naive'),('mamba','lstm'),('lstm','naive'),('arima','naive')]}
    referencias = {'caixa': {'retorno_liquido': 0., 'drawdown': 0.}}
    for nome, agravado in [('base',False),('agravado',True)]:
        referencias[f'compra_diaria_{nome}'] = simular(predicoes['naive','operacional'], minutos, primeiro,
                c['divisao']['teste'][1], c['operacao'], controle=True, agravado=agravado)[0]
        referencias[f'comprar_manter_{nome}'] = comprar_manter(minutos, primeiro, *c['divisao']['teste'], c['operacao'], agravado)
    salvar_json(destino / 'conferencia_metricas.json', auditoria)
    salvar_json(destino / 'resultados.json', {'por_ajuste': resumo, 'medias': agregados, 'contrastes': contrastes,
                'referencias_economicas': referencias, 'natureza': c['exposicao'], 'utc': agora()})
    salvar_json(destino / 'manifesto.json', {'arquivos': {p.relative_to(destino).as_posix(): sha256(p)
                for p in sorted(destino.rglob('*')) if p.is_file()}})
    salvar_json(pasta / 'publicacao.json', {'pasta': destino.relative_to(pasta).as_posix(), 'manifesto_sha256': sha256(destino/'manifesto.json')})
