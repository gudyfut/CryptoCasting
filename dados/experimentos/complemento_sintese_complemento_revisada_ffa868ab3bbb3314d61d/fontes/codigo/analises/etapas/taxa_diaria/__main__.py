"""Recalcula métricas, seleção, ledger e contrastes de artefatos encerrados."""
import json
import math
import shutil
import traceback
from itertools import product
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256, conferir_arquivos
from analises.etapas.fechamento_diario.medidas import medir
from experimentos.taxa_diaria.comparacao import carteira_vigente


def media(v):
    v=list(v); return math.fsum(map(float,v))/len(v)


def perto(a,b): np.testing.assert_allclose(a,b,atol=1e-12,rtol=1e-10)


def historia(p):
    return [{k:v for k,v in json.loads(l).items() if k!='segundos'}
            for l in (p/'epocas.jsonl').read_text().splitlines()]


def intervalos(erros,logs):
    saida={}; n=erros.shape[1]
    for tamanho in (7,14,28):
        rng=np.random.default_rng(3105); valores=[]
        for _ in range(2000):
            sementes=rng.integers(0,3,3)
            inicios=rng.integers(0,n-tamanho+1,math.ceil(n/tamanho))
            dias=np.concatenate([np.arange(i,i+tamanho) for i in inicios])[:n]
            valores.append([media(erros[sementes][:,dias].ravel()),media(logs[sementes][:,dias].ravel())])
        a=np.array(valores)
        saida[str(tamanho)]={'delta_mse_retorno_ic95':np.quantile(a[:,0],[.025,.975]).tolist(),
                            'delta_crescimento_log_ic95':np.quantile(a[:,1],[.025,.975]).tolist()}
    return saida


