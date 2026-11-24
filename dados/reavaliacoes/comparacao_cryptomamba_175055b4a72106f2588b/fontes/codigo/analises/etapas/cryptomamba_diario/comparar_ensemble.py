"""Comparação posterior justa de duas receitas locais, não do checkpoint publicado."""
from copy import deepcopy
import csv
import io
import json
import os
from pathlib import Path
import platform
import shutil
import traceback
import zipfile
import numpy as np
from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256, identidade, conferir_arquivos
from experimentos.generalizacao_moedas.avaliacao import carregar_mercado
from simulacao_operacoes.continuidade_diaria.simulador import simular
from simulacao_operacoes.continuidade_diaria.auditoria_grade import conferir
from analises.etapas.ensemble_2026.ciclo import intervalo

REG = RAIZ/'registros/comparacao_cryptomamba_diaria'
CFG = RAIZ/'configuracoes/comparacao_cryptomamba_diaria_001.json'


def preparar():
    REG.mkdir(exist_ok=True)
    assert not (REG/'execucao.json').exists(), 'Não duplicar avaliação já preparada.'
    cfg=ler_json(CFG)
    preco=ler_json(RAIZ/'registros/cryptomamba_reproducivel/execucao.json')
    ref=ler_json(RAIZ/'registros/continuidade_moedas/execucao.json')
    custos=ler_json(RAIZ/'registros/custos_vigentes/vigente.json')
    assert preco['id']==cfg['referencia_preco'] and ref['id']==cfg['referencia_operacional']
    for ponteiro in [preco,ref]:
        assert sha256(RAIZ/ponteiro['pasta']/'congelamento.json')==ponteiro['congelamento_sha256']
    assert sha256(RAIZ/custos['pasta']/'publicacao_manifesto.json')==custos['manifesto_sha256']
    fp=ler_json(RAIZ/preco['pasta']/'congelamento.json')
    fr=ler_json(RAIZ/ref['pasta']/'congelamento.json')
    info=fr['moedas']['BTCUSDT'];cp=fp['configuracao'];cr=info['configuracao']
    assert cp['arquitetura']==cr['arquitetura'] and cp['periodos']==cr['periodos'] and cp['seeds']==cr['seeds']==cfg['seeds']
    assert cp['normalizar'] is False and cr['normalizar'] is True
    assert cp['alvo']=='preco_fechamento_seguinte_USDT' and cr['alvo']=='retorno_simples_fechamento_seguinte_decimal'
    assert fp['diario']==info['diario'] and fp['mercado_minuto']==info['mercado']
    for k in ['taxa','weight_decay','lote','epocas','scheduler_passo','scheduler_gamma','epsilon_raiz']:
        assert cp['treinamento'][k]==cr['treinamento'][k]
    pais={}
    for ptr in [preco,ref,custos]:
        p=RAIZ/ptr['pasta']
        for nome in ['congelamento.json','manifesto.json']:
            if (p/nome).exists():pais[(p/nome).relative_to(RAIZ).as_posix()]=sha256(p/nome)
    for nome in ['fechamento.json','controle.json']:
        p=RAIZ/preco['pasta']/nome;pais[p.relative_to(RAIZ).as_posix()]=sha256(p)
    for nome in ['resultados.json','carteiras.zip']:
        p=RAIZ/ref['pasta']/nome;pais[p.relative_to(RAIZ).as_posix()]=sha256(p)
    p=RAIZ/custos['pasta']/'publicacao/diarias.json';pais[p.relative_to(RAIZ).as_posix()]=sha256(p)
    p=RAIZ/custos['pasta']/'publicacao_manifesto.json';pais[p.relative_to(RAIZ).as_posix()]=sha256(p)
    for base in [RAIZ/preco['pasta'],RAIZ/info['base']]:
        for fase in cfg['fases']:
            for seed in cfg['seeds']:
                a=base/'publicacao/previsoes'/f'{fase}_{seed}.npz';pais[a.relative_to(RAIZ).as_posix()]=sha256(a)
        for seed in cfg['seeds']:
            d=base/'ajustes'/f'seed_{seed}';sel=ler_json(d/'selecao.json')
            for a in [d/'selecao.json',d/sel['checkpoint']]:pais[a.relative_to(RAIZ).as_posix()]=sha256(a)
    fontes={p:sha256(RAIZ/p) for p in ['codigo/analises/etapas/cryptomamba_diario/comparar_ensemble.py',
        'configuracoes/comparacao_cryptomamba_diaria_001.json','codigo/simulacao_operacoes/continuidade_diaria/simulador.py',
        'codigo/simulacao_operacoes/continuidade_diaria/auditoria_grade.py','codigo/simulacao_operacoes/revisada/conta.py',
        'codigo/simulacao_operacoes/diaria_24h.py','codigo/simulacao_operacoes/envelopes_marcacao.py',
        'codigo/experimentos/generalizacao_moedas/avaliacao.py','codigo/analises/etapas/ensemble_2026/ciclo.py',
        'codigo/infraestrutura/artefatos.py']}
    f=dict(utc=agora(),configuracao=cfg,preco=preco,referencia=ref,custos=custos,info_btc=info,fontes=fontes,pais=pais)
    codigo=identidade(f)[:20];p=RAIZ/'dados/reavaliacoes'/f'comparacao_cryptomamba_{codigo}';p.mkdir(exist_ok=False)
    for n in fontes:
        dest=p/'fontes'/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(RAIZ/n,dest)
    salvar_json(p/'congelamento.json',f)
    ptr=dict(id=codigo,pasta=p.relative_to(RAIZ).as_posix(),congelamento_sha256=sha256(p/'congelamento.json'))
    salvar_json(REG/'execucao.json',ptr);salvar_json(REG/'estado.json',dict(utc=agora(),situacao='preparado_autorizado',execucao=ptr))
    return ptr,p,f


