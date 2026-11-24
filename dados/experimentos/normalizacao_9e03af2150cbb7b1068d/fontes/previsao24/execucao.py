"""Executor retomável com tentativas imutáveis, gates e fonte congelada."""
import os
import shutil
import socket
import traceback
from pathlib import Path
import numpy as np
import pandas as pd
from .arquivos import RAIZ,agora,identidade,ler_json,salvar_json,sha256,fontes,verificar_arquivos
from .configuracao import celulas,FOLDS
from .dados import verificar_dataset,separar,ajustar_escalas
from .auditoria import auditar_modelo

def preparar_execucao(c):
    ponteiro=ler_json(RAIZ/'registros/dataset_atual.json')
    pasta=RAIZ/ponteiro['caminho']
    dataset=verificar_dataset(pasta)
    q=ler_json(RAIZ/'registros/qualificacao/cuda_atual.json')
    if sha256(RAIZ/q['caminho'])!=q['sha256']:
        raise ValueError('Qualificação adulterada.')
    qualificacao=ler_json(RAIZ/q['caminho'])
    if qualificacao['status']!='aprovado' or qualificacao['configuracao']!=c:
        raise ValueError('Qualificação incompatível.')
    verificar_arquivos(RAIZ,qualificacao['fontes'])
    if len(qualificacao['casos'])!=8:
        raise ValueError('Dimensões incompletas na qualificação.')
    testes=ler_json(RAIZ/'registros/qualificacao/testes_atual.json')
    if testes['status']!='aprovado':
        raise ValueError('Testes de contrato não aprovados.')
    verificar_arquivos(RAIZ,testes['fontes'])
    assinatura={'configuracao':c,'dataset':dataset['id'],'fontes':fontes(),'qualificacao':q,'testes':testes}
    id_execucao=identidade(assinatura)[:20]
    destino=RAIZ/'dados/experimentos'/f'retorno24_{id_execucao}'
    destino.mkdir(parents=True,exist_ok=True)
    if not (destino/'execucao.json').exists():
        for relativo in assinatura['fontes']:
            alvo=destino/'fontes'/relativo
            alvo.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(RAIZ/relativo,alvo)
        salvar_json(destino/'execucao.json',{'id':id_execucao,'assinatura':assinatura,'inicio_utc':agora(),'dataset_caminho':ponteiro['caminho']})
    verificar_arquivos(destino/'fontes',assinatura['fontes'])
    salvar_json(RAIZ/'registros/execucao_atual.json',{'id':id_execucao,'caminho':destino.relative_to(RAIZ).as_posix(),'dataset':dataset['id']})
    return destino,pasta,assinatura

def obter_lock(destino):
    caminho=destino/'processo.json'
    if caminho.exists():
        anterior=ler_json(caminho)
        pid=anterior.get('pid')
        if anterior.get('estado')=='executando' and anterior.get('host')==socket.gethostname() and pid:
            try:
                os.kill(pid,0)
            except ProcessLookupError:
                pass
            else:
                raise RuntimeError(f'Processo vivo PID {pid}; não duplicar execução.')
    salvar_json(caminho,{'pid':os.getpid(),'host':socket.gethostname(),'estado':'executando','inicio_utc':agora()})
    return caminho

def congelar(c):
    destino,_,assinatura=preparar_execucao(c)
    if not (destino/'desenvolvimento_concluido.json').exists():
        raise ValueError('Desenvolvimento não concluído.')
    exposicao=ler_json(RAIZ/'registros/exposicao_previa.json')
    if exposicao['declaracao']!='Não usei resultados de 2024–2025 para decidir o estudo':
        raise ValueError('Exposição requer outra classificação de avaliação.')
    esperadas=celulas(c,'desenvolvimento')+[{'par':p,'fold':f,'modelo':m} for f in c['folds_desenvolvimento'] for p in c['pares'] for m in ('naive','arima')]
    evidencias={}
    for celula in esperadas:
        pasta=destino/'celulas'/identidade(celula)[:20]
        aprovadas=[p for p in pasta.glob('tentativa_*') if (p/'tentativa.json').exists() and ler_json(p/'tentativa.json')['status']=='auditada']
        if len(aprovadas)!=1:
            raise ValueError(f'Célula sem resultado único auditado: {celula}')
        recibo=ler_json(aprovadas[0]/'auditoria.json')
        verificar_arquivos(aprovadas[0],recibo['arquivos'])
        evidencias[aprovadas[0].relative_to(destino).as_posix()]=sha256(aprovadas[0]/'auditoria.json')
    caminho=destino/'congelamento.json'
    if caminho.exists():
        registro=ler_json(caminho)
        if registro['assinatura']!=identidade(assinatura) or registro['auditorias_desenvolvimento']!=evidencias:
            raise ValueError('Congelamento existente diverge; não sobrescrever.')
        return caminho
    salvar_json(caminho,{'status':'congelado','utc':agora(),'assinatura':identidade(assinatura),'exposicao':exposicao,
                         'auditorias_desenvolvimento':evidencias,'regra':'Avaliar toda a grade fixa; nenhuma seleção por teste ou alteração entre B1–B4.'})
    return caminho

def tentativa(destino,celula):
    chave=identidade(celula)[:20]
    pasta=destino/'celulas'/chave
    pasta.mkdir(parents=True,exist_ok=True)
    anteriores=sorted(pasta.glob('tentativa_*'))
    for p in anteriores:
        if (p/'tentativa.json').exists():
            registro=ler_json(p/'tentativa.json')
            if registro['status']=='auditada':
                recibo=ler_json(p/'auditoria.json')
                verificar_arquivos(p,recibo['arquivos'])
                return p,True
            if registro['status']=='em_andamento':
                registro.update(status='interrompida',interrupcao_detectada_utc=agora())
                salvar_json(p/'tentativa.json',registro)
    nova=pasta/f'tentativa_{len(anteriores)+1:03d}'
    nova.mkdir()
    salvar_json(nova/'tentativa.json',{'celula':celula,'status':'em_andamento','inicio_utc':agora(),'pid':os.getpid()})
    return nova,False

