"""Recalcula erros, contrastes, intervalos e contabilidade dos artefatos finais."""
import io
import json
import math
import subprocess
import zipfile
from pathlib import Path
import numpy as np
from infraestrutura.artefatos import RAIZ, ler_json, salvar_json, sha256, conferir_arquivos, agora

REG=RAIZ/'registros/fechamento_ramos_diarios'


def media(v):
    return math.fsum(float(x) for x in v)/len(v)


def conferir_intervalos(matrizes, publicados, cfg, reamostrar):
    """Reconstrói diferenças/sorteios; não chama o avaliador ou seu bootstrap."""
    contrastes=dict(cfg['contrastes'])
    for v in cfg['variantes']:
        for ref in ('naive','linear'):contrastes[f'{v}_menos_{ref}']={v:1,ref:-1}
    assert set(publicados)==set(contrastes)
    n_controles=0
    for nome,pesos in contrastes.items():
        dif=sum(peso*matrizes[v] for v,peso in pesos.items())
        if dif.ndim==1:dif=dif[None,:]
        n=dif.shape[1]
        for bloco in cfg['bootstrap']['blocos']:
            rng=np.random.default_rng(cfg['bootstrap']['seed']);amostras=[]
            for _ in range(cfg['bootstrap']['replicas']):
                inicios=rng.integers(0,n-bloco+1,math.ceil(n/bloco))
                indices=np.concatenate([np.arange(i,i+bloco) for i in inicios])[:n]
                redes=rng.integers(0,len(dif),len(dif)) if reamostrar else np.arange(len(dif))
                amostras.append(float(dif[redes][:,indices].mean()))
            p=publicados[nome][str(bloco)]
            np.testing.assert_allclose(p['media'],media(dif.ravel()),rtol=1e-10,atol=1e-14)
            np.testing.assert_allclose(p['ic95'],np.quantile(amostras,[.025,.975]),rtol=1e-10,atol=1e-14)
            assert p['replicas']==cfg['bootstrap']['replicas'] and p['reamostrar_seeds']==reamostrar
            n_controles+=1
    return n_controles


