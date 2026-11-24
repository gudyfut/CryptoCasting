"""Receitas novas sem editar o consumidor, a coleta ou as receitas congeladas."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, ler_json, salvar_json, sha256, identidade
from entradas_modelo.conjunto import ConjuntoEntradas
from entradas_modelo.amostras import ajustar_escalas, aplicar_escalas
from modelos.consumo import ConsumoModelos
from experimentos.huber_blocos.dados import Verificador, carregar_blocos

REG = RAIZ / 'registros/entradas_niveis'
CONFIG = 'configuracoes/entradas_niveis_001.json'
CANAIS = ['abertura_usdt', 'maxima_usdt', 'minima_usdt', 'fechamento_usdt', 'volume_btc']
VARIANTES = ['crua', 'niveis_padronizados']


class ConsumoNiveis(ConsumoModelos):
    """Adiciona apenas o contrato de identidade de entrada; validações base preservadas.

    O consumidor congelado aceita somente zscore. A validação estrutural é feita
    numa cópia com esse identificador, e o contrato real é restaurado antes de
    definir a identidade científica ou entregar qualquer janela. Não normaliza x.
    """
    def __init__(self, conjunto, identidade_dados):
        original = deepcopy(conjunto.contrato)
        if original['receita'] == 'ohlcv_cru_v1':
            assert original['normalizacao'] == 'identidade_entrada_alvo_zscore_treino'
            assert conjunto.escalas['media_entrada'] == [0.] * 5
            assert conjunto.escalas['escala_entrada'] == [1.] * 5
            copia = deepcopy(conjunto)
            copia.contrato['normalizacao'] = 'zscore_treino'
            super().__init__(copia, identidade_dados)
            self._conjunto.contrato = original
            self.especificacao = replace(self.especificacao, identidade=identidade({
                'dados': identidade_dados, 'contrato': original, 'escalas': conjunto.escalas}))
        else:
            assert original['receita'] == 'ohlcv_niveis_padronizados_v1'
            super().__init__(conjunto, identidade_dados)


def representar(candles, referencia, variante):
    if variante not in VARIANTES:
        raise ValueError('Representação não autorizada.')
    raw = candles[['open', 'high', 'low', 'close', 'volume']].to_numpy(np.float64).copy()
    assert len(raw) == len(referencia.matriz)
    # Preserva exatamente disponibilidade/população de A, inclusive primeira hora.
    raw[~np.isfinite(referencia.matriz).all(axis=1)] = np.nan
    escalas = ajustar_escalas(raw, referencia.partes['treino'], 168, CANAIS)
    for k in ('media_alvo', 'escala_alvo'):
        # Redução NumPy pode diferir em ulps após Parquet/layout de memória.
        # Conferir a estatística refeita e herdar os bytes lógicos do escalar A.
        assert np.isclose(escalas[k], referencia.escalas[k], rtol=1e-13, atol=1e-15)
        escalas[k] = referencia.escalas[k]
    if variante == 'crua':
        escalas['media_entrada'] = [0.] * 5
        escalas['escala_entrada'] = [1.] * 5
        escalas['regra'] = 'Entrada identidade: OHLC em USDT e V em BTC; alvo zscore de treino preservado.'
        matriz = raw.astype(np.float32)
    else:
        matriz = aplicar_escalas(raw, escalas)
    contrato = deepcopy(referencia.contrato)
    contrato.update(canais=CANAIS, receita='ohlcv_cru_v1' if variante == 'crua' else 'ohlcv_niveis_padronizados_v1',
        normalizacao='identidade_entrada_alvo_zscore_treino' if variante == 'crua' else 'zscore_treino',
        unidade_canais=['USDT', 'USDT', 'USDT', 'USDT', 'BTC'], variante=variante,
        disponibilidade='Mesmas horas e origens da referência relativa; sem interpolação ou seleção futura.')
    return ConjuntoEntradas(matriz, referencia.origens.copy(), deepcopy(referencia.partes), escalas, contrato)


def preparar():
    REG.mkdir(parents=True, exist_ok=True)
    if (REG/'entradas.json').exists():
        carregar(ler_json(REG/'entradas.json'))
        return ler_json(REG/'entradas.json')
    c = ler_json(RAIZ/CONFIG)
    mapa_a = ler_json(RAIZ/'registros/huber_blocos/entradas.json')
    v = Verificador(); anteriores = carregar_blocos(mapa_a, v)
    cp = RAIZ/c['candles_pasta']; v.artefato(cp)
    candles = pd.read_parquet(cp/'BTCUSDT.parquet')
    saida = {}
    fontes = {f'experimentos/entradas_niveis/{n}': sha256(Path(__file__).parent/n) for n in ('dados.py', '__init__.py')}
    for b, consumo in anteriores.items():
        saida[b] = {'atual': mapa_a[b]}
        for variante in VARIANTES:
            q = representar(candles, consumo._conjunto, variante)
            sig = {'receita': variante, 'bloco': b, 'referencia': mapa_a[b], 'fontes': fontes,
                'candles_manifesto': sha256(cp/'manifesto.json'), 'configuracao': c}
            codigo = identidade(sig)[:20]
            p = RAIZ/f'dados/entradas/niveis_{codigo}'
            if p.exists():
                raise FileExistsError('Artefato já existente sem mapa; investigar em vez de sobrescrever.')
            p.mkdir(parents=True)
            np.save(p/'entradas.npy', q.matriz, allow_pickle=False)
            q.origens.to_parquet(p/'origens.parquet', index=False)
            for parte, df in q.partes.items():
                df.to_parquet(p/f'{parte}.parquet', index=False)
            salvar_json(p/'escalas.json', q.escalas); salvar_json(p/'contrato.json', q.contrato)
            arquivos = {f.name: sha256(f) for f in p.iterdir() if f.is_file()}
            salvar_json(p/'manifesto.json', {'id': codigo, 'tipo': 'entradas_niveis', 'assinatura': sig, 'arquivos': arquivos})
            saida[b][variante] = {'pasta': p.relative_to(RAIZ).as_posix(), 'manifesto_sha256': sha256(p/'manifesto.json')}
            print('Preparado', b, variante, codigo, flush=True)
    salvar_json(REG/'entradas.json', saida)
    carregar(saida)
    return saida


def carregar(mapa):
    v = Verificador()
    bases = carregar_blocos({b: m['atual'] for b, m in mapa.items()}, v)
    cp = RAIZ/ler_json(RAIZ/CONFIG)['candles_pasta']
    esperado = ler_json(cp/'manifesto.json')['arquivos']['BTCUSDT.parquet']
    assert sha256(cp/'BTCUSDT.parquet') == esperado
    candles = pd.read_parquet(cp/'BTCUSDT.parquet')
    saida = {}
    for b, itens in mapa.items():
        saida[b] = {'atual': bases[b]}
        for variante in VARIANTES:
            d = itens[variante]; p = RAIZ/d['pasta']
            v.arquivos_em(p, {'manifesto.json': d['manifesto_sha256']})
            m = ler_json(p/'manifesto.json')
            assert m['id'] == identidade(m['assinatura'])[:20]
            v.arquivos_em(p, m['arquivos']); v.arquivos_em(RAIZ, m['assinatura']['fontes'])
            q = ConjuntoEntradas(np.load(p/'entradas.npy', allow_pickle=False), pd.read_parquet(p/'origens.parquet'),
                {n: pd.read_parquet(p/f'{n}.parquet') for n in ('treino', 'validacao', 'teste', 'operacional')},
                ler_json(p/'escalas.json'), ler_json(p/'contrato.json'))
            x = ConsumoNiveis(q, d['manifesto_sha256'])
            # Reconstrução independente das entradas reais, sem usar a receita.
            bruto = candles[['open','high','low','close','volume']].to_numpy(float).copy()
            bruto[~np.isfinite(bases[b]._conjunto.matriz).all(axis=1)] = np.nan
            if variante == 'crua':
                np.testing.assert_array_equal(q.matriz, bruto.astype(np.float32))
            else:
                ix=q.partes['treino'].indice_candle.to_numpy(int)
                diferencas=np.zeros(len(bruto)+1,int)
                np.add.at(diferencas,ix-167,1);np.add.at(diferencas,ix+1,-1)
                usados=np.cumsum(diferencas[:-1])>0
                mu=bruto[usados].mean(axis=0);sd=bruto[usados].std(axis=0)
                sd=np.where(sd==0,1.,sd)
                np.testing.assert_allclose(mu,q.escalas['media_entrada'],rtol=1e-13,atol=1e-13)
                np.testing.assert_allclose(sd,q.escalas['escala_entrada'],rtol=1e-13,atol=1e-13)
                np.testing.assert_allclose(q.matriz,((bruto-mu)/sd).astype(np.float32),rtol=1e-6,atol=1e-7,equal_nan=True)
            for parte in q.partes:
                pd.testing.assert_frame_equal(q.partes[parte], bases[b]._conjunto.partes[parte], check_exact=True)
            for k in ('media_alvo', 'escala_alvo'):
                assert q.escalas[k] == bases[b]._conjunto.escalas[k]
            saida[b][variante] = x
    return saida