def executar(c,fase,piloto=False):
    destino,pasta_dados,assinatura=preparar_execucao(c)
    if fase=='avaliacao':
        congelamento=ler_json(destino/'congelamento.json')
        if congelamento['assinatura']!=identidade(assinatura) or congelamento['status']!='congelado':
            raise ValueError('Avaliação não congelada.')
        if congelamento['exposicao']['declaracao']!='Não usei resultados de 2024–2025 para decidir o estudo':
            raise ValueError('Declaração requer classificação explícita neste contrato.')
        if not (destino/'desenvolvimento_concluido.json').exists():
            raise ValueError('Desenvolvimento incompleto.')
    lock=obter_lock(destino)
    comum=np.load(pasta_dados/'observavel_comum.npy',allow_pickle=False)
    grade=celulas(c,fase)
    if piloto:
        if fase!='desenvolvimento':
            raise ValueError('Piloto apenas no desenvolvimento.')
        grade=[x for x in grade if x['par']=='BTCUSDT' and x['fold']=='DB1' and x['contexto'] in (24,336) and x['seed']==42]
    elif not (destino/'piloto_aprovado.json').exists():
        raise ValueError('Auditar piloto curto/longo antes de liberar a grade.')
    estado={'status':'executando','fase':fase,'piloto':piloto,'planejados':len(grade),'concluidos':0,'inicio_utc':agora()}
    cache={}
    try:
        for celula in grade:
            verificar_arquivos(RAIZ,assinatura['fontes'])
            chave=(celula['par'],celula['fold'])
            if chave not in cache:
                cache.clear()
                horas=pd.read_parquet(pasta_dados/celula['par']/'horas.parquet')
                blocos=separar(horas,comum,celula['fold'])
                matriz,escalas=ajustar_escalas(horas,blocos['treino'])
                cache[chave]=(horas,blocos,matriz,escalas)
            horas,blocos,matriz,escalas=cache[chave]
            local,pronta=tentativa(destino,celula)
            if not pronta:
                registro=ler_json(local/'tentativa.json')
                try:
                    from .treino import treinar
                    treinar(c,celula,matriz,blocos,escalas,local)
                    auditar_modelo(local,blocos,celula)
                    registro.update(status='auditada',fim_utc=agora())
                except Exception as erro:
                    registro.update(status='falha',fim_utc=agora(),erro=f'{type(erro).__name__}: {erro}',traceback=traceback.format_exc())
                    raise
                finally:
                    salvar_json(local/'tentativa.json',registro)
            estado['concluidos']+=1
            estado['ultima_celula']=celula
            estado['atualizado_utc']=agora()
            salvar_json(destino/f'progresso_{fase}.json',estado)
            print(f"AUDITADA {estado['concluidos']}/{len(grade)} {celula}",flush=True)
        if piloto:
            salvar_json(destino/'piloto_aprovado.json',{'status':'aprovado','celulas':grade,'utc':agora()})
        else:
            # Referências ajustadas uma vez por moeda/fold, sem repetir em W/seeds.
            from .baselines import ajustar
            from .metricas import calcular
            folds=c['folds_desenvolvimento'] if fase=='desenvolvimento' else c['folds_avaliacao']
            for fold in folds:
                for par in c['pares']:
                    horas=pd.read_parquet(pasta_dados/par/'horas.parquet')
                    blocos=separar(horas,comum,fold)
                    for nome in ('naive','arima'):
                        celula={'par':par,'fold':fold,'modelo':nome}
                        local,pronta=tentativa(destino,celula)
                        if pronta:
                            continue
                        registro=ler_json(local/'tentativa.json')
                        try:
                            if nome=='arima':
                                ajustar(horas,blocos,c,local)
                            else:
                                resultado={'modelo':'naive','metricas':{},'parametros':0}
                                for b in ('validacao','teste','operacional'):
                                    q=blocos[b][['origem_utc','destino_utc','indice_hora','close','preco_destino','alvo']].copy()
                                    q['previsao']=0.0
                                    q.to_parquet(local/f'previsoes_{b}.parquet',index=False)
                                    if b!='operacional':
                                        resultado['metricas'][b]=calcular(q['alvo'],q['previsao'])
                                salvar_json(local/'resultado.json',resultado)
                            auditar_modelo(local,blocos,celula)
                            registro.update(status='auditada',fim_utc=agora())
                        except Exception as erro:
                            registro.update(status='falha',fim_utc=agora(),erro=f'{type(erro).__name__}: {erro}',traceback=traceback.format_exc())
                            raise
                        finally:
                            salvar_json(local/'tentativa.json',registro)
            salvar_json(destino/f'{fase}_concluido.json',{'status':'auditado','ajustes_neurais':len(grade),'referencias':32,'utc':agora()})
        estado.update(status='concluido',fim_utc=agora())
    except Exception as erro:
        estado.update(status='falha',erro=f'{type(erro).__name__}: {erro}',fim_utc=agora())
        raise
    finally:
        salvar_json(destino/f'progresso_{fase}.json',estado)
        salvar_json(lock,{'pid':os.getpid(),'host':socket.gethostname(),'estado':estado['status'],'fim_utc':agora()})
    return destino
