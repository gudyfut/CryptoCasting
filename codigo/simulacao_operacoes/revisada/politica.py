"""Só previsão, patrimônio e preço anteriores à ordem são recebidos aqui."""
import math
from .regras import quantizar, filtros


def ordem_planejada(previsao, politica, patrimonio, preco, posicao, bilateral, cfg, futuro=False):
    if not all(math.isfinite(x) for x in [previsao,patrimonio,preco,posicao]) or patrimonio<=0 or preco<=0:
        raise ValueError('Estado/sinal invalido.')
    if politica not in cfg['politicas']:
        raise ValueError('Politica desconhecida.')
    d = max(-1.,min(1.,-math.expm1(-max(-1.,min(1.,previsao)))/cfg['escala_smart']))
    if d == 0:
        return 0.
    sentido = math.copysign(1., d)
    capacidade = cfg['fracao_maxima']*patrimonio
    if politica == 'smart':
        bruto = d*posicao if d<0 and not bilateral else d*max(0.,capacidade-sentido*posicao*preco)/preco
    else:
        pode_abrir = bilateral or d>0
        if politica == 'direcional_filtrada':
            pode_abrir = pode_abrir and abs(previsao)>cfg['limiar_entrada']
        if posicao*d < 0:
            # Ambas as versões encerram a posição contrária; só a bilateral pode abrir short.
            bruto = -posicao + (d*capacidade/preco if pode_abrir else 0.)
        elif pode_abrir:
            bruto = d*max(0.,capacidade-abs(posicao)*preco)/preco
        else:
            bruto = 0.
    return quantizar(bruto,filtros(cfg,futuro)['passo'])
