"""Gates para a mudança única de penalização; registros exclusivos deste ciclo."""
import copy
import importlib.metadata
import inspect
import platform
import subprocess
import warnings
import numpy as np
import torch
from previsao24.arquivos import RAIZ,agora,ler_json,salvar_json,sha256
from previsao24.redes import criar
from previsao24.treino import fixar_seed
from .otimizador import criar_otimizador,grupos_parametros,descrever_grupos


def ambiente():
    import mamba_ssm.modules.mamba_simple as modulo
    fonte=inspect.getfile(modulo)
    return {'python':platform.python_version(),'sistema':platform.platform(),'torch':torch.__version__,
            'cuda':torch.version.cuda,'gpu':torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            'memoria_total':torch.cuda.get_device_properties(0).total_memory if torch.cuda.is_available() else 0,
            'versoes':{n:importlib.metadata.version(n) for n in ['mamba-ssm','causal-conv1d','numpy','pandas','pyarrow','statsmodels']},
            'mamba_fonte_sha256':sha256(fonte),'nvidia_smi':subprocess.check_output(['nvidia-smi'],text=True),
            'pip_freeze':subprocess.check_output([__import__('sys').executable,'-m','pip','freeze'],text=True)}


def executar(c,destino,referencia):
    registro={'status':'em_andamento','inicio_utc':agora(),'ambiente':ambiente(),'casos':[],'agrupamento':[]}
    salvar_json(destino/'qualificacao.json',registro)
    try:
        anterior=ler_json(RAIZ/referencia['assinatura']['qualificacao']['caminho'])
        for k in ('python','torch','cuda','gpu','versoes'):
            if registro['ambiente'][k]!=anterior[k]: raise ValueError(f'Ambiente divergente: {k}')
        if not torch.cuda.is_available(): raise RuntimeError('CUDA obrigatório.')
        t=c['treino']
        for nome in ('lstm','mamba'):
            politicas=('original','corrigido') if nome=='mamba' else ('original',)
            for w in c['contextos']:
                for politica in politicas:
                    repeticoes=[]
                    with warnings.catch_warnings(record=True) as avisos:
                        warnings.simplefilter('always')
                        for repeticao in range(2):
                            fixar_seed(20261020)
                            rede=criar(nome,c).cuda()
                            x=torch.randn(64,w,1,device='cuda'); y=torch.randn(64,device='cuda')
                            o=criar_otimizador(rede,t) if politica=='corrigido' else torch.optim.AdamW(rede.parameters(),lr=t['taxa_aprendizado'],weight_decay=t['weight_decay'],betas=(.9,.999),eps=1e-8)
                            for passo in range(3):
                                rede.train(); o.zero_grad(set_to_none=True)
                                for i in (0,32):
                                    perda=torch.nn.functional.mse_loss(rede(x[i:i+32]),y[i:i+32],reduction='sum')/64
                                    perda.backward()
                                if any(not torch.isfinite(p.grad).all() for p in rede.parameters() if p.grad is not None): raise ValueError('Gradiente inválido.')
                                torch.nn.utils.clip_grad_norm_(rede.parameters(),t['clipping'],error_if_nonfinite=True)
                                o.step()
                            rede.eval()
                            with torch.inference_mode(): previsto=rede(x).cpu().numpy()
                            cp=destino/f'sintetico_{nome}_{w}_{politica}_{repeticao}.pt'
                            torch.save(rede.state_dict(),cp)
                            nova=criar(nome,c).cuda(); nova.load_state_dict(torch.load(cp,map_location='cuda',weights_only=True)); nova.eval()
                            with torch.inference_mode(): recarga=nova(x).cpu().numpy()
                            np.testing.assert_array_equal(previsto,recarga)
                            assert previsto.shape==(64,) and np.isfinite(previsto).all()
                            repeticoes.append(previsto)
                            del rede,nova,o,x,y
                        diferenca=float(np.max(np.abs(repeticoes[0]-repeticoes[1])))
                        if diferenca>1e-6: raise ValueError('Repetição sintética excede 1e-6.')
                    registro['casos'].append({'modelo':nome,'contexto':w,'politica':politica,'recarga_exata':True,'diferenca_repeticao':diferenca,'avisos':[str(a.message) for a in avisos]})
                    print(f'QUALIFICADO {nome} W{w} {politica}',flush=True)
                    salvar_json(destino/'qualificacao.json',registro)
                if nome=='mamba':
                    # Mesmos pesos e gradientes artificiais: isola efeito numérico de agrupar.
                    fixar_seed(20261020); a=criar(nome,c).cuda(); b=copy.deepcopy(a)
                    oa=torch.optim.AdamW(a.parameters(),lr=t['taxa_aprendizado'],weight_decay=t['weight_decay'],betas=(.9,.999),eps=1e-8)
                    grupos=[{'params':g['params'],'weight_decay':t['weight_decay']} for g in grupos_parametros(b,t['weight_decay'])]
                    ob=torch.optim.AdamW(grupos,lr=t['taxa_aprendizado'],weight_decay=t['weight_decay'],betas=(.9,.999),eps=1e-8)
                    for passo in range(5):
                        for pa,pb in zip(a.parameters(),b.parameters()): pa.grad=torch.randn_like(pa); pb.grad=pa.grad.clone()
                        oa.step(); ob.step()
                    for pa,pb in zip(a.parameters(),b.parameters()): torch.testing.assert_close(pa,pb,rtol=0,atol=0)
                    registro['agrupamento'].append({'contexto':w,'passos':5,'equivalencia_exata':True})
                    del a,b,oa,ob
        registro['grupos_corrigidos']=descrever_grupos(criar('mamba',c),t)
        registro.update(status='aprovado',fim_utc=agora())
    except Exception as erro:
        registro.update(status='falha',erro=repr(erro),fim_utc=agora())
        raise
    finally: salvar_json(destino/'qualificacao.json',registro)
    return registro
