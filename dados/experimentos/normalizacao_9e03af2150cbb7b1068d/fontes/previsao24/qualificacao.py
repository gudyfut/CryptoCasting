"""Qualificação sintética, explicitamente distinta de resultados de mercado."""
import importlib.metadata
import platform
import subprocess
import warnings
import numpy as np
import torch
from .arquivos import RAIZ,agora,salvar_json,sha256,identidade
from .redes import criar
from .treino import fixar_seed

def qualificar(c):
    pasta=RAIZ/'registros/qualificacao'
    pasta.mkdir(parents=True,exist_ok=True)
    arquivos={p.relative_to(RAIZ).as_posix():sha256(p) for p in [RAIZ/'previsao24/redes.py',RAIZ/'previsao24/treino.py',RAIZ/'previsao24/qualificacao.py']}
    chave=identidade({'configuracao':c,'fontes':arquivos})[:20]
    destino=pasta/f'cuda_{chave}.json'
    if destino.exists():
        raise ValueError('Qualificação já registrada; inspecionar antes de repetir.')
    registro={'tipo':'sintetico_sem_dados_de_mercado','status':'em_andamento','inicio_utc':agora(),'configuracao':c,'fontes':arquivos,
              'python':platform.python_version(),'sistema':platform.platform(),'torch':torch.__version__,
              'versoes':{n:importlib.metadata.version(n) for n in ['mamba-ssm','causal-conv1d','numpy','pandas','pyarrow','statsmodels']},'casos':[]}
    salvar_json(destino,registro)
    try:
        if not torch.cuda.is_available():
            raise RuntimeError('CUDA indisponível.')
        registro.update(gpu=torch.cuda.get_device_name(0),memoria_total=torch.cuda.get_device_properties(0).total_memory,
                        nvidia_smi=subprocess.check_output(['nvidia-smi'],text=True),cuda=torch.version.cuda)
        for nome in ('lstm','mamba'):
            for w in c['contextos']:
                saidas=[]
                avisos=[]
                memoria=0
                with warnings.catch_warnings(record=True) as capturados:
                    warnings.simplefilter('always')
                    for repeticao in range(2):
                        fixar_seed(20261020)
                        torch.cuda.reset_peak_memory_stats()
                        rede=criar(nome,c).cuda()
                        x=torch.randn(64,w,1,device='cuda')
                        y=torch.randn(64,device='cuda')
                        otim=torch.optim.AdamW(rede.parameters(),lr=c['treino']['taxa_aprendizado'])
                        rede.train()
                        otim.zero_grad()
                        for i in (0,32):
                            perda=torch.nn.functional.mse_loss(rede(x[i:i+32]),y[i:i+32],reduction='sum')/64
                            perda.backward()
                        if not all(torch.isfinite(p.grad).all() for p in rede.parameters() if p.grad is not None):
                            raise ValueError('Gradiente não finito.')
                        otim.step()
                        rede.eval()
                        with torch.inference_mode():
                            original=rede(x).cpu().numpy()
                        recarga=criar(nome,c).cuda()
                        recarga.load_state_dict(rede.state_dict())
                        recarga.eval()
                        with torch.inference_mode():
                            refeito=recarga(x).cpu().numpy()
                        if not np.array_equal(original,refeito):
                            raise ValueError('Recarga sintética divergiu.')
                        if not np.isfinite(original).all():
                            raise ValueError('Saída não finita.')
                        saidas.append(original)
                        memoria=max(memoria,torch.cuda.max_memory_allocated())
                        del rede,recarga,otim,x,y
                        torch.cuda.empty_cache()
                    avisos=[str(a.message) for a in capturados]
                diferenca=float(np.max(np.abs(saidas[0]-saidas[1])))
                if diferenca>1e-6:
                    raise ValueError(f'Repetição sintética acima da tolerância: {diferenca}')
                registro['casos'].append({'modelo':nome,'contexto':w,'batch':64,'microbatch':32,'forward_backward':True,
                                          'recarga_exata':True,'repeticao_exata':np.array_equal(saidas[0],saidas[1]),
                                          'diferenca_repeticao':diferenca,'memoria_maxima_bytes':memoria,'avisos':avisos})
                salvar_json(destino,registro)
                print(f'Qualificado sintético: {nome}/W{w}',flush=True)
        registro.update(status='aprovado',fim_utc=agora())
    except Exception as erro:
        registro.update(status='falha',fim_utc=agora(),erro=f'{type(erro).__name__}: {erro}')
        raise
    finally:
        salvar_json(destino,registro)
    salvar_json(pasta/'cuda_atual.json',{'caminho':destino.relative_to(RAIZ).as_posix(),'sha256':sha256(destino)})
    return registro
