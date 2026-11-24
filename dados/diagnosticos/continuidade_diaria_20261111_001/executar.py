"""Continuidade diária: preparação congelada e backtest posterior sem redes."""
import argparse
from copy import deepcopy
from datetime import datetime,timezone
import hashlib
import io
import json
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
SEEDS=[42,17,2026]


def ler(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def salvar(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def utc():return datetime.now(timezone.utc).isoformat()


def preparar():
    assert not (PASTA/'congelamento.json').exists()
    anterior=ler(RAIZ/'registros/saidas_diarias/execucao.json');ap=RAIZ/anterior['pasta']
    assert sha(ap/'manifesto.json')==anterior['manifesto_sha256']
    f=ler(ap/'congelamento.json');fontes=f['fontes_externas'].copy()
    fontes['codigo/simulacao_operacoes/revisada/conta.py']=sha(RAIZ/'codigo/simulacao_operacoes/revisada/conta.py')
    for nome,h in fontes.items():assert sha(RAIZ/nome)==h,nome
    ptr=ler(RAIZ/'registros/padronizacao_diaria/execucao.json');assert ptr['pasta']==BASE
    protocolo={'versao':1,'utc':utc(),'natureza':'backtest exploratório isolado; sem treinamento e sem seleção por lucro',
        'autorizacao':'Pesquisador solicitou executar continuidade diária, com mesmas previsões/alvo95%, comparar retorno, risco e diferença efetiva.',
        'referencia':ptr,'seeds':SEEDS,'fases':['validacao','teste'],
        'unidades':['42','17','2026','ensemble','naive','sempre_comprado','sempre_vendido'],
        'modos':['diaria','liquida','agenda'],'carteiras_previstas':126,
        'hipotese':'Negociar somente a variação necessária da posição reduz giro/custos e melhora crescimento líquido frente a zerar/reabrir diariamente.',
        'primario':'delta crescimento log diário liquida menos diaria, média das três seeds; bootstrap pareado seeds/blocos14dias,2000réplicas;7/28sensibilidade',
        'secundarios':['retorno líquido','drawdown envelope mark','volume negociado','comissão','slippage/ticks','funding','exposição'],
        'modo_diaria':'zerar na fronteira24h e abrir alvo novo; controle de reprodução contra simulador e publicação financeira vigentes',
        'modo_liquida':'alvo de95% do patrimônio liquidável por dia; negociar apenas delta, fechar em caixa, fechar/abrir em inversão, liquidar no fim',
        'orcamento_comum':'patrimônio liquidável antes da decisão = colateral/PnL a preço adverso de fechamento menos comissão hipotética; serve só para dimensionar, nenhum custo fictício debitado',
        'modo_agenda':'controle auxiliar: quantidades diárias exatas herdadas do modo diária; netar deltas. Mesmo PnL bruto de contrato e funding, isola custo. Exposição proporcional não é95% do novo saldo e não é candidata principal.',
        'precos':'execução no open1m, slippage adverso, ticks e lotes herdados; mesmo arredondador científico histórico para reprodução; não certifica livro/execução',
        'funding':'histórico; fronteira pertence ao intervalo seguinte, após decisão; sem pagamento duplo ou omissão',
        'risco':'mark high/low minuto; envelope conservador com high antes de low; buffer prudencial bloqueante; não liquidação oficial',
        'exposicao':'mesmos sinais/filtro0.2%, dias e lados; quantidades principais dependem de saldo; sem SL/TP/reentrada intradiária',
        'custos':{'comissao_por_lado':.0005,'slippage_por_lado':[.0001,.0002,.0003],'natureza':'1bp provisório,2/3bp estresses'},
        'contabilidade':'caixa equivalente e quantidade assinada; auditor independente usa conta por preço médio/colateral e Decimal',
        'limites':['Receita BTC escolhida retrospectivamente;2024 selecionou checkpoints e2025 já consultado','Seeds compartilham mercado, não independência temporal','IC condicionado aos modelos e à pesquisa anterior','MSE não muda','Conta/simulação não certifica ordens reais ou taxas históricas','Média de carteiras não é ensemble; ensemble separado'],
        'qualificacao':{'testes_sinteticos':9,'falhas':0,'avisos':0,'escopo':'sem mercado, reprodução de contabilidade, agenda, inversão, cash, funding e causalidade'}}
    salvar(PASTA/'protocolo.json',protocolo)
    locais={p.name:sha(p) for p in PASTA.glob('*.py')};locais['protocolo.json']=sha(PASTA/'protocolo.json')
    c={'utc':utc(),'fontes_locais':locais,'fontes_externas':fontes,'referencia':ptr,'custos':f['custos'],'leitura_previa':anterior}
    c['id']=hashlib.sha256(json.dumps(c,sort_keys=True).encode()).hexdigest()[:20];salvar(PASTA/'congelamento.json',c)
    print(json.dumps({'id':c['id'],'carteiras':126,'fontes':len(fontes)}),flush=True)


def verificar(c):
    for nome,h in c['fontes_locais'].items():assert sha(PASTA/nome)==h,nome
    for nome,h in c['fontes_externas'].items():assert sha(RAIZ/nome)==h,nome


def intervalo(a,b,bloco):
    rng=np.random.default_rng(11112026);n=a.shape[1];v=[]
    for _ in range(2000):
        seeds=rng.integers(0,3,3);ix=(rng.integers(0,n-bloco+1,int(np.ceil(n/bloco)))[:,None]+np.arange(bloco)).ravel()[:n]
        v.append(float((a[seeds][:,ix]-b[seeds][:,ix]).mean()))
    return {'delta_crescimento_log_diario':float((a-b).mean()),'ic95':np.quantile(v,[.025,.975]).tolist(),'bloco':bloco,'replicas':2000}


def executar():
    assert not (PASTA/'resultados.json').exists() and not (PASTA/'incidente.json').exists()
    c=ler(PASTA/'congelamento.json');verificar(c)
    lock=PASTA/'execucao.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(fd)
    salvar(PASTA/'processo.json',{'utc':utc(),'host':platform.node(),'pid':os.getpid(),'python':sys.executable,'id':c['id']})
    try:
        from experimentos.generalizacao_moedas.avaliacao import carregar_mercado
        from simulacao_operacoes.diaria_24h import simular as original
        from simulacao_operacoes.diaria_24h import conferir as conferir_original
        f=ler(RAIZ/BASE/'congelamento.json');cfg=f['configuracao'];m=carregar_mercado(f['mercado_minuto'])
        assert not len(m['marca_minutos_envelope_5m']) and np.isfinite(m['negocio']).all() and np.isfinite(m['marca']).all()
        vig=ler(RAIZ/c['custos']['pasta']/'publicacao/diarias.json')[BASE]
        resultados=[];reproducoes=[];auditorias=[];curvas={};controles=[];total=0
        with zipfile.ZipFile(PASTA/'carteiras.zip','x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for fase in ['validacao','teste']:
                dados=[dict(np.load(RAIZ/BASE/'publicacao/previsoes'/f'{fase}_{s}.npz',allow_pickle=False)) for s in SEEDS]
                t=dados[0]['origens_ms'];u=dados[0]['ultimo_close']
                for d in dados[1:]:np.testing.assert_array_equal(t,d['origens_ms']);np.testing.assert_array_equal(u,d['ultimo_close'])
                unidades={str(s):(d['previsoes'],None) for s,d in zip(SEEDS,dados)}
                unidades.update(ensemble=(np.mean([d['previsoes'] for d in dados],axis=0),None),naive=(u,None),sempre_comprado=(u,1),sempre_vendido=(u,-1))
                for nome,(prev,forcar) in unidades.items():
                    for mult in [1,2,3]:
                        regras=deepcopy(cfg['operacoes']);regras['slippage_por_lado']=.0001*mult
                        ref,cv=original(t,prev,u,m,regras,{'slippage_multiplicador':1,'lado':0},forcar);conferir_original(ref,cv,regras)
                        esperado=next(x['metricas'] for x in vig['carteiras'] if x['fase']==fase and x['unidade']==nome and x['cenario']=={1:'base',2:'slippage2',3:'slippage3'}[mult])
                        for k,v in esperado.items():
                            if isinstance(v,(int,float)):np.testing.assert_allclose(v,ref['metricas'][k],atol=1e-7,rtol=1e-10,err_msg=k)
                        mapa={o['origem_ms']:o for o in ref['operacoes']}
                        agenda=[int(round(mapa[int(ts)]['lado']*mapa[int(ts)]['quantidade']/regras['passo_quantidade'])) if int(ts) in mapa else 0 for ts in t]
                        rr={}
                        for modo in ['diaria','liquida','agenda']:
                            r,curva=simular(t,prev,u,m,regras,modo,forcar,agenda if modo=='agenda' else None)
                            au=conferir(r,curva,m,regras,modo,t,prev,u,forcar,agenda if modo=='agenda' else None)
                            if modo=='diaria':
                                np.testing.assert_allclose(cv['saldos_diarios'],curva['saldos_diarios'],atol=1e-7,rtol=1e-10)
                                np.testing.assert_allclose([ref['metricas']['capital_final'],ref['metricas']['drawdown_maximo'],ref['metricas']['comissoes'],ref['metricas']['funding']],
                                    [r['metricas']['capital_final'],r['metricas']['drawdown_maximo'],r['metricas']['comissoes'],r['metricas']['funding']],atol=1e-7,rtol=1e-10)
                                assert agenda==[d['alvo_lotes'] for d in r['dias']]
                                reproducoes.append({'fase':fase,'unidade':nome,'custo':mult,'quantidades_exatas':True,'saldos_max_diferenca_usdt':float(np.max(np.abs(cv['saldos_diarios']-curva['saldos_diarios'])))})
                            rr[modo]=r['metricas'];ident=f'{fase}/{nome}/custo_{mult}/{modo}'
                            r['regras']=regras;z.writestr(ident+'/resultado.json',json.dumps(r,ensure_ascii=False,allow_nan=False))
                            b=io.BytesIO();np.savez_compressed(b,origens_ms=t,**curva);z.writestr(ident+'/curva.npz',b.getvalue())
                            resultados.append({'fase':fase,'unidade':nome,'custo':mult,'modo':modo,'membro':ident,'metricas':r['metricas']});curvas[(fase,nome,mult,modo)]=curva['saldos_diarios'];auditorias.append(dict(identidade=ident,**au))
                            total+=1;salvar(PASTA/'progresso.json',{'utc':utc(),'situacao':'executando','concluidos':total,'previstos':126,'ultima':ident})
                        for k in ['pnl_movimento_contrato','funding']:np.testing.assert_allclose(rr['diaria'][k],rr['agenda'][k],atol=1e-7,rtol=1e-10)
                        ganho=rr['agenda']['capital_final']-rr['diaria']['capital_final'];poupanca=rr['diaria']['comissoes']+rr['diaria']['custo_slippage_ticks']-rr['agenda']['comissoes']-rr['agenda']['custo_slippage_ticks']
                        np.testing.assert_allclose(ganho,poupanca,atol=1e-7,rtol=1e-10)
                        controles.append({'fase':fase,'unidade':nome,'custo':mult,'ganho_execucao_pura_usdt':ganho,'economia_comissao_usdt':rr['diaria']['comissoes']-rr['agenda']['comissoes'],
                            'economia_slippage_ticks_usdt':rr['diaria']['custo_slippage_ticks']-rr['agenda']['custo_slippage_ticks'],'gross_funding_iguais':True})
                        print('CONFERIDO',fase,nome,mult,total,'/126',flush=True)
        medias={};contrastes={}
        for fase in ['validacao','teste']:
            medias[fase]={};contrastes[fase]={}
            for mult in [1,2,3]:
                medias[fase][str(mult)]={};contrastes[fase][str(mult)]={}
                lb=np.array([np.diff(np.log(curvas[(fase,str(s),mult,'diaria')])) for s in SEEDS])
                for modo in ['diaria','liquida','agenda']:
                    rr=[x['metricas'] for x in resultados if x['fase']==fase and x['unidade'] in [str(s) for s in SEEDS] and x['custo']==mult and x['modo']==modo]
                    medias[fase][str(mult)][modo]={k:float(np.mean([v[k] for v in rr])) for k in rr[0] if all(isinstance(v[k],(int,float)) for v in rr)}
                    if modo!='diaria':
                        la=np.array([np.diff(np.log(curvas[(fase,str(s),mult,modo)])) for s in SEEDS])
                        contrastes[fase][str(mult)][modo]={str(b):intervalo(la,lb,b) for b in [7,14,28]}
        assert total==126;verificar(c)
        salvar(PASTA/'resultados.json',{'id':c['id'],'utc':utc(),'situacao':'concluido_conferido','novos_treinamentos':0,'carteiras':126,
            'medias_tres_seeds':medias,'contrastes_pareados':contrastes,'controle_execucao_pura':controles,'resultados':resultados})
        salvar(PASTA/'conferencia.json',{'id':c['id'],'utc':utc(),'fontes_antes_depois':True,'reproducoes':reproducoes,'auditorias':auditorias,
            'ordens_conferidas':sum(x['ordens'] for x in auditorias),'fundings_conferidos':sum(x['fundings'] for x in auditorias),
            'residuo_maximo_usdt':max(x['residuo_usdt'] for x in auditorias),'controle_execucao_pura':True,
            'zip_integral':zipfile.ZipFile(PASTA/'carteiras.zip').testzip(),'ambiente':{'python':sys.version,'numpy':np.__version__,'pandas':pd.__version__,'host':platform.node()}})
        salvar(PASTA/'manifesto.json',{'id':c['id'],'utc':utc(),'arquivos':{p.name:sha(p) for p in PASTA.iterdir() if p.is_file() and p.name not in ['manifesto.json','progresso.json','execucao.lock']}})
        salvar(PASTA/'progresso.json',{'utc':utc(),'situacao':'concluido_conferido','concluidos':126,'previstos':126})
        print('CONCLUIDO',c['id'],flush=True)
    except BaseException:
        salvar(PASTA/'incidente.json',{'utc':utc(),'erro':traceback.format_exc()});raise
    finally:lock.unlink()


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('acao',choices=['preparar','executar']);args=a.parse_args()
    preparar() if args.acao=='preparar' else executar()
