"""Orquestração versionada, cache probabilístico e registro de cada tentativa."""
from __future__ import annotations

import os
import shutil
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

from .arquivos import RAIZ, agora, fontes, identidade, ler_json, salvar_json, sha256
from .configuracao import carregar, celulas, FOLDS
from .dados import verificar_dataset
from .particoes import separar, ajustar_escalas
from .treino import treinar, fixar_seed
from .qualificacao import ambiente, qualificar, qualificar_ar1
from .ar1 import ajustar, probabilidades, semente_origem
from .metricas import calcular
from .financeiro import simular, comprar_manter
from .auditoria import auditar_celula
from .estatistica import comparar, incerteza_financeira
from .preparacao import auditar_preparacao
from .consolidacao import consolidar


def cache_ar1(raiz,par,fold,horas,amostras,treino):
    pasta=raiz/'cache_ar1'/f'{par}_{fold}'
    pasta.mkdir(parents=True,exist_ok=True)
    completo=pasta/'previsoes.parquet'
    if completo.exists() and (pasta/'concluido.json').exists():
        meta=ler_json(pasta/'concluido.json')
        if sha256(completo)!=meta['sha256']:
            raise ValueError('Cache AR(1) alterado.')
        return pd.read_parquet(completo),ler_json(pasta/'ajuste.json')
    ajuste=ajustar(horas,treino.origem_utc.max())
    salvar_json(pasta/'ajuste.json',ajuste)
    inicio=FOLDS[fold].limites()[2];fim=FOLDS[fold].limites()[3]
    q=amostras.loc[amostras.origem_utc.ge(inicio)&amostras.origem_utc.lt(fim)&
         (amostras.origem_utc+pd.Timedelta(hours=1,minutes=1)).lt(fim),
         ['origem_utc','indice_hora','sigma']].copy().reset_index(drop=True)
    resultados=[]
    parcial=pasta/'parcial.parquet'
    if parcial.exists() and (pasta/'parcial.json').exists():
        if sha256(parcial)!=ler_json(pasta/'parcial.json')['sha256']:
            raise ValueError('Cache AR(1) parcial alterado.')
        anterior=pd.read_parquet(parcial)
        if not anterior.origem_utc.equals(q.origem_utc.iloc[:len(anterior)]):
            raise ValueError('Prefixo do cache AR(1) não corresponde às origens.')
        resultados=anterior.filter(regex='^p_').to_numpy().tolist()
    colunas=[f'p_H{h}_{k}' for h in (1,24,168) for k in range(3)]
    for i in range(len(resultados),len(q)):
        r=q.iloc[i]
        seed=semente_origem(par,fold,r.origem_utc.isoformat())
        p=probabilidades(ajuste,float(horas.loc[int(r.indice_hora),'retorno']),float(r.sigma),[1,24,168],seed)
        resultados.append(p.ravel().tolist())
        if (i+1)%100==0 or i+1==len(q):
            salvo=q.iloc[:i+1].copy()
            salvo[colunas]=np.asarray(resultados)
            temp=pasta/'parcial.tmp.parquet';salvo.to_parquet(temp,index=False);temp.replace(parcial)
            salvar_json(pasta/'parcial.json',{'sha256':sha256(parcial),'origens':i+1,'total':len(q),'utc':agora()})
            print(f'AR(1) {par}/{fold} {i+1}/{len(q)} origens; três horizontes.',flush=True)
    q[colunas]=np.asarray(resultados)
    q.to_parquet(completo,index=False)
    salvar_json(pasta/'concluido.json',{'sha256':sha256(completo),'utc':agora()})
    return q,ajuste


def avaliar_financeiro(pasta,nome,q,minutos,primeiro_minuto,limites):
    resumo={}
    for rotulo,opcoes in [('base',{}),('custos_agravados',{'agravado':True}),
                          ('ambiguidade_superior',{'superior_ambiguo':True}),('sem_filtro',{'filtro':False})]:
        r,ordens,curva=simular(q,minutos,primeiro_minuto,limites[2],limites[3],**opcoes)
        ordens.to_parquet(pasta/nome/f'ordens_{rotulo}.parquet',index=False)
        curva.to_parquet(pasta/nome/f'curva_{rotulo}.parquet',index=False)
        resumo[rotulo]=r
        resumo[rotulo]['incerteza']=incerteza_financeira(curva)
    resumo['comprar_manter']=comprar_manter(q,minutos,primeiro_minuto,limites[2],limites[3])
    resumo['caixa']={'retorno_liquido':0.}
    salvar_json(pasta/nome/'financeiro.json',resumo)
    return resumo


