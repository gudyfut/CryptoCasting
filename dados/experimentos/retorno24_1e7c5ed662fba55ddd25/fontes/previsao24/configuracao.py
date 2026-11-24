"""Contrato da primeira grade, com extensão futura separada da execução atual."""
from itertools import product
from .arquivos import ler_json

PARES = ('BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT')
FOLDS = {
    'DB1': ('2022-10-01', '2023-01-01', '2023-04-01'),
    'DB2': ('2023-01-01', '2023-04-01', '2023-07-01'),
    'DB3': ('2023-04-01', '2023-07-01', '2023-10-01'),
    'DB4': ('2023-07-01', '2023-10-01', '2024-01-01'),
    'B1': ('2023-10-01', '2024-01-01', '2024-07-01'),
    'B2': ('2024-04-01', '2024-07-01', '2025-01-01'),
    'B3': ('2024-10-01', '2025-01-01', '2025-07-01'),
    'B4': ('2025-04-01', '2025-07-01', '2026-01-01'),
}

def referencia():
    return {
        'versao': 'retorno24-1.0', 'ciclo': 'retorno24_001',
        'hipotese': 'Efeito de 1/3/7/14 dias de contexto na previsão do retorno em 24h; comparação pareada Mamba/LSTM, ARIMA e Naive.',
        'pares': list(PARES), 'contextos': [24,72,168,336], 'horizonte': 24,
        'candle_minutos': 60, 'origem_minutos': 60, 'entradas': ['retorno_log_horario'],
        'seeds': [17,42,2026], 'folds_desenvolvimento': ['DB1','DB2','DB3','DB4'],
        'folds_avaliacao': ['B1','B2','B3','B4'], 'inicio': '2021-01-01', 'fim': '2026-01-01',
        'mamba': {'largura':32,'camadas':2,'estado':16,'convolucao':4,'expansao':2,'dropout':0.1},
        'lstm': {'largura':32,'camadas':2,'dropout':0.1},
        'treino': {'epocas':100,'paciencia':10,'batch':64,'microbatch':32,'taxa_aprendizado':0.0002,'weight_decay':0.001,'clipping':1.0},
        'arima': {'ordens':[[p,1,q] for p,q in product(range(3),repeat=2)],'tendencia':'n','maxiter':200},
        'dispositivo':'cuda','backend':'oficial','bootstrap':{'dias':[7,14,28],'principal':14,'replicas':2000,'seed':20261020},
        'operacao':{'hora_utc':0,'latencia_minutos':1,'capital':10000.0,'taxa':0.001,'slippage':0.0005,'taxa_agravada':0.002,'slippage_agravado':0.001},
    }

def carregar(caminho):
    c = ler_json(caminho)
    # Variante exige outro contrato, em vez de aceitar opções silenciosamente ignoradas.
    if c != referencia():
        raise ValueError('Configuração não corresponde ao contrato retorno24-1.0; registrar e implementar uma revisão explícita.')
    return c

def celulas(c, fase):
    folds = c['folds_desenvolvimento'] if fase == 'desenvolvimento' else c['folds_avaliacao']
    if fase not in ('desenvolvimento','avaliacao'):
        raise ValueError('Fase desconhecida.')
    return [dict(fold=f, par=p, contexto=w, seed=s, modelo=m)
            for f,p,w,s,m in product(folds,c['pares'],c['contextos'],c['seeds'],('lstm','mamba'))]
