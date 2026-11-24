import math


def fracao(previsao, politica, cfg):
    if not math.isfinite(previsao):
        raise ValueError('Previsao invalida.')
    if politica not in ('smart', 'smart_filtrada'):
        raise ValueError('Politica desconhecida.')
    f, s = cfg['filtro_taxa'], cfg['filtro_slippage']
    limiar = math.log((1+s)*(1+f)/((1-s)*(1-f)))
    if politica == 'smart_filtrada' and abs(previsao) <= limiar:
        return 0.0
    return max(-1.0, min(1.0, -math.expm1(-max(-1.,min(1.,previsao))) / cfg['escala_smart']))


def ordem_planejada(previsao, politica, patrimonio, preco, posicao, bilateral, cfg):
    """Quantidade definida no sinal; nenhum preço posterior é argumento."""
    if patrimonio <= 0 or preco <= 0:
        raise ValueError('Patrimonio/preco invalido.')
    d = fracao(previsao, politica, cfg)
    if d == 0:
        return 0.0
    if d < 0 and not bilateral:
        bruto = d * posicao
    else:
        sentido = 1 if d > 0 else -1
        capacidade = max(0., cfg['fracao_maxima']*patrimonio - sentido*posicao*preco)
        bruto = d * capacidade / preco
    quantidade = math.copysign(math.floor(abs(bruto)/cfg['passo_btc']+1e-10)*cfg['passo_btc'], bruto)
    if abs(quantidade)*preco < cfg['minimo_usdt']:
        return 0.0
    return quantidade
