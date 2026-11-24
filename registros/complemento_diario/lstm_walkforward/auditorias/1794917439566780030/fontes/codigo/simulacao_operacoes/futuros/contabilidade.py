import math

class LimiteMargem(RuntimeError):
    """Trajetoria excedeu envelope de pesquisa; nao inventar execucao de liquidacao."""

def quantidade(capital_sinal,preco_conhecido,lado,cfg):
    if capital_sinal<=0 or preco_conhecido<=0:raise ValueError('Capital/preco invalido.')
    nocional=min(capital_sinal*cfg['fracao_capital'],cfg['nocional_maximo'])
    q=math.floor(nocional/preco_conhecido/cfg['passo_btc'])*cfg['passo_btc']
    if q*preco_conhecido<cfg['minimo_usdt']:q=0.
    return lado*q

def preenchimento(meio,quantidade_assinada,slip):
    return meio*(1+slip if quantidade_assinada>0 else 1-slip)

def pnl(q,entrada,saida):return q*(saida-entrada)

def funding(q,preco,taxa):return -q*preco*taxa
