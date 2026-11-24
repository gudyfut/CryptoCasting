"""Extensão identificada; somente inferência, controles e carteiras preservadas."""
import argparse
from copy import deepcopy
import io
import json
import math
import os
from pathlib import Path
import platform
import shutil
import traceback
import zipfile

import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256, identidade, conferir_arquivos
from experimentos.fechamento_ramos_diarios.avaliacao import medir, agregar, prever_linear, contrastar
from experimentos.fechamento_ramos_diarios.contratos import receita
from analises.etapas.ensemble_2026.entradas import preparar as preparar_janelas, DIA

REG = RAIZ/'registros/ablacao_linear_2026'
CFG = RAIZ/'configuracoes/ablacao_linear_2026_001.json'


def relativo(p):
    return Path(p).relative_to(RAIZ).as_posix()


def estado(situacao, **campos):
    salvar_json(REG/'estado.json', dict(utc=agora(), situacao=situacao, **campos))
    print(situacao, json.dumps(campos, ensure_ascii=False), flush=True)


def preparar():
    assert not (REG/'execucao.json').exists(), 'Identidade já existente; não duplicar.'
    c = ler_json(CFG)
    modelos = ler_json(RAIZ/c['referencia_modelos'])
    periodo = ler_json(RAIZ/c['referencia_periodo'])
    pm, pp = RAIZ/modelos['pasta'], RAIZ/periodo['pasta']
    for ptr, p in ((modelos, pm), (periodo, pp)):
        assert sha256(p/'congelamento.json') == ptr['congelamento_sha256']
        assert ler_json(p/'fechamento.json')['situacao'] == 'concluido_conferido'
    pais = {}
    def guardar(p):
        pais[relativo(p)] = sha256(p)
    # Publicações e modelos anteriores: conservar bytes, sem copiar os dados grandes.
    for raiz in (pm, pp):
        for p in raiz.rglob('*'):
            if p.is_file() and 'fontes' not in p.relative_to(raiz).parts and p.suffix in ('.json','.npz','.zip','.pt','.csv'):
                guardar(p)
    fperiodo = ler_json(pp/'congelamento.json')
    mercados = ler_json(pp/'mercados.json')
    for moeda in c['moedas']:
        indices = ler_json(pm/moeda/'modelos.json')
        for v in c['variantes']:
            for seed in c['seeds']:
                p = RAIZ/indices[f'{v}_{seed}']['pasta']
                sel = ler_json(p/'selecao.json')
                assert sel['epoca'] <= 200 and sha256(p/sel['checkpoint']) == sel['sha256']
                for nome in ('selecao.json', sel['checkpoint'], 'validacao.npz'):
                    guardar(p/nome)
        info = fperiodo['moedas'][moeda]
        for p in (RAIZ/info['base']/'escalas.json', RAIZ/info['diario']['pasta']/'diario.parquet'):
            guardar(p)
        mp = RAIZ/mercados[moeda]['pasta']
        assert sha256(mp/'manifesto.json') == mercados[moeda]['manifesto_sha256']
        conferir_arquivos(mp, ler_json(mp/'manifesto.json')['arquivos'])
        guardar(mp/'manifesto.json')
        for nome in ler_json(mp/'manifesto.json')['arquivos']:
            guardar(mp/nome)
    fontes = {relativo(p):sha256(p) for p in (RAIZ/'codigo').rglob('*.py') if '__pycache__' not in p.parts}
    for p in (CFG, RAIZ/'docs/protocolo_ablacao_linear_2026.md'):
        fontes[relativo(p)] = sha256(p)
    f = dict(utc=agora(), configuracao=c, referencia_modelos=modelos, referencia_periodo=periodo,
             fontes=fontes, pais=pais, novos_treinamentos=0)
    codigo = identidade(f)[:20]
    p = RAIZ/'dados/reavaliacoes'/f'ablacao_linear_2026_{codigo}'
    p.mkdir(parents=True, exist_ok=False)
    for nome in fontes:
        destino = p/'fontes'/nome
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(RAIZ/nome, destino)
    salvar_json(p/'congelamento.json', f)
    ptr = dict(id=codigo, pasta=relativo(p), congelamento_sha256=sha256(p/'congelamento.json'))
    salvar_json(REG/'execucao.json', ptr)
    estado('preparado', execucao=ptr, dependencias=len(pais))


def contexto():
    ptr = ler_json(REG/'execucao.json'); p = RAIZ/ptr['pasta']
    assert sha256(p/'congelamento.json') == ptr['congelamento_sha256']
    f = ler_json(p/'congelamento.json')
    conferir_arquivos(RAIZ, f['fontes']); conferir_arquivos(RAIZ, f['pais'])
    return ptr, p, f


