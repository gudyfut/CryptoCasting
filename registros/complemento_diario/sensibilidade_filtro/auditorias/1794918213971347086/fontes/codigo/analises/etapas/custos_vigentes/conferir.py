"""Confere herança, cobertura e contabilidade amostrada, sem reexecutar carteiras."""
from collections import Counter
from copy import deepcopy
import json
import sqlite3
import zipfile
import platform
import sys
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,sha256,agora
from . import adaptadores as a
from .historico import instalar
from .executar import PONTEIRO


def executar():
    ptr=ler_json(PONTEIRO);p=RAIZ/ptr['pasta'];f=ler_json(p/'congelamento.json')
    if ler_json(p/'progresso.json')['situacao']!='recalculado_conferido' or (p/'execucao.lock').exists():raise ValueError('Execução não encerrada')
    instalar();db=sqlite3.connect(p/'carteiras.sqlite');assert db.execute('PRAGMA integrity_check').fetchone()==('ok',)
    linhas={nome:(k,json.loads(r)) for nome,k,r in db.execute('SELECT fonte,chave,resumo FROM carteiras')}
    jobs=f['inventario']['jobs'];assert set(linhas)=={j['fonte'] for j in jobs}
    for nome,h in f['fontes'].items():assert sha256(RAIZ/nome)==h,nome
    for j in jobs:assert sha256(RAIZ/j['fonte'])==j['sha256'],j['fonte']
    heranca=f.get('continuacao_tecnica');herdadas=0
    with zipfile.ZipFile(p/'ledgers.zip') as z:
        assert z.testzip() is None
        if heranca:
            pai=RAIZ/heranca['pai']['pasta'];bd=sqlite3.connect(pai/'carteiras.sqlite')
            with zipfile.ZipFile(pai/'ledgers.zip') as anterior:
                for nome,k,r in bd.execute('SELECT fonte,chave,resumo FROM carteiras'):
                    assert linhas[nome]==(k,json.loads(r));herdadas+=1
                for nome in anterior.namelist():assert anterior.read(nome)==z.read(nome)
            bd.close()
        vistos=set();amostras=[]
        for j in jobs:
            tipo=j['tipo'];chave,resumo=linhas[j['fonte']]
            if tipo=='spot_retida':s=(tipo,resumo['politica'],resumo['cenario'])
            elif tipo in ('retida','futuro24'):
                g=j['grade'];s=(j['pai'],g['politica'],g.get('braco',g.get('modo')),g['cenario'],g.get('benchmark'),g.get('modelo') if g.get('seed') is None else 'rede')
            else:continue # diária/operacional já exigem auditoria interna em todas as carteiras
            if s in vistos:continue
            vistos.add(s);extra=json.loads(z.read(chave+'.json'));r=deepcopy(resumo)
            if tipo=='spot_retida':
                from backtest_carteira.auditoria import conferir
                cfg=a.localizar(a.contrato(j['pai']),{'custos','risco_smart','passo_btc','minimo_usdt'})
                if cfg is None:cfg=a.contrato('backtest_carteira_8ec8a66648313caa48e3')['configuracao']
                cfg=deepcopy(cfg);custo=deepcopy(cfg['custos'][r['cenario']]);custo['slippage']*=.2;cfg['custos']['execucao_vigente']=custo;r['cenario']='execucao_vigente'
                q=a.q_sinais(ler_json(j['fonte']));m,primeiro=a.spot()
                conferir(q,m,primeiro,cfg,r['politica'],'execucao_vigente',r,extra['ordens'],pd.DataFrame(extra['diarios']))
            else:
                cfg=deepcopy(a.contrato(j['pai'])['configuracao']);custo=deepcopy(cfg['custos'][g['cenario']]);custo['slippage']*=.2;cfg['custos']['execucao_vigente']=custo;r['cenario']='execucao_vigente'
                if tipo=='futuro24':
                    from simulacao_operacoes.futuros.auditoria import conferir
                    conferir(r,extra['operacoes'],extra['funding'],a.mercado_f01(),cfg)
                else:
                    if j['pai'].startswith('revisao_'):from simulacao_operacoes.revisada.auditoria import conferir
                    else:from simulacao_operacoes.smart.auditoria import conferir
                    m=a.mercados_retidos(j['pai'])['spot' if g['braco']=='spot' else 'futuro']
                    conferir(r,extra['ordens'],extra['eventos'],m,cfg)
            amostras.append({'fonte':j['fonte'],'tipo':tipo,'conferido':True})
    anterior=ler_json(RAIZ/'registros/generalizacao_moedas/custos/ultima.json')
    assert sha256(RAIZ/anterior['arquivo'])==anterior['sha256'];sens=ler_json(RAIZ/anterior['arquivo']);medias=0
    bases={'BTC':'dados/experimentos/padronizacao_diaria_f3f8772670f244779ad7',
        **{m:f'dados/experimentos/generalizacao_moedas_1f2b005888361d23c111/{m}USDT'+('/continuacao_001' if m=='XRP' else '') for m in ('ETH','BNB','XRP')}}
    for moeda,base in bases.items():
        for fase in ('validacao','teste'):
            rs=[linhas[j['fonte']][1] for j in jobs if j['tipo']=='diaria' and j['base']==base and j['registro']['fase']==fase and j['registro']['cenario']=='base' and str(j['registro']['unidade']).isdigit()]
            assert len(rs)==3
            for k,v in sens['medias_tres_seeds'][moeda][fase]['slip_1bp'].items():
                if v is not None:np.testing.assert_allclose(np.mean([r[k] for r in rs]),v,rtol=1e-10,atol=1e-8)
            medias+=1
    r={'utc':agora(),'situacao':'conferido','cobertura':dict(Counter(j['tipo'] for j in jobs)),
        'ambiente':{'python':platform.python_version(),'executavel':sys.executable,'numpy':np.__version__,'pandas':pd.__version__,'host':platform.node()},
        'metodo_execucao':'Leitura financeira com cache de timestamps e continuação técnica identificada; sem modelo, otimizador ou GPU de treinamento.',
        'carteiras':len(jobs),'herdadas_preservadas_exatamente':herdadas,'ledgers_zip_integro':True,
        'auditorias_contabeis_amostradas':amostras,'medias_diarias_iguais_a_sensibilidade_preservada':medias,
        'novos_treinamentos':0,'limite':'Amostragem por motor/politica/braco/cenario; não é auditoria independente de cada tick de todas as carteiras.'}
    salvar_json(p/'conferencia_posterior.json',r);print(json.dumps({k:v for k,v in r.items() if k!='auditorias_contabeis_amostradas'},ensure_ascii=False))


if __name__=='__main__':executar()
