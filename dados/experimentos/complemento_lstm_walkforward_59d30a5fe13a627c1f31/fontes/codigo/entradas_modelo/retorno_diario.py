"""Mesmas janelas; apenas alvo preço -> retorno simples, em unidade decimal."""
import numpy as np
from entradas_modelo.cryptomamba_diario import preparar as preparar_precos


def preco_equivalente(retorno, ultimo):
    r,u=np.asarray(retorno,dtype=np.float64),np.asarray(ultimo,dtype=np.float64)
    if r.shape!=u.shape or not np.isfinite(r).all() or (u<=0).any():
        raise ValueError('Retorno/preço incompatíveis; não permitir broadcasting.')
    return u*(1+r)


def preparar(diario,c):
    if c['alvo']!='retorno_simples_fechamento_seguinte_decimal':raise ValueError('Alvo incorreto.')
    d=preparar_precos(diario,c)
    for z in d.values():
        z['preco_alvo']=z['y'].copy()
        z['y']=z['preco_alvo']/z['ultimo_close']-1
        assert np.isfinite(z['y']).all() and (z['y']>-1).all()
        np.testing.assert_allclose(preco_equivalente(z['y'],z['ultimo_close']),z['preco_alvo'],rtol=1e-14)
    return d


def publicar_previsoes(z,retorno):
    """Contrato da publicação: preço interoperável e retorno nativo separados."""
    return {'previsoes':preco_equivalente(retorno,z['ultimo_close']),
            'previsoes_retorno':np.asarray(retorno,dtype=np.float64),'y':z['preco_alvo'],
            'alvo_retorno':z['y'],**{k:v for k,v in z.items() if k not in ('x','y','preco_alvo')}}
