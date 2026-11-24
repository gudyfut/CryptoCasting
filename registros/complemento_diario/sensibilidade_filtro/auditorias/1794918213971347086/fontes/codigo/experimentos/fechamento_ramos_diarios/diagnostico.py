"""Decomposição e intervenção posteriores, sem treinar ou escolher políticas."""
import numpy as np
import torch
from mamba_ssm import Mamba
from infraestrutura.artefatos import RAIZ, ler_json, salvar_json
from .contratos import receita
from .treinamento import carregar_rede, inferir, coeficientes_afins


def estatisticas(v):
    a = np.asarray(v, dtype=np.float64)
    return dict(media=float(a.mean()), desvio=float(a.std()),
                minimo=float(a.min()), maximo=float(a.max()), rms=float(np.sqrt(np.mean(a*a))))


def diagnosticar(p, c, dados):
    caminhos = ler_json(p/'modelos.json'); resultado = {}; trajetorias = {}
    destino = p/'publicacao/diagnostico'; destino.mkdir(exist_ok=False)
    for variante in c['variantes']:
        for seed in c['seeds']:
            chave = f'{variante}_{seed}'; pasta = RAIZ/caminhos[chave]['pasta']
            rede = carregar_rede(pasta, receita(c, variante))
            pesos = {k:v.clone() for k,v in rede.state_dict().items()}
            coef, intercepto = coeficientes_afins(rede)
            entrada = dict(parametros=sum(v.numel() for v in rede.parameters()),
                           coeficientes_canal_dia=coef.tolist(), intercepto=intercepto, fases={})
            for fase,z in dados.items():
                completo = inferir(rede,z['x'])
                hooks = [m.register_forward_hook(lambda m,a,o:torch.zeros_like(o))
                         for m in rede.modules() if isinstance(m,Mamba)]
                try: residual = inferir(rede,z['x'])
                finally:
                    for h in hooks:h.remove()
                por_canal = np.einsum('nct,ct->nc', z['x'].astype(np.float64), coef)
                afim = por_canal.sum(axis=1)+intercepto
                np.testing.assert_allclose(residual,afim,atol=2e-6,rtol=1e-5)
                delta = completo-residual
                entrada['fases'][fase] = dict(exemplos=len(completo),
                    max_diferenca_sem_ramos=float(abs(delta).max()),
                    rms_diferenca_sem_ramos=float(np.sqrt(np.mean(delta**2))),
                    max_residuo_afim_float64=float(abs(residual-afim).max()),
                    mse_completo=float(np.mean((completo-z['y'])**2)),
                    mse_sem_ramos=float(np.mean((residual-z['y'])**2)),
                    previsao=estatisticas(completo),
                    contribuicoes={canal:estatisticas(por_canal[:,i]) for i,canal in enumerate(c['canais'])},
                    contribuicao_ohlc_conjunta=estatisticas(por_canal[:,1:5].sum(axis=1)))
                np.savez_compressed(destino/f'{fase}_{chave}.npz', origens_ms=z['origens_ms'],
                    previsao=completo, previsao_sem_ramos=residual, afim=afim,
                    contribuicoes_canais=por_canal, alvo=z['y'])
            assert all(torch.equal(v,rede.state_dict()[k]) for k,v in pesos.items())
            resultado[chave] = entrada
            trajetorias[chave] = {a.name:ler_json(a) for a in sorted((pasta/'observacoes').glob('*.json'))}
            del rede;torch.cuda.empty_cache()
    salvar_json(p/'publicacao/diagnostico_afim.json', dict(modelos=resultado, atualizacoes_de_pesos=0,
        limites='Intervenção nos checkpoints/populações examinados; não prova inutilidade geral. Em L/L0 ausência estrutural. Contribuições correlacionadas não são causalidade; coeficientes dependem da escala.'))
    salvar_json(p/'publicacao/trajetorias_observadas.json', dict(modelos=trajetorias,
        limites='Somente sondas existentes; épocas ausentes não são interpoladas. Gradientes de lotes fixados não representam todo o Adam.'))
