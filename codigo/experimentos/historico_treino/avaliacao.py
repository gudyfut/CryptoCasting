"""Avaliação pareada de duas janelas; sem escolha por S e sem novos ajustes."""
from pathlib import Path
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, ler_json, salvar_json, sha256, agora
from experimentos.operacional_futuros.avaliar import avaliar_coorte, guardar, ms
from simulacao_operacoes.operacional.motor import Politica, simular, volatilidade_horaria
from .contrato import BRACOS

CENARIOS = [('base',.0005,0),('custo2x',.001,0),('custo3x',.0015,0),('comprado',.0005,1),('vendido',.0005,-1)]


def carregar_previsoes(jobs, fase, seeds):
    z=[dict(np.load(RAIZ/jobs[s]['pasta']/'ajuste'/(fase+'.npz'))) for s in seeds]
    for a in z[1:]:
        for k in ('indices','origens_ms','alvos'):
            np.testing.assert_array_equal(a[k],z[0][k])
    return z


def bootstrap_pareado(partes, dias, replicas=2000, seed=2605):
    """Cada parte contém [seed,dia] somas e contagens; blocos não circulares."""
    rng=np.random.default_rng(seed);saida=[]
    ns=partes[0][0].shape[0]
    for _ in range(replicas):
        seeds=rng.integers(0,ns,ns);estimativas=[]
        for somas,contagens in partes:
            n=somas.shape[1];l=min(dias,n)
            inicio=rng.integers(0,n-l+1,int(np.ceil(n/l)))
            ids=(inicio[:,None]+np.arange(l)).ravel()[:n]
            # Cada seed tem peso igual; mesmas datas e seeds em ambos os braços.
            estimativas.append(np.mean([somas[s,ids].sum()/contagens[s,ids].sum() for s in seeds]))
        saida.append(float(np.mean(estimativas)))
    return {'ic95':np.quantile(saida,[.025,.975]).tolist(),'bloco_dias':dias,'replicas':replicas,
            'natureza':'exploratorio_condicional; recortes fixos; nao corrige exposicao historica',
            'fracao_replicas_delta_positivo':float(np.mean(np.asarray(saida)>0))}


def dias_somas(origens, valores):
    dias=origens//86400000;u=np.unique(dias)
    return np.array([valores[dias==x].sum() for x in u]),np.array([(dias==x).sum() for x in u])


def retornos_diarios(resultado, mercado, inicio, fim):
    """Fechamento diário mark-close; não usa extremos artificiais do envelope de DD."""
    patrimonio=[10000.]
    trades=resultado['operacoes']
    for limite in range(inicio+86400000,fim+1,86400000):
        entradas=[t for t in trades if t['entrada_ms']<limite]
        if not entradas: valor=10000.
        else:
            t=entradas[-1]
            if t['saida_ms']<limite:valor=t['caixa_depois']
            else:
                q=t['quantidade'];preco=t['preco_entrada']
                i=mercado.indice(limite-60000)
                fund=sum(e['por_btc'] for e in t['eventos_funding'] if e['utc_ms']<limite)
                valor=t['caixa_antes']-q*preco*.0005+q*fund+t['lado']*q*(mercado.marca[i,3]-preco)
        patrimonio.append(valor)
    np.testing.assert_allclose(patrimonio[-1],resultado['metricas']['capital_final'],rtol=0,atol=1e-7)
    e=np.asarray(patrimonio)
    return None if (e<=0).any() else np.diff(np.log(e))


def resumo_previsao(z, media_t, limites):
    y,p=z['alvos'],z['previsoes'];erros=(p-y)**2
    lado=np.argmax(p,axis=1);score=p[np.arange(len(p)),lado];real=y[np.arange(len(y)),lado]
    grupos=np.searchsorted(limites,score,side='right')
    bins=[{'grupo':i,'n':int((grupos==i).sum()),
           'payoff_medio':float(real[grupos==i].mean()) if (grupos==i).any() else None} for i in range(5)]
    return {'n':len(y),'mse':float(erros.mean()),'mae':float(abs(p-y).mean()),
            'mse_zero':float((y*y).mean()),'mse_media_t':float(((y-media_t)**2).mean()),
            'preferencia_compra':float((lado==0).mean()),'payoff_hipotetico_preferido':float(real.mean()),
            'correlacao_por_lado':[float(np.corrcoef(p[:,j],y[:,j])[0,1]) if p[:,j].std()>0 and y[:,j].std()>0 else None for j in (0,1)],
            'vies_por_lado':(p-y).mean(axis=0).tolist(),'grupos_definidos_em_C':bins,
            'nota':'Payoffs hipoteticos sobrepostos nao sao retornos de carteira; scores nao sao probabilidades.'}


