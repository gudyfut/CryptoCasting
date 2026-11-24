"""Qualificação do executor reutilizado e das diferenças de instrumentos."""
import os
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
import fcntl
import json
import subprocess
import sys
import time
import traceback
import numpy as np
import torch
from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256
from experimentos.padronizacao_diaria.qualificacao import ambiente, sondar
from experimentos.alvo_retorno_diario.treinamento import ajustar
from entradas_modelo.padronizacao_diaria import preparar
from qualificacao.dados_sinteticos import dados_artificiais
from .ciclo import REG, fontes


def executar():
    assert not (REG/'qualificacao.json').exists(), 'Qualificação existente: conferir, não sobrescrever'
    destino=REG/'qualificacoes'/agora().replace(':','').replace('+','_');destino.mkdir(parents=True,exist_ok=False)
    with (RAIZ/'registros/operacional_futuros/gpu.lock').open('a+b') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
        try:
            for suite in ('testes/padronizacao_diaria','testes/generalizacao_moedas'):
                r=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',suite,'-t','.','-v'],cwd=RAIZ,capture_output=True,text=True)
                (destino/(suite.replace('/','_')+'.log')).write_text(r.stdout+r.stderr,encoding='utf-8')
                assert r.returncode==0,r.stdout+r.stderr
            c=ler_json(RAIZ/'configuracoes/padronizacao_diaria_001.json');sondas=sondar(c)
            df=dados_artificiais();df['volume']=120000+np.arange(len(df))*5;d=preparar(df,c)
            d={f:{k:v[:192] for k,v in z.items()} for f,z in d.items()}
            class Proibido(dict):
                def __getitem__(self,k):raise AssertionError('Teste acessado no ajuste')
            d['teste']=Proibido();inicio=time.monotonic()
            for n in (1,2):ajustar(d,c,42,destino/f'artificial_{n}',{'tipo':'qualificacao_generalizacao'},epocas=50)
            historias=[]
            for n in (1,2):historias.append([{k:v for k,v in json.loads(l).items() if k!='segundos'} for l in (destino/f'artificial_{n}/epocas.jsonl').read_text().splitlines()])
            assert historias[0]==historias[1]
            np.testing.assert_array_equal(np.load(destino/'artificial_1/validacao.npz')['previsoes'],np.load(destino/'artificial_2/validacao.npz')['previsoes'])
            for arq in (destino/'artificial_1/checkpoints').glob('*.pt'):
                a=torch.load(arq,weights_only=True)['pesos'];b=torch.load(destino/'artificial_2/checkpoints'/arq.name,weights_only=True)['pesos']
                assert all(torch.equal(a[k],b[k]) for k in a)
            registro={'utc':agora(),'situacao':'aprovado','ambiente':ambiente(),'sondas':sondas,
                'historicos_e_checkpoints_exatos':True,'recarga_exata':True,'teste_inacessivel':True,
                'segundos_artificiais':time.monotonic()-inicio,'novos_treinos_mercado':0,
                'limite':'Qualificação sintética não substitui os três controles reais por moeda.'}
            salvar_json(destino/'qualificacao.json',registro)
            salvar_json(REG/'qualificacao.json',{'arquivo':(destino/'qualificacao.json').relative_to(RAIZ).as_posix(),
                'sha256':sha256(destino/'qualificacao.json'),'fontes':fontes()})
            print('QUALIFICACAO_APROVADA',destino,flush=True)
        except BaseException:
            salvar_json(destino/'incidente.json',{'utc':agora(),'erro':traceback.format_exc()});raise


if __name__=='__main__':executar()
