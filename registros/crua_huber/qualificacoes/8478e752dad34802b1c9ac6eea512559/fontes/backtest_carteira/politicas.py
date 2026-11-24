"""Decisões causais: recebe retorno previsto, sem preços ou alvos futuros."""
import math


def decisao(nome, retorno, cfg):
    if not math.isfinite(retorno):raise ValueError('Previsão não finita.')
    if nome=='smart':
        risco=cfg['risco_smart']
        if retorno>=-math.log1p(-risco):return 'comprar',1.
        if retorno<=-math.log1p(risco):return 'vender',1.
        d=-math.expm1(-retorno)/risco
        return ('comprar',d) if d>0 else ('vender',-d) if d<0 else ('manter',0.)
    if nome=='vanilla':
        tr=cfg['limiar_vanilla']
        if math.log1p(-tr)<retorno<math.log1p(tr):return 'manter',0.
        return ('comprar',1.) if retorno>0 else ('vender',1.)
    if nome=='diaria24':
        f,s=cfg['custos']['base']['taxa'],cfg['custos']['base']['slippage']
        lim=math.log((1+s)*(1+f)/((1-s)*(1-f)))
        return ('comprar',1.) if retorno>lim else ('manter',0.)
    if nome=='comprar_manter':return 'comprar',1.
    if nome=='caixa':return 'manter',0.
    raise ValueError('Política desconhecida.')
