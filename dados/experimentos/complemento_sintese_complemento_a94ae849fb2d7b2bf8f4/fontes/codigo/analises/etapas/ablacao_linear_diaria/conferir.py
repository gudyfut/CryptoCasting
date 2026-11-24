"""Leitura posterior independente; não treina, simula ou sobrescreve o executor.

Executar somente após o fechamento: python -B -m
analises.etapas.ablacao_linear_diaria.conferir. Usa Python nativo para hashes e
WSL apenas para comparar os tensores dos controles, sem forward ou treino.
"""
import io
import json
import math
import subprocess
import zipfile
from pathlib import Path
import numpy as np
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,sha256,conferir_arquivos,agora


def conferir():
    reg=RAIZ/'registros/ablacao_linear_diaria';ptr=ler_json(reg/'execucao.json');p=RAIZ/ptr['pasta']
    destino=reg/'conferencia_posterior.json'
    if destino.exists():raise RuntimeError('Recibo posterior já existe; não sobrescrever.')
    fecho=ler_json(p/'fechamento.json')
    assert fecho['situacao']=='concluido_conferido'
    assert ler_json(p/'processo.json')['ativo'] is False
    assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    ponteiro=ler_json(reg/'fechamento.json')
    assert sha256(RAIZ/ponteiro['arquivo'])==ponteiro['sha256']
    f=ler_json(p/'congelamento.json');c=f['configuracao']
    conferir_arquivos(p,fecho['arquivos'])
    conferir_arquivos(RAIZ,f['fontes']);conferir_arquivos(p/'fontes',f['fontes'])
    conferir_arquivos(RAIZ,f['preservacao']);conferir_arquivos(p,f['dados_preparados'])
    assert ler_json(p/'controles.json')['aprovados']=={'A':True,'L':True}
    ajustes=ler_json(p/'ajustes.json')
    assert [a['id'] for a in ajustes]==['A_controle_42','L_42','L_controle_42','L_17','L_2026']
    epocas={};tempos={}
    for a in ajustes:
        q=p/'ajustes'/a['id'];h=[json.loads(l) for l in (q/'epocas.jsonl').read_text(encoding='utf8').splitlines()]
        assert [l['epoca'] for l in h]==list(range(1,201)) and a['situacao']=='concluido'
        sel=ler_json(q/'selecao.json');melhor=min(h,key=lambda v:v['rmse_global_validacao_retorno'])
        assert sel['epoca']==melhor['epoca'] and sel['rmse_validacao']==melhor['rmse_global_validacao_retorno']
        assert sha256(q/sel['checkpoint'])==sel['sha256']
        epocas[a['id']]=sel['epoca'];tempos[a['id']]=ler_json(q/'conclusao.json')['segundos']
        grupos=ler_json(q/'grupos_penalizacao.json')
        assert grupos['elementos_isentos']==0
        assert grupos['elementos_totais']==(136952 if a['variante']=='A' else 824)
        assert all(v['weight_decay']==.001 for v in grupos['parametros'])
    codigo="""from infraestrutura.artefatos import RAIZ,ler_json
from experimentos.penalizacao_seletiva_diaria.qualificacao import conferir_controle_A
from experimentos.taxa_diaria.qualificacao import iguais
p=RAIZ/ler_json(RAIZ/'registros/ablacao_linear_diaria/execucao.json')['pasta']
f=ler_json(p/'congelamento.json')
conferir_controle_A(p/'ajustes/A_controle_42',RAIZ/f['referencias']['A']['provas']['42']['pasta'])
iguais(p/'ajustes/L_42',p/'ajustes/L_controle_42')
print('CONTROLES_A_L_EXATOS')
"""
    r=subprocess.run(['wsl','-d','Ubuntu','--cd','/mnt/c/Users/MuriloRFM/Documents/GitHub/CryptoCasting',
                      '--exec','/home/murilorfm/.venvs/cc/bin/python','-B','-c',codigo],capture_output=True,text=True)
    assert r.returncode==0 and 'CONTROLES_A_L_EXATOS' in r.stdout,r.stdout+r.stderr
    pub=p/'publicacao';prev=ler_json(pub/'previsao.json');oper=ler_json(pub/'operacoes.json')
    nomes={f'{v}_{s}' for v in ('A','L') for s in (42,17,2026)}|{'A_ensemble','L_ensemble','naive','linear'}
    series={};maxdelta=0.;recalculados={}
    for fase in ('validacao','teste'):
        dados=dict(np.load(p/'dados'/f'{fase}.npz',allow_pickle=False));series[fase]={};recalculados[fase]={}
        assert set(prev['individuais_e_referencias'][fase])==nomes
        for nome in sorted(nomes):
            z=dict(np.load(pub/'previsoes'/f'{fase}_{nome}.npz',allow_pickle=False));series[fase][nome]=z
            for a,b in (('origens_ms','origens_ms'),('alvo_retorno','y'),('ultimo_close','ultimo_close'),('fim_alvo_ms','fim_alvo_ms')):
                np.testing.assert_array_equal(z[a],dados[b])
            y=z['alvo_retorno'];pr=z['previsoes_retorno'];er=pr-y;n=len(y)
            mse=math.fsum(float(v)*float(v) for v in er)/n
            base=math.fsum(float(v)*float(v) for v in y)/n
            valores={'mse_retorno':mse,'rmse_retorno':math.sqrt(mse),
                'mae_retorno':math.fsum(abs(float(v)) for v in er)/n,
                'vies_retorno':math.fsum(float(v) for v in er)/n,'mse_naive_retorno':base,
                'habilidade_mse_retorno_naive':1-mse/base}
            original=prev['individuais_e_referencias'][fase][nome]
            for k,v in valores.items():
                np.testing.assert_allclose(v,original[k],rtol=1e-12,atol=1e-15)
                maxdelta=max(maxdelta,abs(v-original[k]))
            if (pr!=0).any():
                ba=(np.mean(pr[y>0]>0)+np.mean(pr[y<0]<0))/2
                np.testing.assert_equal(ba,original['acerto_balanceado'])
                np.testing.assert_equal(np.mean(np.sign(pr)==np.sign(y)),original['acerto_sinal'])
            else:assert original['acerto_balanceado'] is None and original['acerto_sinal'] is None
            recalculados[fase][nome]=valores
        for v in ('A','L'):
            preco=np.mean([series[fase][f'{v}_{s}']['previsoes'] for s in (42,17,2026)],axis=0)
            np.testing.assert_array_equal(preco,series[fase][f'{v}_ensemble']['previsoes'])
            np.testing.assert_array_equal(preco/dados['ultimo_close']-1,series[fase][f'{v}_ensemble']['previsoes_retorno'])
            for k in recalculados[fase][f'{v}_42']:
                media=math.fsum(recalculados[fase][f'{v}_{s}'][k] for s in (42,17,2026))/3
                np.testing.assert_allclose(media,prev['medias_seeds'][fase][v][k]['media'],rtol=1e-12,atol=1e-15)
        dif=np.array([((series[fase][f'L_{s}']['previsoes_retorno']-dados['y'])**2-
                       (series[fase][f'A_{s}']['previsoes_retorno']-dados['y'])**2) for s in (42,17,2026)])
        np.testing.assert_allclose(dif.mean(),prev['contrastes_mse'][fase]['medias_individuais']['L_menos_A']['14']['media'],rtol=1e-12,atol=1e-15)
    cobertura={(fase,n,custo) for fase in ('validacao','teste') for n in nomes for custo in (1,2,3)}
    assert not oper['falhas'] and {(v['fase'],v['unidade'],v['custo']) for v in oper['carteiras']}==cobertura
    auditorias=ler_json(pub/'auditoria_operacoes.json')
    assert len(auditorias['auditorias'])==60 and len(auditorias['reproducoes_referencia'])==30
    for fase in ('validacao','teste'):
        for custo in (1,2,3):
            for variante in ('A','L'):
                linhas=[v['metricas'] for v in oper['carteiras'] if v['fase']==fase and v['custo']==custo
                        and v['unidade'] in [f'{variante}_{s}' for s in (42,17,2026)]]
                assert len(linhas)==3
                for k in ('retorno_liquido','capital_final','drawdown_maximo','dias_posicionado'):
                    media=math.fsum(v[k] for v in linhas)/3
                    np.testing.assert_allclose(media,oper['medias_seeds'][fase][str(custo)][variante][k]['media'],atol=1e-10,rtol=1e-12)
                ensemble=next(v['metricas'] for v in oper['carteiras'] if v['fase']==fase and v['custo']==custo and v['unidade']==f'{variante}_ensemble')
                assert ensemble==oper['ensemble'][fase][str(custo)][variante]
    transicoes=0
    with zipfile.ZipFile(pub/'carteiras.zip') as arquivo:
        assert arquivo.testzip() is None and len(arquivo.namelist())==120
        for linha in oper['carteiras']:
            z=json.loads(arquivo.read(linha['membro']+'/resultado.json'));m=linha['metricas'];assert z['metricas']==m
            curva=dict(np.load(io.BytesIO(arquivo.read(linha['membro']+'/curva.npz'))));eq=curva['saldos_diarios']
            bruto=math.fsum(d['pnl_movimento_contrato'] for d in z['dias'])
            funding=math.fsum(d['valor'] for d in z['funding'])
            taxa=math.fsum(o['comissao'] for o in z['ordens']);slip=math.fsum(o['custo_slippage_ticks'] for o in z['ordens'])
            np.testing.assert_allclose(10000+bruto+funding-taxa-slip,m['capital_final'],atol=1e-7,rtol=0)
            np.testing.assert_allclose(eq[-1],m['capital_final'],atol=1e-7,rtol=0)
            np.testing.assert_allclose(eq[-1]/10000-1,m['retorno_liquido'],atol=1e-12)
            np.testing.assert_allclose(np.diff(np.log(eq)).mean(),m['crescimento_log_diario'],atol=1e-12)
            np.testing.assert_allclose(curva['drawdown_acumulado'].max(),m['drawdown_maximo'],atol=1e-12)
            assert m['ordens']==len(z['ordens'])
            assert not any(o['motivo']=='zerar_diario' for o in z['ordens'])
            transicoes+=sum(a['quantidade']*b['quantidade']>0 for a,b in zip(z['dias'],z['dias'][1:]))
            for k,v in [('comissoes',taxa),('custo_slippage_ticks',slip),('funding',funding),('pnl_movimento_contrato',bruto)]:
                np.testing.assert_allclose(v,m[k],atol=1e-7,rtol=0)
    resultado={'utc':agora(),'execucao':ptr['id'],'situacao':'aprovado','fechamento':ponteiro,
        'hashes_artefatos_conferidos':len(fecho['arquivos']),'artefatos_anteriores_preservados':len(f['preservacao']),
        'fontes_congeladas':len(f['fontes']),'controles_historicos_pesos_previsoes_reconferidos':['A','L'],
        'ajustes_novos_com_200_epocas':5,'epocas_selecionadas':epocas,'tempos_ajustes_segundos':tempos,
        'series_previsao_recalculadas':20,'maxima_divergencia_metricas':maxdelta,'ensembles_recompostos_exatos':4,
        'carteiras_cobertura_exata':60,'membros_zip_integros':120,'transicoes_mesmo_lado_conferidas':transicoes,
        'reproducoes_financeiras_A_naive_executor':30,
        'novos_treinos':0,'novos_backtests':0,'fonte_conferencia':str(Path(__file__).relative_to(RAIZ)),
        'fonte_sha256':sha256(__file__),
        'limites':'Não repete forward CUDA, bootstrap ou auditoria por evento/minuto. Recalcula erros com math.fsum, ensembles, seleções e contabilidade agregada. DD conferido contra curva intradiária publicada, não reconstituído dos candles.'}
    salvar_json(destino,resultado)
    print(json.dumps(resultado,ensure_ascii=False))


if __name__=='__main__':conferir()
