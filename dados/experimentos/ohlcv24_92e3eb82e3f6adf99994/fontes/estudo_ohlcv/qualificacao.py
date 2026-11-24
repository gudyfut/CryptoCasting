"""Teste CUDA e treino completo em dados SINTÉTICOS, sem resultado de mercado."""
import contextlib
import copy
import io
from pathlib import Path
import subprocess
import sys
import traceback
import warnings
import numpy as np
import pandas as pd
from previsao24.arquivos import RAIZ, agora, salvar_json, sha256
from .ciclo import configuracao, fontes, ambiente, REGISTROS, conferir_reproducao


def qualificar():
    import torch
    from .treino import fixar_seed, treinar
    from .redes import criar
    from experimento_penalizacao.otimizador import criar_otimizador, descrever_grupos
    pasta = REGISTROS / 'qualificacoes' / agora().replace(':','').replace('+','_')
    pasta.mkdir(parents=True)
    recibo = {'utc': agora(), 'fontes': fontes(), 'natureza': 'sintetico_sem_treinamento_de_mercado'}
    try:
        recibo['ambiente'] = ambiente()
        for nome in ('tests_ohlcv','tests'):
            r = subprocess.run([sys.executable,'-m','unittest','discover','-s',nome,'-v'], cwd=RAIZ,
                               capture_output=True, text=True)
            (pasta / f'{nome}.log').write_text(r.stdout+r.stderr,encoding='utf-8')
            if r.returncode:
                raise RuntimeError(f'Contratos falharam: {nome}; consultar log.')
        c = configuracao()
        c['treino'] = dict(c['treino'], epocas=2, paciencia=2)
        rng = np.random.default_rng(20261028)
        matriz = rng.normal(size=(420,5)).astype(np.float32)
        h = pd.DataFrame({'indice_hora': np.arange(420), 'origem_utc': pd.date_range('2000-01-01',periods=420,freq='h',tz='UTC'),
                          'close':100.,'preco_destino':101.,'alvo':rng.normal(size=420)*.01})
        h['destino_utc']=h['origem_utc']+pd.Timedelta(hours=24)
        blocos={'treino':h.iloc[168:232], 'validacao':h.iloc[256:288], 'teste':h.iloc[312:344], 'operacional':h.iloc[312:345]}
        escalas={'media_alvo':0.,'escala_alvo':.01}
        recibo['redes']={}
        with warnings.catch_warnings(record=True) as avisos:
            warnings.simplefilter('always')
            for nome in ('mamba','lstm'):
                fixar_seed(42)
                rede=criar(nome,c).cuda()
                x=torch.randn(32,168,5,device='cuda',requires_grad=True)
                antes={n:p.detach().clone() for n,p in rede.named_parameters()}
                y=rede(x)
                if y.shape!=(32,) or not torch.isfinite(y).all():
                    raise ValueError('Dimensão/forward inválido.')
                y.square().mean().backward()
                gradientes=x.grad.abs().sum((0,1)).detach().cpu().tolist()
                if not all(v>0 and np.isfinite(v) for v in gradientes):
                    raise ValueError('Nem todos os canais influenciam a saída.')
                otimizador=criar_otimizador(rede,c['treino'])
                otimizador.step()
                if not any(not torch.equal(antes[n],p) for n,p in rede.named_parameters()):
                    raise ValueError('Pesos não atualizados.')
                grupos=descrever_grupos(rede,c['treino'])
                for g in grupos:
                    for n in g['nomes']:
                        if n.endswith(('A_log','.D')) and g['weight_decay']!=0:
                            raise ValueError('Parâmetro marcado recebeu penalização.')
                recibo['redes'][nome]={'parametros':sum(p.numel() for p in rede.parameters()),'gradiente_por_canal':gradientes,'grupos':grupos}
                del rede,otimizador,x,y,antes
                torch.cuda.empty_cache()
                for repeticao in (1,2):
                    destino=pasta/f'{nome}_{repeticao}'
                    with (pasta/f'{nome}_{repeticao}.log').open('w',encoding='utf-8',buffering=1) as log:
                        with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                            treinar(c,{'modelo':nome,'contexto':168,'seed':42},matriz,blocos,escalas,destino)
                recibo['redes'][nome]['reproducao']=conferir_reproducao(pasta/f'{nome}_1',pasta/f'{nome}_2',c)
                recibo['redes'][nome]['recarga_exata']=True
            recibo['avisos']=sorted(set(str(a.message) for a in avisos))
        recibo['status']='aprovado'
    except BaseException:
        recibo.update(status='falha',erro=traceback.format_exc())
        salvar_json(pasta/'qualificacao.json',recibo)
        raise
    recibo['artefatos']={p.relative_to(pasta).as_posix():sha256(p) for p in sorted(pasta.rglob('*')) if p.is_file()}
    salvar_json(pasta/'qualificacao.json',recibo)
    salvar_json(REGISTROS/'qualificacao.json',{'recibo':(pasta/'qualificacao.json').relative_to(RAIZ).as_posix(),'sha256':sha256(pasta/'qualificacao.json')})
    return pasta