def executar(ptr,p,f):
    assert not (p/'resultados.json').exists()
    conferir_arquivos(RAIZ,f['fontes']);conferir_arquivos(RAIZ,f['pais'])
    with (p/'execucao.lock').open('x') as lock:lock.write(str(os.getpid()))
    salvar_json(p/'processo.json',dict(utc=agora(),host=platform.node(),pid=os.getpid()))
    try:
        cfg=f['configuracao'];base=RAIZ/f['preco']['pasta'];atual=RAIZ/f['referencia']['pasta']
        vigente=ler_json(RAIZ/f['custos']['pasta']/'publicacao/diarias.json')[f['preco']['pasta']]
        antigo=ler_json(atual/'resultados.json');m=carregar_mercado(f['info_btc']['mercado'])
        from simulacao_operacoes.diaria_24h import simular as simular_diario, conferir as conferir_diario
        linhas=[];controles=[];contrastes={}
        with zipfile.ZipFile(atual/'carteiras.zip') as herdado, zipfile.ZipFile(p/'carteiras.zip','x',compression=zipfile.ZIP_DEFLATED) as pacote:
            for fase in cfg['fases']:
                a=[dict(np.load(base/'publicacao/previsoes'/f'{fase}_{s}.npz',allow_pickle=False)) for s in cfg['seeds']]
                b=[dict(np.load(RAIZ/f['info_btc']['base']/'publicacao/previsoes'/f'{fase}_{s}.npz',allow_pickle=False)) for s in cfg['seeds']]
                t,u,y=a[0]['origens_ms'],a[0]['ultimo_close'],a[0]['y']
                for z in a+b:
                    for k,v in [('origens_ms',t),('ultimo_close',u),('y',y)]:np.testing.assert_array_equal(z[k],v)
                pp=np.mean([z['previsoes'] for z in a],axis=0);pr=np.mean([z['previsoes'] for z in b],axis=0)
                contrastes[fase]={}
                for mult,custo in enumerate(cfg['slippage_por_lado'],1):
                    regras=deepcopy(f['info_btc']['configuracao']['operacoes']);regras['slippage_por_lado']=custo
                    r0,cv0=simular_diario(t,pp,u,m,regras,{'slippage_multiplicador':1,'lado':0});conferir_diario(r0,cv0,regras)
                    esp=next(q['metricas'] for q in vigente['carteiras'] if q['fase']==fase and q['unidade']=='ensemble' and q['cenario']=={1:'base',2:'slippage2',3:'slippage3'}[mult])
                    for k,v in esp.items():
                        if isinstance(v,(float,int)):np.testing.assert_allclose(r0['metricas'][k],v,atol=1e-7,rtol=1e-10)
                    controles.append(dict(fase=fase,slippage=custo,reproducao_preco_diario=True))
                    curvas={}
                    for un in ['preco_sem_padronizacao','retorno_padronizado','comprar_manter','naive']:
                        nome=f'{fase}/{un}/custo_{mult}'
                        if un=='preco_sem_padronizacao':
                            r,cv=simular(t,pp,u,m,regras,'liquida');au=conferir(r,cv,m,regras,'liquida',t,pp,u,None)
                            r['regras']=regras
                            pacote.writestr(nome+'/resultado.json',json.dumps(r,ensure_ascii=False,allow_nan=False));arq=io.BytesIO();np.savez_compressed(arq,origens_ms=t,**cv);pacote.writestr(nome+'/curva.npz',arq.getvalue())
                            ret=pp/u-1
                        else:
                            origem={'retorno_padronizado':'ensemble','comprar_manter':'comprar_manter','naive':'naive'}[un]
                            modo='passivo' if un=='comprar_manter' else 'liquida'
                            membro=f'BTCUSDT/{fase}/{origem}/custo_{mult}/{modo}'
                            r=json.loads(herdado.read(membro+'/resultado.json'));cv=dict(np.load(io.BytesIO(herdado.read(membro+'/curva.npz')),allow_pickle=False));cv.pop('origens_ms')
                            if un=='comprar_manter':
                                agenda=[int(round(d['quantidade']/regras['passo_quantidade'])) for d in r['dias']]
                                au=conferir(r,cv,m,regras,'agenda',t,u,u,1,agenda);ret=np.zeros(len(t))
                            else:
                                prev=pr if un=='retorno_padronizado' else u
                                au=conferir(r,cv,m,regras,'liquida',t,prev,u,None);ret=prev/u-1
                            for sufixo in ['/resultado.json','/curva.npz']:pacote.writestr(nome+sufixo,herdado.read(membro+sufixo))
                        curvas[un]=cv['saldos_diarios']
                        linhas.append(dict(fase=fase,unidade=un,slippage=custo,membro=nome,herdada=un!='preco_sem_padronizacao',metricas=r['metricas'],auditoria=au,
                                           mse_retorno=float(np.mean((ret-(y/u-1))**2))) if un!='comprar_manter' else dict(fase=fase,unidade=un,slippage=custo,membro=nome,herdada=True,metricas=r['metricas'],auditoria=au,mse_retorno=None))
                    delta=np.diff(np.log(curvas['retorno_padronizado']))-np.diff(np.log(curvas['preco_sem_padronizacao']))
                    contrastes[fase][str(custo)]={str(bloco):intervalo(delta,bloco) for bloco in [7,14,28]}
                    print('COMPARACAO',fase,custo,len(linhas),'/24',flush=True)
        assert len(linhas)==24 and sum(not l['herdada'] for l in linhas)==6 and len(controles)==6
        salvar_json(p/'resultados.json',dict(utc=agora(),execucao=ptr,carteiras=linhas,controles=controles,contraste_atual_menos_preco=contrastes,novos_treinos=0,novas_inferencias=0,carteiras_novas=6,carteiras_herdadas=18,limites=cfg['limites']))
        tabela=[dict(fase=a['fase'],unidade=a['unidade'],slippage=a['slippage'],herdada=a['herdada'],**a['metricas'],mse_retorno=a['mse_retorno']) for a in linhas]
        with (p/'comparacao.csv').open('w',newline='',encoding='utf-8-sig') as arquivo:
            escritor=csv.DictWriter(arquivo,fieldnames=list(tabela[0]));escritor.writeheader();escritor.writerows(tabela)
        conferir_arquivos(RAIZ,f['fontes']);conferir_arquivos(RAIZ,f['pais'])
        salvar_json(p/'manifesto.json',dict(utc=agora(),arquivos={q.relative_to(p).as_posix():sha256(q) for q in p.rglob('*') if q.is_file() and q.name not in ['manifesto.json','execucao.lock','processo.json']}))
        salvar_json(REG/'fechamento.json',dict(utc=agora(),execucao=ptr,manifesto_sha256=sha256(p/'manifesto.json'),novos_treinamentos=0,carteiras_novas=6,carteiras_herdadas=18,controles=6,fontes_pais_preservados=True))
        salvar_json(REG/'estado.json',dict(utc=agora(),situacao='concluido_conferido',execucao=ptr,carteiras=24))
    except BaseException:
        salvar_json(p/'incidente.json',dict(utc=agora(),erro=traceback.format_exc()));salvar_json(REG/'estado.json',dict(utc=agora(),situacao='interrompido_preservado',execucao=ptr));raise
    finally:
        (p/'execucao.lock').unlink()


if __name__=='__main__':
    executar(*preparar())