def qualificar_janelas(pm, pp, moeda, info, mercado, c):
    z = dict(np.load(pp/'previsoes'/moeda/'entradas.npz', allow_pickle=False))
    escalas = ler_json(pm/moeda/'escalas.json')
    assert escalas == ler_json(RAIZ/info['base']/'escalas.json')
    antigo = pd.read_parquet(RAIZ/info['diario']['pasta']/'diario.parquet')
    novo = pd.read_parquet(RAIZ/mercado['pasta']/'diario.parquet')
    t = z['origens_ms']
    assert len(t) == 314 and np.all(np.diff(t) == DIA)
    assert t[0] == pd.Timestamp('2026-01-01',tz='UTC').value//1000000
    assert t[-1] == pd.Timestamp('2026-11-10',tz='UTC').value//1000000
    completo = pd.concat([antigo[antigo.open_time >= t[0]-14*DIA], novo], ignore_index=True)
    reconstruido = preparar_janelas(completo, t, c, escalas)
    for k in z: np.testing.assert_array_equal(z[k], reconstruido[k])
    # Alterar o alvo do primeiro dia não pode mudar a entrada desse dia.
    perturbado = completo.copy()
    perturbado.loc[perturbado.open_time == t[0], ['open','high','low','close','volume']] *= 2
    q = preparar_janelas(perturbado, t[:1], c, escalas)
    np.testing.assert_array_equal(q['x'][0], z['x'][0])
    assert q['y'][0] != z['y'][0] and z['x'].shape == (314,6,14)
    return z


def inferencia(p, f):
    import torch
    from mamba_ssm import Mamba
    from treinamento.otimizacao import fixar_seed
    from experimentos.fechamento_ramos_diarios.treinamento import carregar_rede, inferir
    from experimentos.padronizacao_diaria.qualificacao import ambiente
    pm, pp = RAIZ/f['referencia_modelos']['pasta'], RAIZ/f['referencia_periodo']['pasta']
    c = f['configuracao']; antigo = ler_json(pp/'congelamento.json'); mercados = ler_json(pp/'mercados.json')
    salvar_json(p/'ambiente.json', ambiente())
    controles = []; atividade = {}; resultados = {}
    for moeda in c['moedas']:
        cm = ler_json(pm/moeda/'configuracao.json'); indices = ler_json(pm/moeda/'modelos.json')
        z = qualificar_janelas(pm, pp, moeda, antigo['moedas'][moeda], mercados[moeda], cm)
        destino = p/moeda; destino.mkdir()
        salvar_json(destino/'configuracao_herdada.json',cm)
        salvar_json(destino/'modelos.json',{k:v for k,v in indices.items() if k.split('_')[0] in c['variantes']})
        np.savez_compressed(destino/'entradas.npz', **z)
        prev, precos, metricas = {}, {}, {}
        for v in c['variantes']:
            for seed in c['seeds']:
                nome = f'{v}_{seed}'; fixar_seed(seed)
                rede = carregar_rede(RAIZ/indices[nome]['pasta'], receita(cm,v))
                pesos = {k:t.detach().cpu().clone() for k,t in rede.state_dict().items()}
                for fase in ('validacao','teste'):
                    d = np.load(pm/moeda/'dados'/f'{fase}.npz', allow_pickle=False)
                    guardado = np.load(pm/moeda/'publicacao/previsoes'/f'{fase}_{nome}.npz',allow_pickle=False)
                    np.testing.assert_array_equal(inferir(rede,d['x']),guardado['previsoes_retorno'])
                ret = inferir(rede,z['x']); np.testing.assert_array_equal(ret,inferir(rede,z['x']))
                if v == 'A':
                    esperado = np.load(pp/'previsoes'/moeda/f'seed_{seed}.npz',allow_pickle=False)
                    np.testing.assert_array_equal(ret,esperado['previsoes_retorno'])
                    hooks=[m.register_forward_hook(lambda m,a,o:torch.zeros_like(o)) for m in rede.modules() if isinstance(m,Mamba)]
                    assert len(hooks)==12
                    try: sem = inferir(rede,z['x'])
                    finally:
                        for h in hooks:h.remove()
                    def sinais(a): return np.where(a>.002,1,np.where(a<-.002,-1,0))
                    atividade[f'{moeda}/{nome}'] = dict(max_diferenca=float(abs(ret-sem).max()),
                        rms_diferenca=float(np.sqrt(np.mean((ret-sem)**2))),sinais_alterados=int(np.sum(sinais(ret)!=sinais(sem))))
                    np.savez_compressed(destino/f'diagnostico_{nome}.npz',completo=ret,sem_ramos=sem)
                assert all(torch.equal(t,pesos[k]) for k,t in ((k,t.detach().cpu()) for k,t in rede.state_dict().items()))
                controles.append(dict(moeda=moeda,modelo=nome,validacao_teste_exatos=True,
                    repeticao_2026_exata=True,A_2026_anterior_exato=v=='A',pesos_intactos=True,
                    parametros=sum(t.numel() for t in rede.parameters())))
                prev[nome]=ret; precos[nome]=z['ultimo_close']*(1+ret)
                del rede; torch.cuda.empty_cache()
                estado('inferindo',modelos_concluidos=len(controles),total_modelos=24)
            nome=f'{v}_ensemble'
            precos[nome]=np.mean([precos[f'{v}_{s}'] for s in c['seeds']],axis=0)
            prev[nome]=precos[nome]/z['ultimo_close']-1
        ajuste=ler_json(pm/moeda/'publicacao/linear.json')
        prev['linear']=prever_linear(z['x'],ajuste);prev['naive']=np.zeros(len(z['y']))
        for nome in ('linear','naive'):precos[nome]=z['ultimo_close']*(1+prev[nome])
        for nome,ret in prev.items():
            metricas[nome]=medir(z['alvo_retorno'],ret)
            np.savez_compressed(destino/f'{nome}.npz',previsoes_retorno=ret,previsoes=precos[nome],
                origens_ms=z['origens_ms'],ultimo_close=z['ultimo_close'],alvo_retorno=z['alvo_retorno'])
        referencias={r:(prev[r]-z['alvo_retorno'])**2 for r in ('naive','linear')}
        medias={v:agregar([metricas[f'{v}_{s}'] for s in c['seeds']]) for v in c['variantes']}
        individuais={v:np.array([(prev[f'{v}_{s}']-z['alvo_retorno'])**2 for s in c['seeds']]) for v in c['variantes']}
        ensembles={v:(prev[f'{v}_ensemble']-z['alvo_retorno'])**2 for v in c['variantes']}
        resultados[moeda]=dict(metricas=metricas,medias_seeds=medias,
            contrastes_mse=dict(medias_individuais=contrastar(individuais,referencias,c,False),ensemble=contrastar(ensembles,referencias,c,True)))
    assert len(controles)==24
    salvar_json(p/'inferencia.json',dict(controles=controles,atividade_ramos=atividade,janelas_reconstruidas_exatas=True,
                                       causalidade_perturbacao_alvo=True,novos_treinamentos=0))
    salvar_json(p/'previsao.json',resultados)