def executar(configuracao: Path,dataset: Path,*,somente_pilotos=False):
    c=carregar(configuracao)
    meta=verificar_dataset(dataset)
    auditoria_dados=auditar_preparacao(dataset)
    qualificacao=qualificar()
    env=qualificacao['ambiente']
    fonte=fontes()
    assinatura={'configuracao':c,'dataset':meta['id'],'codigo':fonte,
                'ambiente':{k:env[k] for k in ('pacotes','cuda_runtime','gpu','fonte_mamba_sha256','precisao','tf32')}}
    id_ciclo=identidade(assinatura)[:20]
    raiz=RAIZ/'dados/experimentos'/f'barreiras_{id_ciclo}'
    raiz.mkdir(parents=True,exist_ok=True)
    # Lock do sistema operacional: arquivo de estado sozinho não prova processo vivo.
    import fcntl
    trava=(raiz/'execucao.lock').open('a')
    fcntl.flock(trava.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    salvar_json(raiz/'ciclo.json',{'id':id_ciclo,'assinatura':assinatura,'qualificacao':qualificacao})
    salvar_json(raiz/'auditoria_dados.json',auditoria_dados)
    grade=celulas(c)
    pilotos=[x for x in grade if x['par']=='BTCUSDT' and x['fold']=='DB1' and
             (x['contexto'],x['horizonte']) in ((24,24),(168,168))]
    grade=pilotos if somente_pilotos else pilotos+[x for x in grade if x not in pilotos]
    comuns=np.load(dataset/'origens_comuns.npy')
    for numero,celula in enumerate(grade,1):
        if fontes()!=fonte:
            raise RuntimeError('Código/protocolo mudaram durante a execução; não misturar identidades.')
        chave=identidade({'ciclo':id_ciclo,'celula':celula})[:20]
        base=raiz/chave
        candidatas=[base]+sorted(raiz.glob(f'{chave}_tentativa*'))
        concluida=next((p for p in candidatas if (p/'concluido.json').exists()),None)
        if concluida is not None:
            for rel,h in ler_json(concluida/'integridade.json').items():
                if sha256(concluida/rel)!=h:
                    raise ValueError('Execução concluída foi alterada; não reutilizar.')
            print(f'Reutilizando célula auditada {celula}',flush=True)
            continue
        # Uma tentativa interrompida não é sobrescrita. O lock obtido prova que
        # não existe outro executor ativo para esta identidade no mesmo host.
        tentativa=1
        pasta=base
        while (pasta/'estado.json').exists():
            anterior=ler_json(pasta/'estado.json')
            if anterior['status'] not in ('falha','interrompido'):
                anterior.update(status='interrompido',fim_utc=agora(),motivo='Executor anterior não mantém lock.')
                salvar_json(pasta/'estado.json',anterior)
                salvar_json(RAIZ/'historico/execucoes'/f"{anterior['id']}.json",anterior)
            tentativa+=1
            pasta=raiz/f'{chave}_tentativa{tentativa}'
        pasta.mkdir(parents=True,exist_ok=True)
        id_exec=pasta.name
        estado={'id':id_exec,'ciclo':c['ciclo'],'id_ciclo':id_ciclo,'celula':celula,'dataset':meta['id'],
                'status':'preparando','inicio_utc':agora(),'pid':os.getpid(),
                'diretorio':pasta.relative_to(RAIZ).as_posix(),'codigo':identidade(fonte)}
        def registrar():
            salvar_json(pasta/'estado.json',estado)
            salvar_json(RAIZ/'historico/execucoes'/f'{id_exec}.json',estado)
        registrar()
        try:
            print(f'Célula {numero}/{len(grade)}: {celula}',flush=True)
            salvar_json(pasta/'configuracao.json',assinatura)
            salvar_json(pasta/'ambiente.json',env)
            for relativo in fonte:
                alvo=pasta/'fontes'/relativo;alvo.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(RAIZ/relativo,alvo)
            par=celula['par'];h=celula['horizonte']
            horas=pd.read_parquet(dataset/par/'horas.parquet')
            amostras=pd.read_parquet(dataset/par/f'amostras_H{h}.parquet')
            blocos=separar(amostras,comuns,celula['fold'])
            matriz,escalas=ajustar_escalas(horas,blocos['treino'])
            salvar_json(pasta/'escalas.json',escalas)
            salvar_json(pasta/'particoes.json',{k:{'n':len(v),'primeira_origem':v.origem_utc.min().isoformat(),
                      'ultima_origem':v.origem_utc.max().isoformat()} for k,v in blocos.items()})
            qual_ar1=raiz/f'qualificacao_ar1_{par}.json'
            if not qual_ar1.exists():
                ajuste=ajustar(horas,blocos['treino'].origem_utc.max())
                qualificar_ar1(ajuste,horas,blocos['validacao'],par,celula['fold'],qual_ar1)
            elif ler_json(qual_ar1)['status']!='aprovado':
                raise ValueError('Qualificação AR(1) reprovada.')
            resultados={};previsoes={};financeiro={}
            frequencias=(np.bincount(blocos['treino'].classe,minlength=3)+.5)/(len(blocos['treino'])+1.5)
            referencia_constante={'probabilidades':frequencias.tolist(),'origens_ajuste':len(blocos['treino']),
                'metricas_teste':calcular(blocos['teste'].classe,np.tile(frequencias,(len(blocos['teste']),1)),blocos['teste'].ambiguo)}
            salvar_json(pasta/'referencia_constante.json',referencia_constante)
            for nome in ('lstm','mamba'):
                estado.update(status='treinando',modelo=nome);registrar()
                resultados[nome],previsoes[nome]=treinar(nome,c,celula,matriz,blocos,escalas,pasta/nome)
            estado.update(status='baseline');registrar()
            referencia=pd.read_parquet(dataset/par/'amostras_H1.parquet')
            cache,ajuste=cache_ar1(raiz,par,celula['fold'],horas,referencia,blocos['treino'])
            (pasta/'ar1').mkdir(exist_ok=True)
            salvar_json(pasta/'ar1/ajuste.json',ajuste)
            previsoes['ar1']={}
            for bloco in ('teste','operacional'):
                q=blocos[bloco].merge(cache[['origem_utc']+[f'p_H{h}_{k}' for k in range(3)]],
                                     on='origem_utc',how='left',validate='one_to_one',sort=False)
                q=q.rename(columns={f'p_H{h}_{k}':f'p{k}' for k in range(3)})
                q['modelo']='ar1'
                if not np.isfinite(q[['p0','p1','p2']].to_numpy()).all():
                    raise ValueError('Cache AR(1) não cobre todas as origens.')
                q.to_parquet(pasta/'ar1'/f'previsoes_{bloco}.parquet',index=False)
                previsoes['ar1'][bloco]=q
            q=previsoes['ar1']['teste']
            resultados['ar1']={'modelo':'ar1','metricas':{'teste':calcular(q.classe,q[['p0','p1','p2']].to_numpy(),q.ambiguo)}}
            salvar_json(pasta/'ar1/resultado_modelo.json',resultados['ar1'])
            estado.update(status='avaliando');registrar()
            minutos=np.load(dataset/par/'minutos.npy',mmap_mode='r')
            limites=FOLDS[celula['fold']].limites()
            for nome in ('lstm','mamba','ar1'):
                financeiro[nome]=avaliar_financeiro(pasta,nome,previsoes[nome]['operacional'],minutos,meta['primeiro_minuto'],limites)
            comparacoes={nome:comparar(previsoes['mamba']['teste'],previsoes[nome]['teste']) for nome in ('lstm','ar1')}
            salvar_json(pasta/'comparacoes.json',comparacoes)
            auditoria=auditar_celula(pasta,blocos,horas,minutos,escalas,celula,limites)
            if fontes()!=fonte:
                raise RuntimeError('Código/protocolo alterado durante treino; resultados não promovidos.')
            estado.update(status='concluida_auditada',fim_utc=agora(),resultados=resultados,
                          financeiro=financeiro,comparacoes=comparacoes,auditoria=auditoria['status'])
            estado['referencia_constante']=referencia_constante
            registrar()
            salvar_json(pasta/'concluido.json',{'id':id_exec,'fim_utc':estado['fim_utc']})
            print(f'Célula concluída e auditada: {id_exec}',flush=True)
        except Exception as erro:
            estado.update(status='falha',fim_utc=agora(),erro=f'{type(erro).__name__}: {erro}',
                          traceback=traceback.format_exc())
            registrar()
            raise
    salvar_json(raiz/'etapa_concluida.json',{'pilotos_apenas':somente_pilotos,'celulas':len(grade),'fim_utc':agora()})
    consolidar(raiz)
    trava.close()
    return raiz
