"""Unidade WSL: uma tarefa qualificada, nunca retoma/sobrescreve tentativa."""
import argparse
import os
import socket
import subprocess
import time
import traceback
from datetime import datetime
from pathlib import Path
import numpy as np
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,sha256,conferir_arquivos,agora
from entradas_modelo.operacional_futuros import preparar
from simulacao_operacoes.operacional.mercado import carregar
from simulacao_operacoes.operacional.motor import gerar_alvos
from treinamento.operacional_futuros import ajustar
from .receitas import validar


def executar_interno(pasta_job):
    p=RAIZ/pasta_job;job=ler_json(p/'job.json')
    raiz=RAIZ/job['execucao_pasta'];freeze=ler_json(raiz/'congelamento.json')
    ptr=ler_json(RAIZ/'registros/operacional_futuros/execucao.json')
    if sha256(raiz/'congelamento.json')!=ptr['congelamento_sha256'] or ptr['id']!=freeze['id']:
        raise ValueError('Ponteiro/congelamento divergentes.')
    jobs=ler_json(raiz/'ajustes.json')
    if not 1<=len(jobs)<=185 or jobs[-1]!=job or job['status']!='iniciado':
        raise ValueError('Job sem autorização no orçamento sequencial.')
    if time.time()+2700>datetime.fromisoformat(freeze['sessao']['limite_novos_trabalhos_utc']).timestamp():
        raise ValueError('Job sem reserva temporal.')
    if not p.resolve().is_relative_to(raiz.resolve()): raise ValueError('Destino fora da execução.')
    conferir_arquivos(RAIZ,freeze['fontes'])
    if job['execucao_id']!=freeze['id'] or not freeze['autorizacao']['treinamento']:
        raise ValueError('Identidade/autorização incompatível.')
    validar(job['receita'])
    if ler_json(raiz/'receitas.json')[job['receita_id']]!=job['receita']:
        raise ValueError('Receita diferente do registro.')
    if job['controle'] not in (False,True): raise ValueError('Controle não identificado.')
    final=job['recorte']['id'].startswith('B')
    if final and not (raiz/'finalista_congelada.json').exists():
        raise ValueError('Proibido ler avaliação final antes do congelamento da finalista.')
    if final:
        escolha=ler_json(raiz/'finalista_congelada.json')
        if job['receita_id'] not in ('R0',escolha['id']): raise ValueError('Receita final não autorizada.')
    mercado,h=carregar(final=final)
    alvos=None
    if job['receita']['familia_alvo']=='payoff':
        k,razao=job['receita']['barreiras_payoff']
        alvos,realizacao,motivos=gerar_alvos(mercado,h,k,razao)
    dados=preparar(h,job['receita'],job['recorte'],alvos)
    if alvos is not None:
        for nome,ids in dados.indices.items():
            if (realizacao[ids]>dados.origens_ms[ids,None]+1442*60000).any():
                raise ValueError('Realização alvo excede purga.')
        np.savez_compressed(p/'contrato_alvos.npz',alvos=alvos,realizacao_ms=realizacao,motivos=motivos)
    salvar_json(p/'contrato_dados.json',{'canais':list(dados.canais),'contexto':dados.contexto,
        'dimensao_alvo':dados.alvo.shape[1],'origens':{k:{'n':len(v),'primeira_ms':int(dados.origens_ms[v[0]]),
        'ultima_ms':int(dados.origens_ms[v[-1]])} for k,v in dados.indices.items()}})
    vinculo={'execucao':freeze['id'],'job':job['id'],'receita':job['receita_id'],'recorte':job['recorte']['id'],
             'seed':job['seed'],'controle':job['controle']}
    ajustar(dados,job['receita'],job['seed'],p/'ajuste',vinculo)
    conferir_arquivos(RAIZ,freeze['fontes'])
    salvar_json(p/'conferido.json',{'status':'concluido','checkpoint_e_previsoes_recarregados':True,
        'conclusao_sha256':sha256(p/'ajuste/conclusao.json')})


def executar(pasta_job):
    import fcntl
    p=RAIZ/pasta_job
    with (RAIZ/'registros/operacional_futuros/gpu.lock').open('a+b') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        consulta=subprocess.run(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],capture_output=True,text=True,check=True)
        if consulta.stdout.strip(): raise RuntimeError('GPU já tem processo de cálculo; não duplicar execução.')
        proc={'pid':os.getpid(),'host':socket.gethostname(),'boot':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
              'utc':agora(),'ativo':True}
        salvar_json(p/'processo_linux.json',proc)
        try: executar_interno(pasta_job)
        except BaseException:
            salvar_json(p/'incidente_worker.json',{'utc':agora(),'erro':traceback.format_exc()});raise
        finally:
            proc.update(ativo=False,encerramento_utc=agora());salvar_json(p/'processo_linux.json',proc)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('job');args=a.parse_args();executar(args.job)
