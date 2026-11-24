import math

def direcao(previsao,politica,modo,cfg):
    if not math.isfinite(previsao):raise ValueError('Previsao nao finita.')
    if politica not in ['sinal24','filtrada24'] or modo not in ['comprada','bilateral']:raise ValueError('Politica/modo invalido.')
    limite=0.
    if politica=='filtrada24':
        c=cfg['custos']['base'];f,s=c['taxa'],c['slippage']
        limite=math.log((1+s)*(1+f)/((1-s)*(1-f)))
    lado=1 if previsao>limite else -1 if previsao < -limite else 0
    return 0 if modo=='comprada' and lado<0 else lado