def executar():
    reg=RAIZ/'registros/taxa_diaria'; ptr=ler_json(reg/'execucao.json'); p=RAIZ/ptr['pasta']
    assert ptr['id']=='64c5a9532894252c7b88'
    assert ler_json(p/'processo.json')['ativo'] is False
    destino=reg/'conferencias'/agora().replace(':','').replace('+','_'); destino.mkdir(parents=True,exist_ok=False)
    try:
        assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
        fecho_ptr=ler_json(reg/'fechamento.json'); assert sha256(RAIZ/fecho_ptr['arquivo'])==fecho_ptr['sha256']
        f=ler_json(p/'congelamento.json');c=f['configuracao'];a=RAIZ/f['antecessora']['pasta']
        fecho=ler_json(p/'fechamento.json'); conferir_arquivos(p,fecho['arquivos'])
        conferir_arquivos(p/'fontes',f['fontes']);conferir_arquivos(RAIZ,f['fontes']);conferir_arquivos(RAIZ,f['preservacao'])
        for k in ('diario','mercado_minuto'):
            base=RAIZ/f[k]['pasta'];assert sha256(base/'manifesto.json')==f[k]['manifesto_sha256']
            conferir_arquivos(base,ler_json(base/'manifesto.json')['arquivos'])
        jobs=ler_json(p/'ajustes.json')
        assert {j['id'] for j in jobs}=={'seed_42','controle_42','seed_17','seed_2026'} and len(jobs)==4
        trajetorias=[]
        for j in jobs:
            assert j['situacao']=='concluido'
            d=p/'ajustes'/j['id']; h=historia(d); sel=ler_json(d/'selecao.json')
            assert [e['epoca'] for e in h]==list(range(1,1001))
            assert sel['epoca']==min(h,key=lambda x:x['rmse_global_validacao_retorno'])['epoca']
            for e in h: assert e['taxa']==.001*.5**((e['epoca']-1)//100)
            assert sha256(d/sel['checkpoint'])==sel['sha256']
            z=np.load(d/'validacao.npz'); perto(math.sqrt(media((z['previsoes']-z['y'])**2)),sel['rmse_validacao'])
            trajetorias.append({'job':j['id'],'epocas':len(h),'epoca_escolhida':sel['epoca'],
                'rmse_validacao_escolhida':sel['rmse_validacao'],'rmse_validacao_final':h[-1]['rmse_global_validacao_retorno'],
                'perda_treino_inicial':h[0]['perda_treino_rmse_lotes'],'perda_treino_final':h[-1]['perda_treino_rmse_lotes'],
                'sonda_selecionada':ler_json(d/'observacoes/selecionado.json')['contribuicao_ramos']})
        assert historia(p/'ajustes/seed_42')==historia(p/'ajustes/controle_42')
        np.testing.assert_array_equal(np.load(p/'ajustes/seed_42/validacao.npz')['previsoes'],np.load(p/'ajustes/controle_42/validacao.npz')['previsoes'])
        assert ler_json(p/'controle.json')['aprovado']
        cmp=ler_json(p/'publicacao/comparacao.json'); previsoes=ler_json(p/'publicacao/previsao.json')
        assert {(l['fase'],l['seed']) for l in previsoes}==set(product(('validacao','teste'),c['seeds'])) and len(previsoes)==6
        diagnostico=[]; cis={}
        for fase in ('validacao','teste'):
            erros=[];logs=[]
            for seed in c['seeds']:
                za=np.load(a/'publicacao/previsoes'/f'{fase}_{seed}.npz');zb=np.load(p/'publicacao/previsoes'/f'{fase}_{seed}.npz')
                for k in ('y','origens_ms','fim_alvo_ms','ultimo_close','alvo_retorno'):np.testing.assert_array_equal(za[k],zb[k])
                y=zb['y'];u=zb['ultimo_close'];r=y/u-1
                np.testing.assert_array_equal(zb['previsoes'],u*(1+zb['previsoes_retorno']))
                if fase=='validacao':np.testing.assert_array_equal(zb['previsoes_retorno'],np.load(p/f'ajustes/seed_{seed}/validacao.npz')['previsoes'])
                for nome,z in [('referencia',za),('candidata',zb)]:
                    mm=medir(r,z['previsoes']/u-1)
                    m=next(l for l in cmp['fases'][fase]['seeds_pareadas'] if l['seed']==seed)[nome]
                    for k,alvo in [('mse','mse_retorno'),('mae','mae_retorno'),('rmse','rmse_retorno'),('vies','vies_retorno'),('acerto_sinal','acerto_sinal')]:perto(mm[k],m[alvo])
                    diagnostico.append({'fase':fase,'seed':seed,'braco':nome,'metricas':mm})
                erros.append(((zb['previsoes']-y)/u)**2-((za['previsoes']-y)/u)**2)
                oa,la=carteira_vigente(f['custos_vigentes'],(a/'publicacao/carteiras'/fase/str(seed)/'base/resultado.json').relative_to(RAIZ).as_posix())
                sb=np.load(p/'publicacao/carteiras'/fase/str(seed)/'base/curva.npz')['saldos_diarios']
                logs.append(np.diff(np.log(sb))-np.diff(np.log(la['saldos_diarios'])))
            perto(media(np.asarray(erros).ravel()),cmp['fases'][fase]['delta_mse_retorno'])
            cis[fase]=intervalos(np.asarray(erros),np.asarray(logs))
            for bloco,q in cis[fase].items():
                for k,v in q.items():perto(v,cmp['fases'][fase]['incerteza'][bloco][k])
            for campo in ('referencia','candidata','operacao_referencia','operacao_candidata'):
                linhas=cmp['fases'][fase]['seeds_pareadas']
                for k,v in cmp['fases'][fase]['medias'][campo].items():perto(media(l[campo][k] for l in linhas),v)
        carteiras=ler_json(p/'publicacao/carteiras.json'); esperado=set(product(('validacao','teste'),[str(s) for s in c['seeds']]+['ensemble','naive','sempre_comprado','sempre_vendido'],c['cenarios']))
        assert {(l['fase'],l['unidade'],l['cenario']) for l in carteiras}==esperado and len(carteiras)==70
        mercado=RAIZ/f['mercado_minuto']['pasta'];k=pd.read_parquet(mercado/'klines.parquet',columns=['open_time','open'])
        tempo=k.open_time.to_numpy();precos=k.open.to_numpy();contagem=0
        for linha in carteiras:
            d=RAIZ/linha['pasta']; ledger=ler_json(d/'resultado.json');cv=np.load(d/'curva.npz')
            assert ledger['metricas']==linha['metricas'];saldo=10000.;slip=.0001*c['cenarios'][linha['cenario']]['slippage_multiplicador']
            for o in ledger['operacoes']:
                assert o['entrada_ms']==o['origem_ms']+60000 and o['saida_ms']==o['entrada_ms']+86400000
                lado=o['lado'];q=o['quantidade'];ie=np.searchsorted(tempo,o['entrada_ms']);isai=np.searchsorted(tempo,o['saida_ms'])
                assert tempo[ie]==o['entrada_ms'] and tempo[isai]==o['saida_ms']
                arred=lambda valor,l:(math.ceil(valor/.1) if l>0 else math.floor(valor/.1))*.1
                pe=arred(precos[ie]*(1+lado*slip),lado);ps=arred(precos[isai]*(1-lado*slip),-lado)
                perto(pe,o['preco_entrada']);perto(ps,o['preco_saida'])
                perto(math.floor(saldo*.95/pe/.001)*.001,q)
                funding=-lado*q*math.fsum(e['taxa']*e['preco'] for e in o['eventos_funding'])
                comissao=q*(pe+ps)*.0005;liquido=lado*q*(ps-pe)+funding-comissao
                np.testing.assert_allclose([saldo,funding,comissao,liquido],[o['caixa_antes'],o['funding'],o['comissao'],o['pnl_liquido']],atol=1e-7,rtol=0)
                saldo+=liquido;np.testing.assert_allclose(saldo,o['caixa_depois'],atol=1e-7,rtol=0);contagem+=1
            np.testing.assert_allclose([saldo,saldo/10000-1],[ledger['metricas']['capital_final'],ledger['metricas']['retorno_liquido']],atol=1e-7,rtol=0)
            env=cv['patrimonio_envelope'];perto(np.max(1-env/np.maximum.accumulate(env)),ledger['metricas']['drawdown_maximo'])
            perto(media(np.diff(np.log(cv['saldos_diarios']))),ledger['metricas']['crescimento_log_diario'])
            if linha['unidade'] in ('naive','sempre_comprado','sempre_vendido'):
                _,la=carteira_vigente(f['custos_vigentes'],(a/'publicacao/carteiras'/linha['fase']/linha['unidade']/linha['cenario']/'resultado.json').relative_to(RAIZ).as_posix())
                np.testing.assert_array_equal(cv['saldos_diarios'],la['saldos_diarios'])
        resultado={'utc':agora(),'situacao':'aprovado','execucao':ptr,'arquivos_publicacao':len(fecho['arquivos']),
          'fontes':len(f['fontes']),'preservados':len(f['preservacao']),'ajustes':4,'carteiras':70,'operacoes_conferidas':contagem,
          'controle_historia_previsoes_selecao_exatos':True,'trajetorias':trajetorias,'diagnostico':diagnostico,'intervalos_recalculados':cis,
          'limites':'Leitura CPU sem nova inferência ou treinamento. Hashes dos pesos conferidos; igualdade numérica de todos os pesos é a evidência do controle executado em CUDA. Drawdown recalculado do envelope preservado; não reconstrói caminho intraminuto ou liquidação oficial.'}
        salvar_json(destino/'conferencia.json',resultado)
        for fonte in (Path(__file__),RAIZ/'codigo/analises/etapas/fechamento_diario/medidas.py'):
            shutil.copyfile(fonte,destino/fonte.name)
        salvar_json(reg/'conferencia_posterior.json',{'arquivo':(destino/'conferencia.json').relative_to(RAIZ).as_posix(),'sha256':sha256(destino/'conferencia.json')})
        print(json.dumps({k:v for k,v in resultado.items() if k not in ('trajetorias','diagnostico','intervalos_recalculados')},ensure_ascii=False),flush=True)
    except BaseException:
        salvar_json(destino/'incidente.json',{'utc':agora(),'erro':traceback.format_exc()});raise


if __name__=='__main__':
    from pathlib import Path
    executar()
