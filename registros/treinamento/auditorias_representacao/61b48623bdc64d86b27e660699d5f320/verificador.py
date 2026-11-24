"""Conferência posterior: representação OHLCV e custos, sem ajustar redes."""
from pathlib import Path
import argparse
import math
import shutil
import urllib.request
import json
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256, conferir_arquivos


def capital_recebido(operacoes, taxa, slippage, forma='recebido'):
    capital = 10000.
    for o in operacoes:
        if o['status'] != 'pontas_observadas':
            raise ValueError('Não imputar operações indisponíveis.')
        fator_preco = o['preco_saida'] * (1-slippage) / (o['preco_entrada'] * (1+slippage))
        fator_taxa = (1-taxa)**2 if forma == 'recebido' else (1-taxa)/(1+taxa)
        capital *= fator_preco * fator_taxa
    return capital


def auditar(destino):
    destino = Path(destino)
    conjunto = RAIZ/'dados/entradas/0420879c2afc454c7754'
    horas = RAIZ/'dados/mercado/candles/93509a1b06b19103ac1c/BTCUSDT.parquet'
    publicacao = RAIZ/'dados/experimentos/ohlcv_modular_ab5baf3eab3a2e66d8b2/publicacoes/tentativa_001'
    conferir_arquivos(conjunto, ler_json(conjunto/'manifesto.json')['arquivos'])
    q = pd.read_parquet(horas)
    escalas = ler_json(conjunto/'escalas.json')
    # Fórmulas independentes do produtor, calculadas em float64.
    anterior = q.close.shift(1).to_numpy(float)
    bruto = np.column_stack([np.log(q[k].to_numpy(float)/anterior) for k in ('open','high','low','close')]
                            + [np.log1p(q.volume.to_numpy(float))])
    matriz = np.load(conjunto/'entradas.npy', allow_pickle=False)
    z64 = (bruto - escalas['media_entrada']) / escalas['escala_entrada']
    if not np.array_equal(matriz, z64.astype(np.float32), equal_nan=True):
        raise ValueError('Matriz diverge das fórmulas documentadas.')
    invertido = matriz.astype(float)*escalas['escala_entrada'] + escalas['media_entrada']
    ok = np.isfinite(bruto).all(axis=1)
    geometria = [float(np.max(np.abs(np.exp(bruto[ok,j]-bruto[ok,0])-q[k].to_numpy()[ok]/q.open.to_numpy()[ok])))
                 for j,k in ((1,'high'),(2,'low'),(3,'close'))]
    partes = {}
    for parte in ('treino','validacao','teste'):
        exemplos = pd.read_parquet(conjunto/f'{parte}.parquet')
        usados = np.zeros(len(q), bool)
        for i in exemplos.indice_candle:
            usados[i-167:i+1] = True
        v = matriz[usados]
        partes[parte] = {'candles_unicos':int(usados.sum()), 'canais':{}}
        for j,nome in enumerate(escalas['canais']):
            w=v[:,j]
            partes[parte]['canais'][nome]={'media_z':float(w.mean()),'std_z':float(w.std()),
                'min_z':float(w.min()),'max_z':float(w.max()),'fora_5_desvios_pct':float(100*(np.abs(w)>5).mean())}
        if parte == 'treino':
            np.testing.assert_array_equal(bruto[usados].mean(axis=0), escalas['media_entrada'])
            np.testing.assert_array_equal(bruto[usados].std(axis=0), escalas['escala_entrada'])
        indices=exemplos.indice_candle.to_numpy()
        y=np.log(q.close.to_numpy()[indices+24]/q.close.to_numpy()[indices])
        np.testing.assert_allclose(y,exemplos.alvo.to_numpy(),rtol=0,atol=1e-15)
        fronteira=pd.Timestamp(ler_json(conjunto/'contrato.json')['divisao'][parte][1])
        assert (exemplos.destino_utc<fronteira).all()
    r=ler_json(publicacao/'resultados.json')
    custos={}
    for chave,resultado in r['por_ajuste'].items():
        ops=ler_json(publicacao/chave/'operacoes_base.json')
        anterior=capital_recebido(ops,.001,.0005,'anterior')
        if not math.isclose(anterior,resultado['spot']['base']['capital_final'],rel_tol=1e-12):
            raise ValueError('Contabilidade original não reproduzida.')
        perfis={'contabilizacao_recebido_mesmos_custos':(.001,.0005),
                'taxa010_slippage0':(.001,0.),'taxa0075_slippage0':(.00075,0.),
                'taxa0075_slippage001':(.00075,.0001)}
        custos[chave]={'operacoes':len(ops),'capital_original':anterior,'retorno_original':anterior/10000-1,
                      'cenarios':{}}
        for nome,(f,s) in perfis.items():
            capital=capital_recebido(ops,f,s)
            custos[chave]['cenarios'][nome]={'taxa_por_lado':f,'slippage_por_lado':s,
                        'capital_final':capital,'retorno':capital/10000-1}
    # Identidade analítica: correção do recebimento = fator (1-f²) por compra.
    for chave,v in custos.items():
        esperado=v['capital_original']*(1-.001**2)**v['operacoes']
        assert math.isclose(esperado,v['cenarios']['contabilizacao_recebido_mesmos_custos']['capital_final'],rel_tol=1e-12)
    # Testes de caixa simples independentes de séries reais.
    o=[{'status':'pontas_observadas','preco_entrada':100.,'preco_saida':100.}]
    assert math.isclose(capital_recebido(o,.001,0),10000*.999**2)
    assert capital_recebido([],0,0)==10000
    # Reconciliação amostral com candle horário nativo da mesma fonte.
    nativos=[]
    for data in ('2021-01-10','2023-06-10','2024-06-10','2025-06-10'):
        t=pd.Timestamp(data,tz='UTC');inicio=int(t.timestamp()*1000)
        url=f'https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1h&startTime={inicio}&limit=2'
        try:
            with urllib.request.urlopen(url,timeout=25) as resposta:
                corpo=resposta.read()
            arquivo=destino/f'klines_{data}.json';arquivo.write_bytes(corpo)
            linhas=json.loads(corpo)
            assert len(linhas)==2
            for linha in linhas:
                observado=q.loc[q.inicio_utc==pd.to_datetime(linha[0],unit='ms',utc=True)].iloc[0]
                np.testing.assert_allclose(observado[['open','high','low','close','volume']].to_numpy(float),
                                           np.asarray(linha[1:6],float),rtol=1e-12,atol=1e-8)
            nativos.append({'data':data,'url':url,'status':'coincide','candles':2,'resposta_sha256':sha256(arquivo)})
        except Exception as erro:
            nativos.append({'data':data,'url':url,'status':'falhou','erro':repr(erro)})
    relatorio={'utc':agora(),'status':'conferido','treinamento':False,
        'matriz_float32_identica':True,'scalers_treino_refeitos_exatamente':True,'alvos_24h_conferidos':True,
        'erro_maximo_inversao_float32':float(np.nanmax(np.abs(invertido-bruto))),
        'geometria_relativa_erro_maximo':max(geometria),'partes':partes,'api_horaria_amostral':nativos,
        'custos_sensibilidade_sinais_fixos':custos,
        'formula_anterior_compra':'B/[P*(1+s)*(1+f)]',
        'formula_recebido_compra':'B/[P*(1+s)]*(1-f)',
        'limites':['Sensibilidades mantêm exatamente as entradas da regra original; não selecionam limiar, horário ou modelo.',
                  'Taxa0.075% é cenário equivalente de custo, não carteira BNB modelada.',
                  'Não modela livro, fills parciais, arredondamento de lotes nem filtros históricos.',
                  'Taxas públicas e filtros atuais não comprovam taxas particulares/históricas2025.',
                  'Coincidência amostral com oito candles nativos não é reconciliação de todas as horas.',
                  'Mudança de distribuição e extremos não demonstram causalmente prejuízo ao modelo.']}
    shutil.copy2(Path(__file__),destino/'verificador.py')
    salvar_json(destino/'auditoria.json',relatorio)
    salvar_json(destino/'manifesto_auditoria.json',{'arquivos':{p.name:sha256(p) for p in destino.iterdir() if p.is_file()}})
    return relatorio


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--destino',type=Path,required=True);a=p.parse_args()
    if (a.destino/'auditoria.json').exists():
        raise FileExistsError('Auditoria já publicada; não sobrescrever.')
    a.destino.mkdir(parents=True,exist_ok=True)
    r=auditar(a.destino)
    print({'status':r['status'],'api':r['api_horaria_amostral'],'arquivo':str(a.destino/'auditoria.json')})
