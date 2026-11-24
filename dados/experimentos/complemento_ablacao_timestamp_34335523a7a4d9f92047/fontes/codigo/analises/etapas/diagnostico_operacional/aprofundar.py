"""Conferência independente e aprofundamentos posteriores à tabela inicial.

Não reabre a execução diagnóstica publicada. Produz recibo próprio, incluindo
o corte C06 >0,5% identificado como interessante depois da primeira leitura.
"""
from pathlib import Path
import json
import platform
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, ler_json, sha256, conferir_arquivos, identidade, agora
from .executar import salvar
from .metricas import bootstrap, direcao


def executar():
    ptr=ler_json(RAIZ/'registros/diagnostico_operacional/execucao.json'); p=RAIZ/ptr['pasta']
    assert sha256(p/'manifesto.json')==ptr['manifesto_sha256']
    conferir_arquivos(p,ler_json(p/'manifesto.json')['arquivos'])
    assinatura=ler_json(p/'congelamento.json'); conferir_arquivos(RAIZ,assinatura['fontes'])
    origem=RAIZ/assinatura['origem']['pasta']; q=pd.read_parquet(p/'observacoes.parquet')
    t=ler_json(p/'tabelas.json'); verificadas=0
    for j in ler_json(origem/'ajustes.json'):
        if j['controle']: continue
        for fase in ['validacao','calibracao','comparacao']:
            z=np.load(RAIZ/j['pasta']/'ajuste'/(fase+'.npz')); y=z['alvos']; pred=z['previsoes']
            g=q[(q.receita==j['receita_id'])&(q.recorte==j['recorte']['id'])&(q.seed==j['seed'])&(q.fase==fase)]
            assert np.array_equal(g.origem_ms,z['origens_ms'])
            assert np.isclose(((pred-y)**2).sum()/y.size,g.erro2.mean(),rtol=1e-12)
            if pred.shape[1]==1:
                np.testing.assert_allclose(g.previsao_terminal_simples,np.exp(pred[:,0])-1,atol=3e-16)
                np.testing.assert_allclose(g.retorno_terminal,np.exp(y[:,0])-1,atol=3e-16)
            else:
                np.testing.assert_array_equal(g[['p_long','p_short']].to_numpy(),pred)
                np.testing.assert_array_equal(g[['y_long','y_short']].to_numpy(),y)
            verificadas+=1
    for r in t['receitas']:
        g=q[(q.receita==r['receita'])&(q.fase==r['fase'])]
        assert len(g)==r['n']
        ativo=(g.lado!=0)&(g.retorno_terminal!=0)
        assert np.isclose((g.loc[ativo,'lado']*g.loc[ativo,'retorno_terminal']>0).mean(),r['acuracia'])
        for lado,nome in [(1,'alta'),(-1,'queda')]:
            a=g[(g.lado==lado)&(g.retorno_terminal!=0)]; v=(a.retorno_terminal*lado>0).mean()
            if len(a): assert np.isclose(v,r['precisao_'+nome])
    # Independente da função decompor_operacao: reconstrói PnL diretamente dos fills.
    residual=0.; total_carteiras=0
    for ca in ler_json(origem/'publicacao/carteiras.json'):
        rr=ler_json(RAIZ/ca['pasta']/'resultado.json'); soma=0.
        for o in rr['operacoes']:
            valor=o['quantidade']*(o['lado']*(o['preco_saida']-o['preco_entrada'])-o['comissao_por_btc']+o['funding_por_btc'])
            residual=max(residual,abs(valor-o['pnl_liquido'])); soma+=valor
        residual=max(residual,abs(soma-(rr['metricas']['capital_final']-rr['metricas']['capital_inicial'])))
        total_carteiras+=1
    assert residual<1e-7
    s=q[q.fase=='comparacao']; aprofundamentos={}
    cortes=[]
    for (r,fase),g in q.groupby(['receita','fase']):
        cortes.append({'receita':r,'fase':fase,**direcao(g.direcao_preco.to_numpy(),g.retorno_terminal.to_numpy())})
    aprofundamentos['direcao_modelo_sem_ajuste_funding']=cortes
    # Maioria e presença de oportunidades são comparadores descritivos, não estratégias.
    bases=[]
    for fold,g in s[s.receita=='R0'].drop_duplicates(['recorte','origem_ms']).groupby('recorte'):
        bases.append({'recorte':fold,'n':len(g),'alta_real':float((g.retorno_terminal>0).mean()),
            'payoff_compra':float(g.y_long.mean()),'payoff_venda':float(g.y_short.mean()),
            'ambos_payoffs_negativos':float(((g.y_long<=0)&(g.y_short<=0)).mean()),
            'algum_payoff_positivo':float(((g.y_long>0)|(g.y_short>0)).mean()),
            'maioria_treino_acuracia':float(g.acerto_maioria_treino.mean())})
    aprofundamentos['oportunidades_ex_post']=bases
    detalhes=[]
    for (fase,fold,seed),g in q[(q.receita=='C06')&(q.score>.005)].groupby(['fase','recorte','seed']):
        detalhes.append({'fase':fase,'recorte':fold,'seed':seed,'n':len(g),'origens':int(g.origem_ms.nunique()),
            'dias':int(g.dia.nunique()),'payoff_medio':float(g.payoff_escolhido.mean()),
            'acerto_terminal':float((g.lado*g.retorno_terminal>0).mean()),'taxa_payoff_positivo':float((g.payoff_escolhido>0).mean())})
    aprofundamentos['c06_score_maior_005_post_hoc']=detalhes
    cfg=assinatura['configuracao']['bootstrap']; g=s[s.receita=='C06'].copy(); g['score']=g.score-.005
    aprofundamentos['c06_cauda_ic_exploratorio']=[x for x in bootstrap(g,cfg) if x['metrica'] in ['payoff_score_positivo','ganho_lado_score_positivo']]
    # R0 direção bruta é distinta da preferência operacional que inclui funding.
    g=s[s.receita=='R0'].copy(); g['lado']=g.direcao_preco
    aprofundamentos['r0_direcao_pura_ic']=[x for x in bootstrap(g,cfg) if x['metrica'] in ['acuracia_direcional','vantagem_acuracia_maioria_treino']]
    aprofundamentos['r0_preferencia_alterada_funding']=float(np.mean(s[s.receita=='R0'].lado!=s[s.receita=='R0'].direcao_preco))
    # Assimetria das médias aprendidas em T e observadas em S.
    medias=[]
    for j in ler_json(origem/'ajustes.json'):
        if j['controle'] or j['receita_id']!='P0' or j['seed']!=42: continue
        escala=ler_json(RAIZ/j['pasta']/'ajuste/escalas.json'); g=s[(s.receita=='P0')&(s.recorte==j['recorte']['id'])&(s.seed==42)]
        medias.append({'recorte':j['recorte']['id'],'media_t':escala['media_alvo'],
            'media_s':[float(g.y_long.mean()),float(g.y_short.mean())]})
    aprofundamentos['medias_alvos_T_S']=medias
    concentracao=[]
    for (r,fold,seed),g in s.groupby(['receita','recorte','seed']):
        lim=np.quantile(abs(g.retorno_terminal),.95); grande=abs(g.retorno_terminal)>=lim
        concentracao.append({'receita':r,'recorte':fold,'seed':seed,'fracao_mse_nos_5pct_maiores_movimentos':float(g.loc[grande,'erro2'].sum()/g.erro2.sum()),
            'autocorrelacao_score_1h':float(g.score.autocorr(lag=1)),'autocorrelacao_score_24h':float(g.score.autocorr(lag=24))})
    aprofundamentos['concentracao_e_persistencia']=concentracao
    fontes={str(Path(__file__).resolve().relative_to(RAIZ)).replace('\\','/'):sha256(__file__),
        'codigo/analises/etapas/diagnostico_operacional/metricas.py':sha256(RAIZ/'codigo/analises/etapas/diagnostico_operacional/metricas.py'),
        'registros/diagnostico_operacional/testes.log':sha256(RAIZ/'registros/diagnostico_operacional/testes.log')}
    recibo={'utc':agora(),'conferido':True,'diagnostico':ptr,'fontes':fontes,'python':platform.python_version(),
        'previsoes_conferidas_independentemente':verificadas,'carteiras_conferidas':total_carteiras,
        'residuo_contabil_usdt':residual,'aprofundamentos':aprofundamentos,
        'limites':'C06 cauda foi aprofundada após observar as tabelas; intervalo exploratório sem correção de seleção/multiplicidade. Sem nova carteira ou treino.'}
    destino=RAIZ/'registros/diagnostico_operacional/conferencias'/identidade({'diagnostico':ptr,'fontes':fontes})[:20]
    destino.mkdir(parents=True,exist_ok=False)
    for nome in fontes:
        alvo=destino/'fontes'/nome; alvo.parent.mkdir(parents=True,exist_ok=True); alvo.write_bytes((RAIZ/nome).read_bytes())
    salvar(destino/'conferencia.json',recibo)
    print(json.dumps({'conferencia':destino.relative_to(RAIZ).as_posix()+'/conferencia.json','sha256':sha256(destino/'conferencia.json'),'conferido':True}))

if __name__=='__main__': executar()