def avaliar(p,f):
    from experimentos.generalizacao_moedas.avaliacao import carregar_mercado
    from simulacao_operacoes.continuidade_diaria.simulador import simular
    from simulacao_operacoes.continuidade_diaria.auditoria_grade import conferir
    from simulacao_operacoes.diaria_24h import arredondar_preco
    c=f['configuracao'];pp=RAIZ/f['referencia_periodo']['pasta']
    mercados=ler_json(pp/'mercados.json');antigo=ler_json(pp/'resultados.json')
    carteiras=[];controles=[];comparacoes={};auditorias=[]
    with zipfile.ZipFile(p/'carteiras.zip','x',compression=zipfile.ZIP_DEFLATED) as pacote, zipfile.ZipFile(pp/'carteiras.zip') as anterior:
        for moeda in c['moedas']:
            cm=ler_json(p/moeda/'configuracao_herdada.json');z=np.load(p/moeda/'entradas.npz')
            t,ultimo=z['origens_ms'],z['ultimo_close'];m=carregar_mercado(mercados[moeda]);curvas={}
            nomes=[f'{v}_{s}' for v in c['variantes'] for s in (*c['seeds'],'ensemble')]+['naive','linear','comprar_manter']
            for custo,slip in enumerate(c['slippage_cenarios'],1):
                regras=deepcopy(cm['operacoes']);regras['slippage_por_lado']=slip
                for nome in nomes:
                    agenda=None;modo='liquida';fixo=None
                    if nome=='comprar_manter':
                        prev=ultimo;modo='agenda';fixo=1
                        inicio=int(np.searchsorted(m['tempo'],t[0]+60000))
                        fill=arredondar_preco(float(m['negocio'][inicio,0])*(1+slip),1,regras['tick_preco'])
                        lotes=math.floor(regras['capital_inicial']*regras['fracao_nocional']/fill/regras['passo_quantidade'])
                        agenda=np.full(len(t),lotes,dtype=np.int64)
                    else:prev=np.load(p/moeda/f'{nome}.npz')['previsoes']
                    resultado,cv=simular(t,prev,ultimo,m,regras,modo,fixo,agenda)
                    auditoria=conferir(resultado,cv,m,regras,modo,t,prev,ultimo,fixo,agenda)
                    ident=f'{moeda}/{nome}/custo_{custo}'
                    if nome in ('A_ensemble','comprar_manter'):
                        unidade=nome.removeprefix('A_')
                        esperado=next(q for q in antigo['carteiras'] if q['simbolo']==moeda and q['unidade']==unidade and q['slippage_por_lado']==slip)
                        for k,v in esperado['metricas'].items():
                            if v is None:assert resultado['metricas'][k] is None
                            else:np.testing.assert_allclose(resultado['metricas'][k],v,atol=1e-7,rtol=1e-10)
                        velho=np.load(io.BytesIO(anterior.read(esperado['membro']+'/curva.npz')))
                        np.testing.assert_allclose(cv['saldos_diarios'],velho['saldos_diarios'],atol=1e-7,rtol=1e-10)
                        controles.append(ident)
                    pacote.writestr(ident+'/resultado.json',json.dumps(dict(regras=regras,**resultado),ensure_ascii=False,allow_nan=False))
                    b=io.BytesIO();np.savez_compressed(b,origens_ms=t,**cv);pacote.writestr(ident+'/curva.npz',b.getvalue())
                    carteiras.append(dict(moeda=moeda,unidade=nome,custo=custo,membro=ident,metricas=resultado['metricas']))
                    auditorias.append(dict(identidade=ident,**auditoria));curvas[(nome,custo)]=cv['saldos_diarios']
                    estado('simulando',carteiras_concluidas=len(carteiras),total=132)
            comparacoes[moeda]={}
            for custo in range(1,4):
                crescimentos={nome:np.diff(np.log(curvas[(nome,custo)])) for nome in nomes}
                refs={r:crescimentos[r] for r in ('naive','linear','comprar_manter')}
                individuais={v:np.array([crescimentos[f'{v}_{s}'] for s in c['seeds']]) for v in c['variantes']}
                ensembles={v:crescimentos[f'{v}_ensemble'] for v in c['variantes']}
                comparacoes[moeda][str(custo)]=dict(
                    medias_seeds={v:agregar([q['metricas'] for q in carteiras if q['moeda']==moeda and q['custo']==custo and q['unidade'] in [f'{v}_{s}' for s in c['seeds']]]) for v in c['variantes']},
                    contrastes=dict(medias_individuais=contrastar(individuais,refs,c,False),ensemble=contrastar(ensembles,refs,c,True)))
            del m
    assert len(carteiras)==132 and len(controles)==24
    salvar_json(p/'operacoes.json',dict(carteiras=carteiras,comparacoes=comparacoes))
    salvar_json(p/'auditoria_operacoes.json',dict(auditorias=auditorias,reproducoes=controles))