def executar(p, c, jobs, mercado, h, atualizar):
    d=p/'publicacao';d.mkdir(exist_ok=False)
    sigma=volatilidade_horaria(h);fixas=[];selecionadas=[];preditivas=[];partes=[]
    principais=[j for j in jobs if not j['controle']]
    if len(principais)!=18 or len({(j['braco'],j['recorte']['id'],j['seed']) for j in principais})!=18:
        raise ValueError('Cobertura principal inválida.')
    for rec in c['recortes']:
        pares={}
        for braco in BRACOS:
            jj={j['seed']:j for j in principais if j['braco']==braco and j['recorte']['id']==rec['id']}
            if set(jj)!=set(c['seeds']):raise ValueError('Pareamento incompleto.')
            destino=d/'operacao'/braco/rec['id'];atualizar('avaliando',coorte=f'{braco}/{rec["id"]}')
            # Preserva integralmente a regra histórica, incluindo caixa após reprovação em C.
            selecionadas.extend(avaliar_coorte(destino/'selecao_C',mercado,h,c['receita'],rec,
                 {s:RAIZ/jj[s]['pasta'] for s in c['seeds']},c['seeds'],braco,'historico'))
            zs=carregar_previsoes(jj,'comparacao',c['seeds']);zc=carregar_previsoes(jj,'calibracao',c['seeds'])
            medias=[]
            for s,z,cal in zip(c['seeds'],zs,zc):
                mt=np.array(ler_json(RAIZ/jj[s]['pasta']/'ajuste/escalas.json')['media_alvo'])
                medias.append(mt)
                limites=np.quantile(cal['previsoes'].max(axis=1),[.2,.4,.6,.8])
                m=resumo_previsao(z,mt,limites)
                # Conferência independente do MSE/MAE publicado pelo treinador.
                antigo=ler_json(RAIZ/jj[s]['pasta']/'ajuste/conclusao.json')['metricas']['comparacao']
                np.testing.assert_allclose([m['mse'],m['mae']],[antigo['mse'],antigo['mae']],rtol=1e-12,atol=1e-15)
                preditivas.append({'braco':braco,'recorte':rec['id'],'seed':s,**m})
            for mt in medias[1:]:np.testing.assert_array_equal(mt,medias[0])
            pares[braco]=zs
            unidades=[(str(s),z['previsoes']) for s,z in zip(c['seeds'],zs)]
            unidades += [('ensemble',np.mean([z['previsoes'] for z in zs],axis=0)),
                         ('media_t',np.broadcast_to(medias[0],zs[0]['previsoes'].shape).copy())]
            inicio,fim=map(ms,rec['comparacao']);pol=Politica(**c['politica_fixa'])
            for unidade,previsoes in unidades:
                for nome,slip,lado in CENARIOS:
                    r=simular(mercado,zs[0]['origens_ms'],previsoes,sigma[zs[0]['indices']],
                              'payoff',pol,inicio,fim,*c['receita']['barreiras_payoff'],slip,lado)
                    pasta=destino/'fixa'/unidade/nome
                    met=guardar(pasta,r,mercado,inicio,fim,{'braco':braco,'recorte':rec['id'],
                         'unidade':unidade,'cenario':nome,'politica':'fixa ex ante; nao selecionada em C/S'})
                    fixas.append({'braco':braco,'recorte':rec['id'],'unidade':unidade,'cenario':nome,
                                  'pasta':pasta.relative_to(RAIZ).as_posix(),'metricas':met})
        somas=[];contagens=[]
        for a,b in zip(pares['acumulado'],pares['movel12']):
            for k in ('origens_ms','alvos'):np.testing.assert_array_equal(a[k],b[k])
            delta=((b['previsoes']-b['alvos'])**2-(a['previsoes']-a['alvos'])**2).mean(axis=1)
            x,n=dias_somas(a['origens_ms'],delta);somas.append(x);contagens.append(n)
        partes.append((np.array(somas),np.array(contagens)))
    real=sum(1 for _ in d.rglob('curva.npz'))
    if real!=456:raise ValueError(f'Cobertura de carteiras: {real}, esperado456.')
    resumos={}
    for b in BRACOS:
        pre=[x for x in preditivas if x['braco']==b]
        resumos[b]={'mse_media_seeds_recortes':float(np.mean([x['mse'] for x in pre])),
                    'mae_media_seeds_recortes':float(np.mean([x['mae'] for x in pre])), 'operacao_fixa':{}}
        for tipo in ('seeds','ensemble','media_t'):
            resumos[b]['operacao_fixa'][tipo]={}
            for cen,_,_ in CENARIOS:
                linhas=[x['metricas'] for x in fixas if x['braco']==b and x['cenario']==cen and
                        ((x['unidade'].isdigit()) if tipo=='seeds' else x['unidade']==tipo)]
                campos=('retorno_liquido','drawdown_maximo','crescimento_log_diario','operacoes','pnl_compras','pnl_vendas')
                resumos[b]['operacao_fixa'][tipo][cen]={k:float(np.mean([v[k] for v in linhas])) if all(v[k] is not None for v in linhas) else None for k in campos}
    # Incerteza econômica: uma carteira ensemble, não oito/ três mercados independentes.
    partes_g=[]
    for rec in c['recortes']:
        curvas=[]
        for b in BRACOS:
            linha=next(x for x in fixas if x['braco']==b and x['recorte']==rec['id'] and x['unidade']=='ensemble' and x['cenario']=='base')
            r=ler_json(RAIZ/linha['pasta']/'resultado.json')
            diario=retornos_diarios(r,mercado,*map(ms,rec['comparacao']))
            if diario is None:curvas=[];break
            curvas.append(diario)
        if len(curvas)==2:
            delta=curvas[1]-curvas[0];partes_g.append((delta[None,:],np.ones((1,len(delta)))))
    incerteza={str(n):bootstrap_pareado(partes,n,c['bootstrap']['replicas']) for n in c['bootstrap']['dias']}
    economica={str(n):bootstrap_pareado(partes_g,n,c['bootstrap']['replicas']) for n in c['bootstrap']['dias']} if len(partes_g)==3 else {'nao_estimavel':'patrimonio nao positivo em alguma carteira'}
    resumo={'utc':agora(),'situacao':'concluido','carteiras':real,'principais':18,'controles':2,
        'resumos':resumos,'incerteza_delta_mse_movel_menos_acumulado':incerteza,
        'incerteza_delta_log_diario_ensemble':economica,'periodos':'S2023 ja consultado; retrospectiva exploratoria',
        'limites':['tres seeds e tres recortes','mesmo criterio de parada, diferentes atualizacoes por epoca',
                  'calendario ancestral preserva seis meses entre fim de T e inicio de S',
                  'motor prudencial nao certifica liquidacao Binance','media de carteiras nao e retorno composto',
                  'nenhuma promocao automatica ou novo teste2024–2025']}
    salvar_json(d/'previsao.json',preditivas);salvar_json(d/'carteiras_fixas.json',fixas)
    salvar_json(d/'carteiras_selecionadas_C.json',selecionadas);salvar_json(d/'resumo.json',resumo)
    texto=['# Histórico acumulado versus12meses','',f'Execução {p.name}. 18 ajustes principais +2 controles;456 carteiras.',
           '','Retrospectiva em2023. Receita C06, calendário, motor e políticas mantidos. Apenas início de T varia.',
           '','|Braço|MSE médio|Retorno médio ensemble fixo|Drawdown médio ensemble fixo|','|---|---:|---:|---:|']
    for b,r in resumos.items():
        op=r['operacao_fixa']['ensemble']['base']
        texto.append(f"|{b}|{r['mse_media_seeds_recortes']:.9f}|{op['retorno_liquido']:.2%}|{op['drawdown_maximo']:.2%}|")
    texto += ['','IC95 delta MSE (móvel−acumulado), blocos14dias: '+str(incerteza['14']['ic95']),
              'Valores negativos favorecem móvel no MSE; lucro deve ser avaliado separadamente.',
              '','Ver resumo.json para estresse, seeds, referência de média T e incerteza econômica; carteiras_selecionadas_C.json preserva a política histórica.',
              '','## Limitações']+['- '+x for x in resumo['limites']]
    (d/'relatorio.md').write_text('\n'.join(texto)+'\n',encoding='utf-8')
    arquivos={x.relative_to(d).as_posix():sha256(x) for x in d.rglob('*') if x.is_file()}
    salvar_json(d/'manifesto.json',{'arquivos':arquivos,'carteiras':real,'utc':agora()})
    return resumo
