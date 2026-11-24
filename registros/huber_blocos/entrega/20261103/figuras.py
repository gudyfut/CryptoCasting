"""Figura da comparação encerrada, sem recalcular modelos ou carteiras."""
from pathlib import Path
import hashlib
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

DEST = Path(__file__).resolve().parent
RAIZ = DEST.parents[3]
r = json.loads((RAIZ/'dados/experimentos/huber_blocos_10dac17ea9df2c540c57/publicacoes/tentativa_001/resultados.json').read_text())
a = json.loads((DEST/'conferencia.json').read_text())
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                     'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.titleweight': 'bold', 'axes.labelcolor': '#374151'})
fig = plt.figure(figsize=(14, 10.5), layout='constrained')
gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.12])
verde = '#11845B'; vermelho = '#C45454'; azul = '#3967A9'; roxo = '#8164B0'
ax = fig.add_subplot(gs[0, 0])
seeds = a['por_seed_teste_media_quatro_blocos']
mud = [v['mudanca_percentual'] for v in seeds.values()]
ax.barh(list(seeds), mud, color=[verde if x < 0 else vermelho for x in mud])
ax.axvline(0, color='#8A929E', lw=1)
ax.invert_yaxis(); ax.set_xlim(-2.05, 3.15)
for i, v in enumerate(mud):
    ax.text(v+(.05 if v >= 0 else -.05), i, f'{v:+.2f}%',
            va='center', ha='left' if v >= 0 else 'right', fontsize=10)
ax.set_title('Efeito por seed: Huber em relação à MSE', loc='left', pad=14)
ax.set_xlabel('Mudança do MSE de teste (%) — menor é melhor')
ax.set_ylabel('Seed · média dos quatro períodos')

ax = fig.add_subplot(gs[0, 1])
bs = list(r['medias_por_bloco'])
mud_b = [100*(r['medias_por_bloco'][b]['teste']['huber']['mse']/
              r['medias_por_bloco'][b]['teste']['mse']['mse']-1) for b in bs]
ax.barh(['B1 · 2024 / 1º sem.', 'B2 · 2024 / 2º sem.',
         'B3 · 2025 / 1º sem.', 'B4 · 2025 / 2º sem.'], mud_b,
        color=[verde if x < 0 else vermelho for x in mud_b])
ax.axvline(0, color='#8A929E', lw=1); ax.invert_yaxis(); ax.set_xlim(-1.3, .55)
for i, v in enumerate(mud_b):
    ax.text(v+(.025 if v >= 0 else -.025), i, f'{v:+.3f}%',
            va='center', ha='left' if v >= 0 else 'right')
ax.set_title('Efeito por período: média das oito seeds', loc='left', pad=14)
ax.set_xlabel('Mudança do MSE de teste (%) — menor é melhor')
ax.text(.02, -.24, 'Média global: −0,290%\nIC95% da diferença / MSE de referência: −1,160% a +0,796%\nO intervalo cruza zero: melhoria ainda inconclusiva.',
        transform=ax.transAxes, fontsize=10, va='top', color='#374151')

ax = fig.add_subplot(gs[1, :])
x = np.arange(4); largura = .24
for j, (v, label, cor) in enumerate([('mse', 'Mamba treinado com MSE', azul),
                                    ('huber', 'Mamba treinado com Huber', verde),
                                    ('benchmark', 'Comprar e manter BTC', roxo)]):
    vals = [100*(r['carteiras'][f'{b}/benchmark/benchmark/comprar_manter/base']['retorno_liquido']
                  if v == 'benchmark' else r['medias_operacionais_por_bloco'][b][f'{v}/smart/base']['retorno_liquido']) for b in bs]
    barras = ax.bar(x+(j-1)*largura, vals, largura, label=label, color=cor)
    for barra, valor in zip(barras, vals):
        ax.annotate(f'{valor:+.1f}%', (barra.get_x()+barra.get_width()/2, valor),
                    xytext=(0, 4 if valor >= 0 else -5), textcoords='offset points',
                    ha='center', va='bottom' if valor >= 0 else 'top', fontsize=10)
ax.axhline(0, color='#8A929E', lw=1)
ax.set_xticks(x, ['B1 · 1º sem. 2024', 'B2 · 2º sem. 2024', 'B3 · 1º sem. 2025', 'B4 · 2º sem. 2025'])
ax.set_ylim(-30, 61); ax.set_ylabel('Retorno líquido no período (%)')
ax.set_title('Simulação Spot Smart: custos base e carteiras independentes', loc='left', pad=13)
ax.legend(loc='upper left', frameon=False, ncol=3, fontsize=10)
ax.text(0, -.15, '10.000 USDT reiniciados em cada bloco; médias de oito carteiras individuais, sem ensemble.\nRetornos não compõem uma série contínua. Períodos já consultados: avaliação retrospectiva.',
        transform=ax.transAxes, fontsize=10, color='#374151', va='top')
fig.suptitle('Mamba16 · comparação controlada MSE × Huber', fontsize=19, weight='bold')
for ext in ('png', 'svg'):
    fig.savefig(DEST/f'comparacao.{ext}', dpi=160, facecolor='white', bbox_inches='tight')
plt.close(fig)
nomes = ['conferir.py', 'conferencia.json', 'figuras.py', 'comparacao.png', 'comparacao.svg']
(DEST/'manifesto.json').write_text(json.dumps({'arquivos': {
    n: hashlib.sha256((DEST/n).read_bytes()).hexdigest() for n in nomes}}, indent=2), encoding='utf-8')
