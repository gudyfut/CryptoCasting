"""Rodada fechada, CPU, previsões herdadas. Preparação e execução explícitas."""
import argparse
from copy import deepcopy
from datetime import datetime,timezone
import hashlib
import io
import json
import math
import os
from pathlib import Path
import platform
import sys
import traceback
import zipfile
import numpy as np
import pandas as pd
from infraestrutura.caminhos import RAIZ
from simulador import simular
from auditoria import conferir

PASTA=Path(__file__).resolve().parent
BASE='dados/experimentos/padronizacao_diaria_f3f8772670f244779ad7'
SEEDS=(42,17,2026)


def ler(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for q in iter(lambda:f.read(8*1024*1024),b''):h.update(q)
    return h.hexdigest()
def salvar(p,d):
    Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def utc():return datetime.now(timezone.utc).isoformat()


def preparar():
    assert not (PASTA/'congelamento.json').exists(),'Já preparado; não reescrever identidade.'
    ptr=ler(RAIZ/'registros/padronizacao_diaria/execucao.json');base=RAIZ/BASE
    assert ptr['pasta']==BASE and sha(base/'congelamento.json')==ptr['congelamento_sha256']
    f=ler(base/'congelamento.json');cp=ler(RAIZ/'registros/custos_vigentes/vigente.json');cust=RAIZ/cp['pasta']
    assert sha(cust/'publicacao_manifesto.json')==cp['manifesto_sha256'];cm=ler(cust/'publicacao_manifesto.json')
    fe=ler(RAIZ/'registros/padronizacao_diaria/fechamento.json')
    assert sha(RAIZ/fe['arquivo'])==fe['sha256'];fechamento=ler(RAIZ/fe['arquivo'])
    fontes={};adicionar=lambda p:fontes.update({p.relative_to(RAIZ).as_posix():sha(p)})
    for p in [base/'congelamento.json',RAIZ/fe['arquivo'],RAIZ/'registros/custos_vigentes/vigente.json',cust/'publicacao_manifesto.json',RAIZ/'configuracoes/custos_vigentes_001.json']:
        adicionar(p)
    for arq in ['publicacao/diarias.json','publicacao/resumo.json']:
        p=cust/arq;assert sha(p)==cm['arquivos'][arq];adicionar(p)
    for chave,arquivos in [('diario',['diario.parquet']),('mercado_minuto',['klines.parquet','markPriceKlines.parquet','funding.parquet'])]:
        p=RAIZ/f[chave]['pasta'];assert sha(p/'manifesto.json')==f[chave]['manifesto_sha256'];adicionar(p/'manifesto.json')
        man=ler(p/'manifesto.json')
        for nome in arquivos:
            assert sha(p/nome)==man['arquivos'][nome];adicionar(p/nome)
    for fase in ['validacao','teste']:
        for seed in SEEDS:
            nome=f'publicacao/previsoes/{fase}_{seed}.npz';p=base/nome
            assert sha(p)==fechamento['arquivos'][nome];adicionar(p)
    for p in [RAIZ/'codigo/simulacao_operacoes/diaria_24h.py',RAIZ/'codigo/experimentos/generalizacao_moedas/avaliacao.py',RAIZ/'codigo/simulacao_operacoes/envelopes_marcacao.py']:
        adicionar(p)
    diario=pd.read_parquet(RAIZ/f['diario']['pasta']/'diario.parquet')
    inicio,fim=[int(pd.Timestamp(d,tz='UTC').timestamp()*1000) for d in f['configuracao']['periodos']['treino']]
    q=diario[(diario.open_time>=inicio)&(diario.open_time<fim)]
    assert np.all(np.diff(q.open_time)==86400000)
    retornos=np.diff(q.close.to_numpy(float))/q.close.to_numpy(float)[:-1]
    distancia=math.fsum(np.abs(retornos))/len(retornos)
    protocolo={'versao':1,'utc':utc(),'natureza':'exploracao retrospectiva isolada, sem seleção por lucro',
        'autorizacao':'Pesquisador solicitou testar TP/SL 1:1 e somente SL, com melhor referência preditiva e sem treinamento; scripts e resultados separados.',
        'referencia':ptr,'criterio_modelo':'Menor MSE médio de retorno entre receitas diárias completas de BTC discutidas; padronizada, três seeds, sem escolher seed.',
        'novos_treinamentos':0,'politicas':['prazo','stop_take','stop'],'seeds':list(SEEDS),
        'unidades':['42','17','2026','ensemble','naive','sempre_comprado','sempre_vendido'],
        'fases':['validacao','teste'],'slippage_por_lado':[.0001,.0002,.0003],
        'distancia':{'metodo':'media absoluta dos retornos simples close/close dos candles completos 2020-2023; sem retorno atravessando início do treino',
            'valor':distancia,'n':len(retornos),'primeiro_candle_ms':int(q.open_time.iloc[0]),'ultimo_candle_ms':int(q.open_time.iloc[-1]),
            'fixa':True,'multiplicador':1.,'sem_busca':True},
        'comparacoes':['stop_take menos prazo','stop menos prazo'],
        'metrica_principal_operacional':'diferença pareada de crescimento log diário; retorno/drawdown/exposição complementares',
        'incerteza':{'replicas':2000,'blocos_dias':[7,14,28],'principal':14,'seed':11112026,'correcao_duas_comparacoes':'IC97.5% por contraste (Bonferroni), condicionado a busca anterior'},
        'ambiguidades':'abertura precede extremos; duplo toque intraminuto usa SL primeiro no principal, TP primeiro somente sensibilidade',
        'execucao':'gatilho em high/low do contrato; ordens mercado aproximadas, slippage adverso e ticks; SL em gap usa abertura, TP em gap conserva barreira',
        'tempo':'toque tem minuto conhecido, segundo desconhecido; saída fim desse minuto; funding no início do minuto incluído; prazo exato 24h após entrada',
        'risco':'envelope conservador de mark inclui todo minuto do toque; pode incluir extremos posteriores à saída; não é drawdown de ticks nem limite de perda garantido',
        'manter':'mesmos sinais/filtro0.2%/origens/latência1min/capital10000/nocional95%/lote/tick/comissão0.05%/funding; sem reentrada até próxima origem; tamanhos dependem do saldo',
        'limites':['2024 selecionou checkpoints;2025 já consultado; referência escolhida retrospectivamente','1bp é provisório, não custo histórico certificado','previsão terminal não prevê primeiro toque; MSE não muda','simulação não certifica livro, liquidação ou preenchimento real','seeds não são mercados independentes','inclusão no artigo pode ser decidida depois; evidência de execução não será apagada por resultado ruim'],
        'orcamento_carteiras':168}
    salvar(PASTA/'protocolo.json',protocolo)
    locais={p.name:sha(p) for p in PASTA.glob('*.py')};locais['protocolo.json']=sha(PASTA/'protocolo.json')
    congelado={'utc':utc(),'fontes_externas':fontes,'fontes_locais':locais,'referencia':ptr,'custos':cp}
    congelado['id']=hashlib.sha256(json.dumps(congelado,sort_keys=True).encode()).hexdigest()[:20]
    salvar(PASTA/'congelamento.json',congelado)
    print(json.dumps({'id':congelado['id'],'distancia_pct':distancia*100,'retornos_treino':len(retornos),'fontes':len(fontes),'carteiras':168}),flush=True)


def verificar(cong):
    for nome,h in cong['fontes_locais'].items():assert sha(PASTA/nome)==h,nome
    for nome,h in cong['fontes_externas'].items():assert sha(RAIZ/nome)==h,nome


def intervalo(logs_a,logs_b,bloco):
    rng=np.random.default_rng(11112026);n=logs_a.shape[1];amostra=[]
    for _ in range(2000):
        s=rng.integers(0,3,3);ix=(rng.integers(0,n-bloco+1,int(np.ceil(n/bloco)))[:,None]+np.arange(bloco)).ravel()[:n]
        amostra.append(float((logs_a[s][:,ix]-logs_b[s][:,ix]).mean()))
    return {'delta_media':float((logs_a-logs_b).mean()),'ic95':np.quantile(amostra,[.025,.975]).tolist(),
        'ic97_5_duas_comparacoes':np.quantile(amostra,[.0125,.9875]).tolist()}


def executar():
    assert not (PASTA/'resultados.json').exists(),'Execução encerrada não reaberta.'
    c=ler(PASTA/'congelamento.json');verificar(c)
    lock=PASTA/'execucao.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(fd)
    processo={'pid':os.getpid(),'host':platform.node(),'utc':utc(),'python':sys.executable,'id':c['id']};salvar(PASTA/'processo.json',processo)
    try:
        from experimentos.generalizacao_moedas.avaliacao import carregar_mercado
        from simulacao_operacoes.diaria_24h import simular as original
        from simulacao_operacoes.diaria_24h import conferir as conferir_original
        f=ler(RAIZ/BASE/'congelamento.json');cfg=f['configuracao'];m=carregar_mercado(f['mercado_minuto'])
        assert not len(m['marca_minutos_envelope_5m'])
        assert np.isfinite(m['negocio']).all() and np.isfinite(m['marca']).all()
        protocolo=ler(PASTA/'protocolo.json');distancia=protocolo['distancia']['valor'];base=RAIZ/BASE
        vig=ler(RAIZ/c['custos']['pasta']/'publicacao/diarias.json')[BASE]
        resultados=[];reproducoes=[];auditorias=[];curvas={};total=0
        with zipfile.ZipFile(PASTA/'carteiras.zip','x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for fase in protocolo['fases']:
                dados=[dict(np.load(base/'publicacao/previsoes'/f'{fase}_{s}.npz',allow_pickle=False)) for s in SEEDS]
                t=dados[0]['origens_ms'];u=dados[0]['ultimo_close']
                for d in dados[1:]:
                    np.testing.assert_array_equal(t,d['origens_ms']);np.testing.assert_array_equal(u,d['ultimo_close'])
                    np.testing.assert_array_equal(dados[0]['y'],d['y'])
                unidades={str(s):(d['previsoes'],None) for s,d in zip(SEEDS,dados)}
                unidades.update(ensemble=(np.mean([d['previsoes'] for d in dados],axis=0),None),naive=(u,None),sempre_comprado=(u,1),sempre_vendido=(u,-1))
                for unidade,(prev,forcar) in unidades.items():
                    for mult in (1,2,3):
                        regras=deepcopy(cfg['operacoes']);regras['slippage_por_lado']=.0001*mult
                        antigo,cv=original(t,prev,u,m,regras,{'slippage_multiplicador':1,'lado':0},forcar)
                        conferir_original(antigo,cv,regras)
                        esperado=next(x['metricas'] for x in vig['carteiras'] if x['fase']==fase and x['unidade']==unidade and x['cenario']=={1:'base',2:'slippage2',3:'slippage3'}[mult])
                        for nome,v in esperado.items():
                            if isinstance(v,(int,float)):np.testing.assert_allclose(v,antigo['metricas'][nome],rtol=1e-10,atol=1e-7,err_msg=nome)
                        for politica,desempate in [('prazo','stop'),('stop','stop'),('stop_take','stop'),('stop_take','take')]:
                            r,curva=simular(t,prev,u,m,regras,distancia,politica,desempate,forcar)
                            if politica=='prazo':
                                for nome,v in antigo['metricas'].items():
                                    if isinstance(v,(int,float)):np.testing.assert_allclose(v,r['metricas'][nome],rtol=1e-10,atol=1e-7,err_msg=nome)
                                np.testing.assert_array_equal(cv['saldos_diarios'],curva['saldos_diarios'])
                                reproducoes.append({'fase':fase,'unidade':unidade,'mult':mult,'metricas_e_saldos_exatos':True})
                            au=conferir(r,curva,m,regras,distancia,politica,desempate,t,prev,u,forcar)
                            ident=f'{fase}/{unidade}/custo_{mult}/{politica}_{desempate}'
                            r['regras']=regras;r['distancia']=distancia
                            z.writestr(ident+'/resultado.json',json.dumps(r,ensure_ascii=False,allow_nan=False))
                            bio=io.BytesIO();np.savez_compressed(bio,origens_ms=t,**curva);z.writestr(ident+'/curva.npz',bio.getvalue())
                            resultados.append({'fase':fase,'unidade':unidade,'slippage_multiplicador':mult,'politica':politica,'desempate':desempate,'membro':ident,'metricas':r['metricas']})
                            auditorias.append(dict(identidade=ident,**au));curvas[(fase,unidade,mult,politica,desempate)]=curva['saldos_diarios']
                            total+=1;salvar(PASTA/'progresso.json',{'utc':utc(),'situacao':'executando','concluidos':total,'previstos':168,'ultima':ident})
                        print('CONFERIDO',fase,unidade,mult,'carteiras',total,'/168',flush=True)
        medias={};contrastes={}
        for fase in protocolo['fases']:
            medias[fase]={};contrastes[fase]={}
            for mult in (1,2,3):
                medias[fase][str(mult)]={};contrastes[fase][str(mult)]={}
                logs_b=np.array([np.diff(np.log(curvas[(fase,str(s),mult,'prazo','stop')])) for s in SEEDS])
                for pol in ['prazo','stop','stop_take']:
                    rr=[x['metricas'] for x in resultados if x['fase']==fase and x['unidade'] in [str(s) for s in SEEDS] and x['slippage_multiplicador']==mult and x['politica']==pol and x['desempate']=='stop']
                    medias[fase][str(mult)][pol]={k:float(np.mean([r[k] for r in rr])) for k in rr[0] if all(isinstance(r[k],(int,float)) for r in rr)}
                    if pol!='prazo':
                        logs=np.array([np.diff(np.log(curvas[(fase,str(s),mult,pol,'stop')])) for s in SEEDS])
                        contrastes[fase][str(mult)][pol]={str(b):intervalo(logs,logs_b,b) for b in [7,14,28]}
        assert total==168
        verificar(c)
        salvar(PASTA/'resultados.json',{'id':c['id'],'utc':utc(),'situacao':'concluido_conferido','novos_treinamentos':0,'distancia_pct':distancia*100,
            'carteiras':total,'medias_tres_seeds':medias,'contrastes_pareados':contrastes,'resultados':resultados,'limites':protocolo['limites']})
        salvar(PASTA/'conferencia.json',{'id':c['id'],'utc':utc(),'reproducoes_prazo':reproducoes,'auditorias':auditorias,
            'fontes_antes_depois_iguais':True,'zip_integral':zipfile.ZipFile(PASTA/'carteiras.zip').testzip(),
            'operacoes_conferidas':sum(x['operacoes_conferidas'] for x in auditorias),'residuo_maximo_usdt':max(x['residuo_maximo_usdt'] for x in auditorias),
            'ambiente':{'python':sys.version,'numpy':np.__version__,'pandas':pd.__version__,'host':platform.node()},'novos_treinamentos':0})
        salvar(PASTA/'manifesto.json',{'id':c['id'],'utc':utc(),'arquivos':{p.name:sha(p) for p in PASTA.iterdir() if p.is_file() and p.name not in ['manifesto.json','progresso.json','execucao.lock','execucao.log']}})
        salvar(PASTA/'progresso.json',{'utc':utc(),'situacao':'concluido_conferido','concluidos':168,'previstos':168})
        print('CONCLUIDO',c['id'],flush=True)
    except BaseException:
        salvar(PASTA/'incidente.json',{'utc':utc(),'erro':traceback.format_exc()});raise
    finally:lock.unlink()


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('acao',choices=['preparar','executar']);x=a.parse_args()
    preparar() if x.acao=='preparar' else executar()
