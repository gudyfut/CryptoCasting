"""Prepara uma receita de entradas identificada a partir de um artefato de candles."""
from pathlib import Path
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, abrir_artefato, destino_artefato, fontes, relativo, salvar_json, sha256, tentativa, ler_json
from mercado_binance import carregar_candles
from mercado_binance.contratos import conferir_candles
from .receitas import calcular_entradas
from .alvos import retorno_terminal
from .amostras import separar, ajustar_escalas, aplicar_escalas
from .conjunto import ConjuntoEntradas


def construir(candles,config,intervalo):
    conferir_candles(candles,intervalo)
    esperadas={'versao','par','receita','canais','alvo','horizonte_minutos','contexto_passos','passo_origens','divisao','normalizacao'}
    if set(config)!=esperadas or config['versao']!=1 or config['alvo']!='log_retorno_terminal' or config['normalizacao']!='zscore_treino':
        raise ValueError('Configuração de entradas contém campo desconhecido ou método não implementado.')
    x=calcular_entradas(candles,config['receita'],config['canais'])
    origens=retorno_terminal(candles,config['horizonte_minutos'],intervalo)
    partes=separar(origens,x,config['contexto_passos'],config['divisao'],config['passo_origens'])
    escalas=ajustar_escalas(x,partes['treino'],config['contexto_passos'],config['canais'])
    matriz=aplicar_escalas(x,escalas)
    contrato=dict(config,intervalo_minutos=intervalo,dimensao_entrada=len(config['canais']),
                  unidade_alvo='log-retorno, não porcentagem',dtype='float32',ordem_janela='passado até origem inclusive')
    return ConjuntoEntradas(matriz,origens,partes,escalas,contrato)


def preparar_entradas(candles,config,base=None):
    candles=Path(candles).resolve()
    q,m=carregar_candles(candles,config['par'])
    intervalo=m['assinatura']['parametros']['intervalo_minutos']
    assinatura={'contrato':'entradas-1','configuracao':config,
                'candles':relativo(candles),'manifesto_candles_sha256':sha256(candles/'manifesto.json'),
                'dependencias':[{'pasta':relativo(candles),'manifesto_sha256':sha256(candles/'manifesto.json')}],
                'fontes':fontes('infraestrutura','mercado_binance','entradas_modelo')}
    base=Path(base or RAIZ/'dados/entradas')
    with tentativa(base,'entradas_modelo',assinatura) as (pasta,existe):
        if not existe:
            conjunto=construir(q,config,intervalo)
            np.save(pasta/'entradas.npy',conjunto.matriz,allow_pickle=False)
            conjunto.origens.to_parquet(pasta/'origens.parquet',index=False)
            for nome,parte in conjunto.partes.items():
                parte.to_parquet(pasta/f'{nome}.parquet',index=False)
            salvar_json(pasta/'escalas.json',conjunto.escalas)
            salvar_json(pasta/'contrato.json',conjunto.contrato)
            salvar_json(pasta/'populacoes.json',{k:{'n':len(v),'primeira_origem':v.origem_utc.min().isoformat(),
                        'ultima_origem':v.origem_utc.max().isoformat(),'ultimo_destino':v.destino_utc.max().isoformat()}
                        for k,v in conjunto.partes.items()})
    return destino_artefato(base,assinatura)


def carregar_conjunto(pasta):
    pasta=Path(pasta).resolve();abrir_artefato(pasta,'entradas_modelo')
    contrato=ler_json(pasta/'contrato.json');matriz=np.load(pasta/'entradas.npy',allow_pickle=False)
    origens=pd.read_parquet(pasta/'origens.parquet')
    if matriz.shape!=(len(origens),contrato['dimensao_entrada']) or matriz.dtype!=np.float32:
        raise ValueError('Matriz não cumpre contrato de entrada.')
    partes={k:pd.read_parquet(pasta/f'{k}.parquet') for k in ('treino','validacao','teste','operacional')}
    return ConjuntoEntradas(matriz,origens,partes,ler_json(pasta/'escalas.json'),contrato)
