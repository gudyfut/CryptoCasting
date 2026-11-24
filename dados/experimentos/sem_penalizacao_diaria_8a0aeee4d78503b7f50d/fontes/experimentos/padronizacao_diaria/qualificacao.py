"""Qualificação técnica sem resultados de teste/mercado para escolher a correção."""
import os
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
import sys
import time
import subprocess
import inspect
import importlib.metadata
import numpy as np
import torch
from infraestrutura.artefatos import RAIZ, ler_json, salvar_json, agora, sha256
from treinamento.otimizacao import fixar_seed
from modelos.cryptomamba_diario import construir as construir_original
from entradas_modelo.padronizacao_diaria import preparar
from tests_cryptomamba_diario.test_contratos import dados_artificiais
from experimentos.cryptomamba_reproducivel.modelo import construir
from experimentos.alvo_retorno_diario.treinamento import ajustar


def ambiente():
    import mamba_ssm.modules.mamba_simple as mod
    import mamba_ssm.ops.selective_scan_interface as scan
    import causal_conv1d.cpp_functions as conv
    import selective_scan_cuda, causal_conv1d_cuda
    return {'torch':torch.__version__, 'cuda':torch.version.cuda,
            'gpu':torch.cuda.get_device_name(),
            'pacotes':{n:importlib.metadata.version(n) for n in ('mamba-ssm','causal-conv1d','numpy')},
            'fontes_backend':{m.__file__:sha256(m.__file__) for m in (mod,scan,conv,selective_scan_cuda,causal_conv1d_cuda)},
            'cublas_workspace':os.environ.get('CUBLAS_WORKSPACE_CONFIG')}


def sondar(c):
    resultados=[]
    for seed,lote in ((42,32),(17,6),(2026,1)):
        fixar_seed(seed);rede=construir(c);original=construir_original(c)
        original.load_state_dict(rede.state_dict(),strict=True)
        torch.use_deterministic_algorithms(True, warn_only=False)
        x=torch.randn(lote,6,14,device='cuda')
        y=torch.full((lote,),.01,device='cuda')
        saidas=[];grads=[];inicio=time.monotonic()
        for _ in range(20):
            rede.zero_grad(set_to_none=True);v=rede(x);torch.sqrt(((v-y)**2).mean()+1e-8).backward()
            saidas.append(v.detach().clone());grads.append({n:p.grad.detach().clone() for n,p in rede.named_parameters()})
        assert all(torch.equal(saidas[0],s) for s in saidas)
        assert all(torch.equal(grads[0][n],g[n]) for g in grads for n in g)
        original.zero_grad(set_to_none=True);o=original(x);torch.sqrt(((o-y)**2).mean()+1e-8).backward()
        # Equivalência numérica, não identidade de operações: caminhos de somas diferentes.
        torch.testing.assert_close(saidas[0],o,rtol=1e-5,atol=1e-4)
        for n,p in original.named_parameters():
            torch.testing.assert_close(grads[0][n],p.grad,rtol=1e-3,atol=1e-6)
        r={'seed':seed,'lote':lote,'repeticoes':20,'forward_exato':True,'gradientes_exatos':True,
           'equivalencia_forward_gradiente_original':True,'max_delta_forward':float((saidas[0]-o).abs().max()),
           'segundos':time.monotonic()-inicio}
        print('SONDA',r,flush=True);resultados.append(r)
        del rede,original,grads,saidas;torch.cuda.empty_cache()
    return resultados


def executar(destino):
    destino.mkdir(parents=True,exist_ok=False)
    c=ler_json(RAIZ/'configuracoes/padronizacao_diaria_001.json')
    teste=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests_padronizacao_diaria','-v'],cwd=RAIZ,capture_output=True,text=True)
    (destino/'tests.log').write_text(teste.stdout+teste.stderr,encoding='utf8')
    if teste.returncode:raise RuntimeError('Contratos herdados reprovados.')
    sondas=sondar(c)
    salvar_json(destino/'sondas.json',{'sondas':sondas,'ambiente':ambiente()})
    df=dados_artificiais();df['volume']=120000+np.arange(len(df))*5
    d=preparar(df,c)
    d={f:{k:v[:192] for k,v in fase.items()} for f,fase in d.items()}
    class Proibido(dict):
        def __getitem__(self,k):raise AssertionError('Teste acessado no treinamento.')
    d['teste']=Proibido()
    inicio=time.monotonic()
    for n in (1,2):ajustar(d,c,42,destino/f'artificial_{n}',{'tipo':'artificial_reproducao'},epocas=50)
    a=ler_json(destino/'artificial_1/conclusao.json');b=ler_json(destino/'artificial_2/conclusao.json')
    assert a['epoca_escolhida']==b['epoca_escolhida']
    np.testing.assert_array_equal(np.load(destino/'artificial_1/validacao.npz')['previsoes'],np.load(destino/'artificial_2/validacao.npz')['previsoes'])
    import json
    hist=[]
    for n in (1,2):hist.append([{k:v for k,v in json.loads(l).items() if k!='segundos'} for l in (destino/f'artificial_{n}/epocas.jsonl').read_text().splitlines()])
    assert hist[0]==hist[1]
    for arq in (destino/'artificial_1/checkpoints').glob('*.pt'):
        aa=torch.load(arq,weights_only=True)['pesos'];bb=torch.load(destino/'artificial_2/checkpoints'/arq.name,weights_only=True)['pesos']
        assert all(torch.equal(aa[k],bb[k]) for k in aa)
    r={'utc':agora(),'situacao':'aprovado','ambiente':ambiente(),'sondas':sondas,
       'repeticao_artificial':{'epocas':50,'exemplos_treino':192,'historico_exato':True,'checkpoints_exatos':True,'previsoes_exatas':True},
       'segundos_artificiais':time.monotonic()-inicio,'estimativa_segundos_grade':(time.monotonic()-inicio)/2/50*1000*(46/6)*4,
       'recarga_exata':True,'teste_inacessivel':True,'novos_treinos_mercado':0}
    salvar_json(destino/'qualificacao.json',r);print('QUALIFICACAO',r,flush=True)
    return r


if __name__=='__main__':
    import fcntl
    import traceback
    with (RAIZ/'registros/operacional_futuros/gpu.lock').open('a+b') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        ocupacao=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True)
        if ocupacao.strip():raise RuntimeError('GPU ocupada.')
        destino=RAIZ/'registros/padronizacao_diaria/qualificacoes'/agora().replace(':','').replace('+','_')
        try:
            executar(destino)
            from .ciclo import fontes
            salvar_json(RAIZ/'registros/padronizacao_diaria/qualificacao.json',{'arquivo':(destino/'qualificacao.json').relative_to(RAIZ).as_posix(),'sha256':sha256(destino/'qualificacao.json'),'fontes':fontes(),'testes_adicionais_aprovados':True})
        except BaseException:
            salvar_json(destino/'incidente.json',{'utc':agora(),'erro':traceback.format_exc()})
            raise
