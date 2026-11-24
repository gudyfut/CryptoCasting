"""Recomputação contábil sem chamar o executor ou reutilizar seu payoff."""
import math
import numpy as np


def conferir(resultado, mercado, inicio_ms, fim_ms):
    capital=10000.; ultimo=inicio_ms-1; maior_residuo=0.
    for t in resultado['operacoes']:
        q=t['quantidade']; lado=t['lado']; pe=t['preco_entrada']; ps=t['preco_saida']
        if lado not in (-1,1) or q<=0 or abs(q/.001-round(q/.001))>1e-7:
            raise ValueError('Quantidade/lado fora do contrato.')
        if t['entrada_ms']<t['origem_ms']+60000 or t['entrada_ms']<ultimo or t['saida_ms']>=fim_ms:
            raise ValueError('Latência, sobreposição ou período inválido.')
        if q*pe>min(.95*capital,50000.)+1e-7 or q*pe<100:
            raise ValueError('Nocional fora dos filtros.')
        if mercado.funding_evento[t['entrada']]:
            raise ValueError('Entrada indevida no settlement.')
        slip=t['deslizamento']
        def fill(preco,sinal):
            v=preco*(1+sinal*slip)/.1
            return (math.ceil(v-1e-10) if sinal>0 else math.floor(v+1e-10))*.1
        if abs(pe-fill(mercado.negociacao[t['entrada'],0],lado))>1e-8:
            raise ValueError('Preço de entrada não reconcilia com mercado/latência.')
        if t['motivo']=='tempo': bruto=mercado.negociacao[t['saida'],0]
        elif t['motivo']=='prudencial': bruto=mercado.negociacao[t['saida'],2 if lado==1 else 1]
        else:
            janela=mercado.negociacao[t['entrada']:t['saida']+1]
            hs=janela[:,2]<=t['stop'] if lado==1 else janela[:,1]>=t['stop']
            ht=janela[:,1]>=t['take'] if lado==1 else janela[:,2]<=t['take']
            pos=np.flatnonzero(hs|ht)
            if not len(pos) or pos[0]!=len(janela)-1:
                raise ValueError('Primeira barreira não corresponde ao encerramento.')
            motivo='stop' if hs[-1] else 'take'
            if t['motivo']!=motivo: raise ValueError('Ambiguidade favoreceu take.')
            bruto=t['stop'] if motivo=='stop' else t['take']
            if motivo=='stop' and t['saida']!=t['entrada']:
                bruto=min(bruto,janela[-1,0]) if lado==1 else max(bruto,janela[-1,0])
        if abs(ps-fill(bruto,-lado))>1e-8: raise ValueError('Preço de saída divergente.')
        inicio=t['entrada']; fim=t['saida']-(t['motivo']=='tempo')
        eventos=mercado.eventos[(mercado.eventos>=inicio)&(mercado.eventos<=fim)]
        if [int(i) for i in eventos] != [e['indice'] for e in t['eventos_funding']]:
            raise ValueError('Settlement omitido ou duplicado.')
        valores=[]
        for i,e in zip(eventos,t['eventos_funding']):
            taxa=float(mercado.funding_taxa[i]); paga=lado*taxa>0
            marca=float(mercado.funding_preco[i]) if mercado.funding_exato[i] else float(mercado.marca[i,1 if paga else 2])
            v=-lado*taxa*marca
            if i==t['saida'] and t['motivo']!='tempo' and v>0: v=0.
            if abs(v-e['por_btc'])>1e-9: raise ValueError('Funding divergente.')
            valores.append(v)
        liquido=q*(lado*(ps-pe)-.0005*(pe+ps)+math.fsum(valores))
        residuos=[abs(t['caixa_antes']-capital),abs(t['pnl_liquido']-liquido)]
        capital+=liquido; residuos.append(abs(t['caixa_depois']-capital))
        maior_residuo=max(maior_residuo,*residuos); ultimo=t['saida_ms']
    curva=np.asarray(resultado['patrimonio']); tempo=np.asarray(resultado['segundos_utc'])
    if np.any(np.diff(tempo)<0) or tempo[0]!=inicio_ms/1000 or tempo[-1]!=fim_ms/1000:
        raise ValueError('Curva fora da cronologia.')
    maior_residuo=max(maior_residuo,abs(curva[-1]-capital))
    dd=float(np.max(1-curva/np.maximum.accumulate(curva)))
    if abs(dd-resultado['metricas']['drawdown_maximo'])>1e-12 or maior_residuo>1e-7:
        raise ValueError('Patrimônio/drawdown não reconciliados.')
    return {'conferido':True,'operacoes':len(resultado['operacoes']),
            'capital_recalculado':capital,'residuo_maximo_usdt':maior_residuo,
            'limite':'Auditoria contábil; não certifica preços intraminuto, liquidação ou tarifas históricas.'}
