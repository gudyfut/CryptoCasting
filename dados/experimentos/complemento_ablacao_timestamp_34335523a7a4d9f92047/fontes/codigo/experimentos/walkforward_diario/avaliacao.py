"""Métricas e operações em blocos independentes, sem seleção pelo teste."""
from copy import deepcopy
import io
import json
import zipfile
import numpy as np
import torch
from infraestrutura.artefatos import RAIZ, salvar_json
from experimentos.fechamento_ramos_diarios.avaliacao import medir, agregar, intervalo
from experimentos.fechamento_ramos_diarios.contratos import receita
from experimentos.generalizacao_moedas.avaliacao import carregar_mercado
from simulacao_operacoes.continuidade_diaria.simulador import simular
from simulacao_operacoes.continuidade_diaria.auditoria_grade import conferir
from .treinamento import carregar_rede, inferir


def executar(p,f,progresso):
    c=f['configuracao'];mercado=carregar_mercado(f['referencias']['mercado'])
    pub=p/'publicacao';pub.mkdir(exist_ok=False)
    resultado={};carteiras=[];auditorias=[];falhas=[]
    with zipfile.ZipFile(pub/'carteiras.zip','x',compression=zipfile.ZIP_DEFLATED) as arquivo:
        for bloco in c['blocos']:
            b=bloco['id'];base=p/b;cfg=f['configs_blocos'][b]
            with np.load(base/'dados/teste.npz',allow_pickle=False) as q:z={k:q[k].copy() for k in q.files}
            with np.load(base/'dados/validacao.npz',allow_pickle=False) as q:validacao={k:q[k].copy() for k in q.files}
            previsoes={};precos={};metricas={};contrastes={}
            for variante in c['variantes']:
                for seed in c['seeds']:
                    nome=f'{variante}_{seed}';ajuste=base/'ajustes'/nome
                    rede=carregar_rede(ajuste,receita(cfg,variante))
                    with np.load(ajuste/'validacao.npz',allow_pickle=False) as q:
                        np.testing.assert_array_equal(inferir(rede,validacao['x']),q['previsoes'])
                    previsoes[nome]=inferir(rede,z['x']);precos[nome]=z['ultimo_close']*(1+previsoes[nome])
                    metricas[nome]=medir(z['y'],previsoes[nome]);del rede;torch.cuda.empty_cache()
                nome=f'{variante}_ensemble'
                precos[nome]=np.mean([precos[f'{variante}_{s}'] for s in c['seeds']],axis=0)
                previsoes[nome]=precos[nome]/z['ultimo_close']-1;metricas[nome]=medir(z['y'],previsoes[nome])
            previsoes['naive']=np.zeros(len(z['y']));precos['naive']=z['ultimo_close'].copy();metricas['naive']=medir(z['y'],previsoes['naive'])
            for nome,prev in previsoes.items():
                d=pub/b/'previsoes';d.mkdir(parents=True,exist_ok=True)
                np.savez_compressed(d/f'{nome}.npz',previsoes_retorno=prev,previsoes=precos[nome],alvo_retorno=z['y'],
                                    origens_ms=z['origens_ms'],ultimo_close=z['ultimo_close'])
            for a,ref in (('A','L'),('A','naive'),('L','naive')):
                for forma in ('individuais','ensemble'):
                    if forma=='individuais':
                        dif=np.array([(previsoes[f'{a}_{s}']-z['y'])**2-
                             (previsoes[f'{ref}_{s}']-z['y'])**2 if ref!='naive' else
                             (previsoes[f'{a}_{s}']-z['y'])**2-z['y']**2 for s in c['seeds']])
                    else:
                        direita=previsoes[f'{ref}_ensemble'] if ref!='naive' else previsoes['naive']
                        dif=(previsoes[f'{a}_ensemble']-z['y'])**2-(direita-z['y'])**2
                    contrastes[f'{a}_menos_{ref}_{forma}']={str(n):intervalo(dif,n,c['bootstrap'],forma=='individuais') for n in c['bootstrap']['blocos']}
            resultado[b]=dict(populacao=len(z['y']),origens=[int(z['origens_ms'][0]),int(z['origens_ms'][-1])],
                              metricas=metricas,medias={v:agregar([metricas[f'{v}_{s}'] for s in c['seeds']]) for v in c['variantes']},
                              contrastes_mse=contrastes)
            for custo,slip in enumerate(c['slippage_cenarios'],1):
                regras=deepcopy(cfg['operacoes']);regras['slippage_por_lado']=slip
                for nome,prev in precos.items():
                    ident=f'{b}/{nome}/custo_{custo}'
                    try:
                        r,cv=simular(z['origens_ms'],prev,z['ultimo_close'],mercado,regras,'liquida')
                        audit=conferir(r,cv,mercado,regras,'liquida',z['origens_ms'],prev,z['ultimo_close'],None)
                    except ValueError as erro:
                        if 'Violação prudencial' not in str(erro):raise
                        falhas.append(dict(identidade=ident,erro=str(erro)))
                        arquivo.writestr(ident+'/falha.json',json.dumps(falhas[-1],ensure_ascii=False));continue
                    arquivo.writestr(ident+'/resultado.json',json.dumps(dict(regras=regras,**r),ensure_ascii=False,allow_nan=False))
                    memoria=io.BytesIO();np.savez_compressed(memoria,origens_ms=z['origens_ms'],**cv)
                    arquivo.writestr(ident+'/curva.npz',memoria.getvalue())
                    carteiras.append(dict(bloco=b,unidade=nome,custo=custo,membro=ident,metricas=r['metricas']))
                    auditorias.append(dict(identidade=ident,**audit))
                    progresso(carteiras_concluidas=len(carteiras),falhas_prudenciais=len(falhas),carteiras_previstas=108)
    assert len(carteiras)+len(falhas)==108
    with zipfile.ZipFile(pub/'carteiras.zip') as z:assert z.testzip() is None
    salvar_json(pub/'previsao.json',resultado)
    salvar_json(pub/'operacoes.json',dict(carteiras=carteiras,falhas=falhas,
                limite='Carteiras por semestre independentes; não somar retornos como carteira contínua.'))
    salvar_json(pub/'auditoria_operacoes.json',dict(auditorias=auditorias,total=len(auditorias),falhas=falhas))
    return dict(blocos=len(resultado),carteiras=len(carteiras),falhas_prudenciais=len(falhas),
                limite='Períodos retrospectivos; IC inclui dependência temporal parcial e não corrige seleção histórica.')