def conferir():
    destino=REG/'conferencia_posterior.json';assert not destino.exists(),'Não sobrescrever recibo.'
    ptr=ler_json(REG/'execucao.json');p=RAIZ/ptr['pasta']
    assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    f=ler_json(p/'congelamento.json');fecho=ler_json(p/'fechamento.json')
    assert fecho['situacao'] in ('concluido_conferido','concluido_com_falhas_operacionais')
    assert ler_json(p/'processo.json')['ativo'] is False
    pp=ler_json(REG/'fechamento.json');assert sha256(RAIZ/pp['arquivo'])==pp['sha256']
    conferir_arquivos(p,fecho['arquivos'])
    conferir_arquivos(RAIZ,f['fontes']);conferir_arquivos(p/'fontes',f['fontes'])
    conferir_arquivos(RAIZ,f['referencias']['preservacao']);conferir_arquivos(p,f['dados_preparados'])
    diagnostico=ler_json(REG/'diagnostico_previo.json');conferir_arquivos(RAIZ,diagnostico['fontes'])
    ajustes=ler_json(p/'ajustes.json')
    assert [{k:v for k,v in j.items() if k!='situacao'} for j in ajustes]==f['ajustes']
    assert len(ajustes)==20 and sum(not j['controle'] for j in ajustes)==12
    epocas={};tempos={}
    for j in ajustes:
        q=p/j['simbolo']/'ajustes'/j['id'];h=[json.loads(l) for l in (q/'epocas.jsonl').read_text(encoding='utf-8').splitlines()]
        assert j['situacao']=='concluido' and [v['epoca'] for v in h]==list(range(1,201))
        sel=ler_json(q/'selecao.json');melhor=min(h,key=lambda x:x['rmse_global_validacao_retorno'])
        assert sel['epoca']==melhor['epoca'] and sel['rmse_validacao']==melhor['rmse_global_validacao_retorno']
        assert sha256(q/sel['checkpoint'])==sel['sha256']
        assert all(v['taxa']==.01*.5**((v['epoca']-1)//100) for v in h)
        fator=f['configuracao']['moedas'][j['simbolo']]['variantes'][j['variante']]
        grupos=ler_json(q/'grupos_penalizacao.json')
        assert grupos['elementos_totais']==(136952 if fator['ramos_mamba'] else 824)
        assert all(x['weight_decay']==fator['weight_decay'] for x in grupos['parametros'])
        nome=f"{j['simbolo']}/{j['id']}";epocas[nome]=sel['epoca'];tempos[nome]=ler_json(q/'conclusao.json')['segundos']
    codigo="""from infraestrutura.artefatos import RAIZ,ler_json
from experimentos.penalizacao_seletiva_diaria.qualificacao import conferir_controle_A
from experimentos.taxa_diaria.qualificacao import iguais
p=RAIZ/ler_json(RAIZ/'registros/fechamento_ramos_diarios/execucao.json')['pasta']
f=ler_json(p/'congelamento.json')
for moeda,ref in f['referencias']['moedas'].items():
    a,l=('B','L0') if moeda=='BTCUSDT' else ('A','L')
    conferir_controle_A(p/moeda/'ajustes'/f'{a}_controle_42',RAIZ/ref['modelos'][f'{a}_42']['pasta'])
    iguais(p/moeda/'ajustes'/f'{l}_42',p/moeda/'ajustes'/f'{l}_controle_42')
print('OITO_CONTROLES_EXATOS')
"""
    r=subprocess.run(['wsl','-d','Ubuntu','--cd','/mnt/c/Users/MuriloRFM/Documents/GitHub/CryptoCasting',
        '--exec','/home/murilorfm/.venvs/cc/bin/python','-B','-c',codigo],capture_output=True,text=True)
    assert r.returncode==0 and 'OITO_CONTROLES_EXATOS' in r.stdout,r.stdout+r.stderr
    resumo={};total_carteiras=0;total_series=0;total_ic=0;total_diagnosticos=0;maxdelta=0.
    for simbolo in f['configuracao']['moedas']:
        base=p/simbolo;cfg=ler_json(base/'configuracao.json');pub=base/'publicacao'
        conferir_arquivos(base,ler_json(base/'fechamento.json')['arquivos'])
        pr=ler_json(pub/'previsao.json');op=ler_json(pub/'operacoes.json')
        diag=ler_json(pub/'diagnostico_afim.json')
        for nome,modelo in diag['modelos'].items():
            coef=np.asarray(modelo['coeficientes_canal_dia'])
            assert coef.shape==(6,14)
            for fase in ('treino','validacao','teste'):
                z=dict(np.load(pub/'diagnostico'/f'{fase}_{nome}.npz'))
                d=dict(np.load(base/'dados'/f'{fase}.npz'))
                np.testing.assert_array_equal(z['origens_ms'],d['origens_ms'])
                np.testing.assert_array_equal(z['alvo'],d['y'])
                canais=np.stack([np.sum(d['x'][:,i,:].astype(np.float64)*coef[i],axis=1) for i in range(6)],axis=1)
                np.testing.assert_allclose(canais,z['contribuicoes_canais'],rtol=1e-12,atol=1e-14)
                np.testing.assert_allclose(canais.sum(axis=1)+modelo['intercepto'],z['afim'],rtol=1e-12,atol=1e-14)
                np.testing.assert_allclose(z['previsao_sem_ramos'],z['afim'],rtol=1e-5,atol=2e-6)
                m=modelo['fases'][fase];delta=z['previsao']-z['previsao_sem_ramos']
                assert m['max_diferenca_sem_ramos']==float(abs(delta).max())
                np.testing.assert_allclose(m['rms_diferenca_sem_ramos'],np.sqrt(media(delta**2)),rtol=1e-12,atol=1e-15)
                for chave,pre in [('mse_completo','previsao'),('mse_sem_ramos','previsao_sem_ramos')]:
                    np.testing.assert_allclose(m[chave],media((z[pre]-d['y'])**2),rtol=1e-12,atol=1e-15)
                if nome.split('_')[0] in ('L','L0'):np.testing.assert_array_equal(z['previsao'],z['previsao_sem_ramos'])
                total_diagnosticos+=1
        nomes={f'{v}_{s}' for v in cfg['variantes'] for s in cfg['seeds']}|{f'{v}_ensemble' for v in cfg['variantes']}|{'naive','linear'}
        for fase in ('validacao','teste'):
            d=dict(np.load(base/'dados'/f'{fase}.npz'));series={};erros={};metricas={}
            assert set(pr['individuais_e_referencias'][fase])==nomes
            for nome in nomes:
                z=dict(np.load(pub/'previsoes'/f'{fase}_{nome}.npz'))
                for k,l in [('origens_ms','origens_ms'),('ultimo_close','ultimo_close'),('fim_alvo_ms','fim_alvo_ms'),('alvo_retorno','y')]:
                    np.testing.assert_array_equal(z[k],d[l])
                e=z['previsoes_retorno']-d['y'];mse=media([float(x)*float(x) for x in e]);naive=media(d['y']**2)
                mm=dict(mse_retorno=mse,rmse_retorno=math.sqrt(mse),mae_retorno=media(abs(e)),
                    vies_retorno=media(e),mse_naive_retorno=naive,habilidade_mse_retorno_naive=1-mse/naive)
                for k,v in mm.items():
                    antigo=pr['individuais_e_referencias'][fase][nome][k]
                    np.testing.assert_allclose(v,antigo,rtol=1e-12,atol=1e-15);maxdelta=max(maxdelta,abs(v-antigo))
                pre=z['previsoes_retorno'];y=d['y']
                if np.any(pre!=0):
                    np.testing.assert_equal((np.mean(pre[y>0]>0)+np.mean(pre[y<0]<0))/2,pr['individuais_e_referencias'][fase][nome]['acerto_balanceado'])
                else:assert pr['individuais_e_referencias'][fase][nome]['acerto_balanceado'] is None
                series[nome]=z;erros[nome]=e**2;metricas[nome]=mm;total_series+=1
            for v in cfg['variantes']:
                preco=np.mean([series[f'{v}_{s}']['previsoes'] for s in cfg['seeds']],axis=0)
                np.testing.assert_array_equal(preco,series[f'{v}_ensemble']['previsoes'])
                np.testing.assert_array_equal(preco/d['ultimo_close']-1,series[f'{v}_ensemble']['previsoes_retorno'])
                for k in metricas[f'{v}_42']:
                    np.testing.assert_allclose(media([metricas[f'{v}_{s}'][k] for s in cfg['seeds']]),pr['medias_seeds'][fase][v][k]['media'],rtol=1e-12,atol=1e-15)
            for ens in (False,True):
                matrizes={v:erros[f'{v}_ensemble'] if ens else np.array([erros[f'{v}_{s}'] for s in cfg['seeds']]) for v in cfg['variantes']}
                matrizes.update({v:erros[v] for v in ('naive','linear')})
                total_ic+=conferir_intervalos(matrizes,pr['contrastes_mse'][fase]['ensemble' if ens else 'medias_individuais'],cfg,not ens)
        cobertura={(fase,n,custo) for fase in ('validacao','teste') for n in nomes for custo in (1,2,3)}
        ok={(x['fase'],x['unidade'],x['custo']) for x in op['carteiras']}
        falhas={(x['identidade'].split('/')[0],x['identidade'].split('/')[1],int(x['identidade'].split('_')[-1])) for x in op['falhas']}
        assert len(ok)==len(op['carteiras']) and ok.isdisjoint(falhas) and ok|falhas==cobertura
        auditorias=ler_json(pub/'auditoria_operacoes.json');assert len(auditorias['auditorias'])==len(ok)
        assert len(auditorias['reproducoes_referencia'])==30
        curvas={};transicoes=0
        with zipfile.ZipFile(pub/'carteiras.zip') as z:
            assert z.testzip() is None and len(z.namelist())==2*len(ok)+len(falhas)
            for linha in op['carteiras']:
                ar=json.loads(z.read(linha['membro']+'/resultado.json'));m=linha['metricas'];assert ar['metricas']==m
                cv=dict(np.load(io.BytesIO(z.read(linha['membro']+'/curva.npz'))));eq=cv['saldos_diarios']
                pnl=math.fsum(d['pnl_movimento_contrato'] for d in ar['dias'])
                fu=math.fsum(v['valor'] for v in ar['funding']);tx=math.fsum(o['comissao'] for o in ar['ordens']);sl=math.fsum(o['custo_slippage_ticks'] for o in ar['ordens'])
                np.testing.assert_allclose(10000+pnl+fu-tx-sl,m['capital_final'],atol=1e-7,rtol=0)
                np.testing.assert_allclose(eq[-1],m['capital_final'],atol=1e-7,rtol=0)
                np.testing.assert_allclose(eq[-1]/10000-1,m['retorno_liquido'],atol=1e-12)
                np.testing.assert_allclose(cv['drawdown_acumulado'].max(),m['drawdown_maximo'],atol=1e-12)
                assert len(ar['ordens'])==m['ordens'] and not any(o['motivo']=='zerar_diario' for o in ar['ordens'])
                transicoes+=sum(a['quantidade']*b['quantidade']>0 for a,b in zip(ar['dias'],ar['dias'][1:]))
                for k,v in [('pnl_movimento_contrato',pnl),('funding',fu),('comissoes',tx),('custo_slippage_ticks',sl)]:
                    np.testing.assert_allclose(v,m[k],atol=1e-7,rtol=0)
                curvas[(linha['fase'],linha['unidade'],linha['custo'])]=eq
        for fase in ('validacao','teste'):
            for custo in (1,2,3):
                for v in cfg['variantes']:
                    ens=next((a['metricas'] for a in op['carteiras'] if a['fase']==fase and a['custo']==custo and a['unidade']==f'{v}_ensemble'),None)
                    assert op['ensemble'][fase][str(custo)][v]==ens
                    linhas=[a['metricas'] for a in op['carteiras'] if a['fase']==fase and a['custo']==custo and a['unidade'] in [f'{v}_{s}' for s in cfg['seeds']]]
                    if len(linhas)==3:
                        for k in ('capital_final','retorno_liquido','drawdown_maximo','dias_posicionado'):
                            np.testing.assert_allclose(media([a[k] for a in linhas]),op['medias_seeds'][fase][str(custo)][v][k]['media'],atol=1e-10,rtol=1e-12)
                    else:assert op['medias_seeds'][fase][str(custo)][v]['incompleto']
                if all((fase,n,custo) in curvas for n in nomes):
                    logs={n:np.diff(np.log(curvas[(fase,n,custo)])) for n in nomes}
                    for ens in (False,True):
                        matrizes={v:logs[f'{v}_ensemble'] if ens else np.array([logs[f'{v}_{s}'] for s in cfg['seeds']]) for v in cfg['variantes']}
                        matrizes.update({v:logs[v] for v in ('naive','linear')})
                        total_ic+=conferir_intervalos(matrizes,op['contrastes_log_diario'][fase][str(custo)]['ensemble' if ens else 'medias_individuais'],cfg,not ens)
        resumo[simbolo]=dict(carteiras=len(ok),falhas=len(falhas),transicoes_mesmo_lado=transicoes)
        total_carteiras+=len(cobertura)
    assert total_carteiras==288 and total_series==96 and total_diagnosticos==90
    resultado=dict(utc=agora(),situacao='aprovado',execucao=ptr,moedas=resumo,ajustes_com_200_epocas=20,
        controles_reconferidos=8,epocas_selecionadas=epocas,tempos_ajustes_segundos=tempos,
        series_recalculadas=total_series,diagnosticos_recalculados=total_diagnosticos,intervalos_recalculados=total_ic,max_divergencia_metricas=maxdelta,
        cobertura_carteiras=total_carteiras,anteriores_preservados=len(f['referencias']['preservacao']),
        fonte_sha256=sha256(__file__),novos_treinos=0,novos_backtests=0,
        limites='Não repete forward CUDA nem auditoria minuto/evento do executor. Recalcula erros, ensembles, contrastes/bootstrap e contabilidade agregada; DD conferido na curva intradiária publicada.')
    salvar_json(destino,resultado);print(json.dumps(resultado,ensure_ascii=False))


if __name__=='__main__':conferir()
