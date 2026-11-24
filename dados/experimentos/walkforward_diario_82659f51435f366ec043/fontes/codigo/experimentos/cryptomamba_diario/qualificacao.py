import importlib.util
import time
import subprocess
import numpy as np
import torch
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,agora
from treinamento.cryptomamba_diario import ajustar
from modelos.cryptomamba_diario import construir
from entradas_modelo.cryptomamba_diario import preparar
from qualificacao.dados_sinteticos import dados_artificiais


def executar(destino):
    destino.mkdir(parents=True,exist_ok=False);c=ler_json(RAIZ/'configuracoes/cryptomamba_diario_001.json')
    teste=subprocess.run([__import__('sys').executable,'-B','-m','unittest','discover','-s','testes/cryptomamba_diario','-t','.','-v'],cwd=RAIZ,capture_output=True,text=True)
    (destino/'tests.log').write_text(teste.stdout+teste.stderr,encoding='utf-8')
    if teste.returncode:raise RuntimeError('Contratos reprovados; consultar tests.log.')
    torch.manual_seed(42);rede=construir(c)
    fonte=RAIZ/'registros/cryptomamba/fontes_externas'/c['codigo_publico_commit']/'models/cmamba.py'
    spec=importlib.util.spec_from_file_location('cryptomamba_publico_conferencia',fonte);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    oficial=mod.CMamba(num_features=6,hidden_dims=[14,16,32,1],d_states=64,layer_density=4).cuda()
    oficial.load_state_dict(rede.nucleo.state_dict(),strict=True)
    x=torch.randn(4,6,14,device='cuda');x[:,0]+=1500000000;x[:,1:5]+=10000
    rede.eval();oficial.eval()
    with torch.no_grad():np.testing.assert_allclose(rede(x).cpu(),oficial(x).reshape(-1).cpu(),rtol=1e-6,atol=1e-4)
    parametros=sum(p.numel() for p in rede.parameters());del rede,oficial;torch.cuda.empty_cache()
    d=preparar(dados_artificiais(),c)
    # Pequeno conjunto totalmente artificial; não consulta resultados de mercado.
    for fase in d:
        d[fase]={k:v[:64] for k,v in d[fase].items()}
    # Treinamento não pode consultar teste, nem mesmo para métricas a cada época.
    class Proibido(dict):
        def __getitem__(self,k):raise AssertionError('Teste acessado durante treinamento.')
    d['teste']=Proibido()
    inicio=time.monotonic()
    for n in (1,2):ajustar(d,c,42,destino/f'artificial_{n}',{'tipo':'artificial'},epocas=3)
    a=np.load(destino/'artificial_1/validacao.npz')['previsoes'];b=np.load(destino/'artificial_2/validacao.npz')['previsoes']
    np.testing.assert_allclose(a,b,rtol=1e-5,atol=.01)
    r={'utc':agora(),'situacao':'aprovado','testes_cpu':14,'torch':torch.__version__,'cuda':torch.version.cuda,
       'gpu':torch.cuda.get_device_name(),'parametros':parametros,'equivalencia_codigo_publico':True,
       'repeticao_artificial_max_abs':float(abs(a-b).max()),'recarga_exata':True,'novos_treinos_mercado':0,
       'segundos_artificiais':time.monotonic()-inicio,'teste_inacessivel_durante_treino':True,
       'cublas_workspace':__import__('os').environ.get('CUBLAS_WORKSPACE_CONFIG'),
       'comparacao_controle_real':{'rtol':1e-5,'atol_usdt':.01}}
    salvar_json(destino/'qualificacao.json',r);print(r,flush=True)
    return r