def executar():
    os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
    import fcntl
    import torch
    ptr,p,f=contexto()
    assert not (p/'fechamento.json').exists() and not (p/'incidente.json').exists()
    lock=p/'execucao.lock'
    with lock.open('x') as arquivo, (RAIZ/'registros/operacional_futuros/gpu.lock').open('a+b') as gpu:
        fcntl.flock(gpu,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert torch.cuda.is_available()
        salvar_json(p/'processo.json',dict(pid=os.getpid(),host=platform.node(),ativo=True,utc=agora()))
        try:
            inferencia(p,f);avaliar(p,f)
            contexto()
            salvar_json(p/'manifesto.json',dict(utc=agora(),arquivos={q.relative_to(p).as_posix():sha256(q) for q in p.rglob('*') if q.is_file() and 'fontes' not in q.relative_to(p).parts and q.name not in ('execucao.lock','processo.json')}))
            salvar_json(p/'fechamento.json',dict(utc=agora(),situacao='concluido_controles_aprovados',execucao=ptr,
                modelos=24,carteiras=132,controles_financeiros=24,novos_treinamentos=0,preservacao_antes_depois=True,
                manifesto_sha256=sha256(p/'manifesto.json')))
            estado('concluido_controles_aprovados',execucao=ptr,conferencia_posterior='pendente')
        except BaseException:
            salvar_json(p/'incidente.json',dict(utc=agora(),erro=traceback.format_exc()))
            estado('interrompido',execucao=ptr);raise
        finally:
            salvar_json(p/'processo.json',dict(pid=os.getpid(),host=platform.node(),ativo=False,utc=agora()))
    lock.unlink()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('acao',choices=['preparar','executar'])
    globals()[parser.parse_args().acao]()
