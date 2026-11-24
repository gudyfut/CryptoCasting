"""Figura de apresentação dos resultados conferidos; sem modelos ou simulações."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

p = Path(__file__).resolve().parent
r = json.loads((p / 'conferencia.json').read_text(encoding='utf-8'))
d = r['comparacao_detalhada']
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.titleweight': 'bold'})
fig, axs = plt.subplots(1, 2, figsize=(12, 4.6), layout='constrained')
azul, laranja, verde = '#205E91', '#C66422', '#197A63'
y = np.arange(6); a = axs[0]
a.barh(y - .17, [t['delta_mse_pct']['validacao'] for t in r['trajetorias']], height=.3, color=azul, label='Validação 2024')
a.barh(y + .17, [t['delta_mse_pct']['teste'] for t in r['trajetorias']], height=.3, color=laranja, label='Teste 2025')
a.set_yticks(y, [str(t['seed']) for t in r['trajetorias']]); a.invert_yaxis()
a.axvline(0, color='#444444', lw=.8)
a.set_xlabel('Mudança do MSE com Huber (%)\nNegativo = erro menor')
a.set_ylabel('Seed'); a.set_title('Previsão: melhora modesta e desigual')
a.legend(loc='lower right', frameon=False, fontsize=9)
a.grid(axis='x', alpha=.15); a.set_axisbelow(True)
a = axs[1]; x = np.arange(4)
labels = ['SpotR0\nsem custos', 'SpotR0\ncustos base', 'Smart\nsem custos', 'Smart\ncustos base']
ref = [d['spot_r0']['referencia']['bruto_mesmos_sinais']['retorno_liquido'],
       d['spot_r0']['referencia']['base']['retorno_liquido'],
       d['smart']['teste']['ideal']['referencia/smart']['retorno_liquido'],
       d['smart']['teste']['base']['referencia/smart']['retorno_liquido']]
huber = [d['spot_r0']['huber']['bruto_mesmos_sinais']['retorno_liquido'],
         d['spot_r0']['huber']['base']['retorno_liquido'],
         d['smart']['teste']['ideal']['huber/smart']['retorno_liquido'],
         d['smart']['teste']['base']['huber/smart']['retorno_liquido']]
for xx, valores, cor, nome in [(x - .18, ref, azul, 'Referência MSE'), (x + .18, huber, verde, 'Huber')]:
    barras = a.bar(xx, np.array(valores) * 100, width=.34, color=cor, label=nome)
    for barra, valor in zip(barras, valores):
        a.text(barra.get_x() + barra.get_width() / 2, 100 * valor + (.5 if valor >= 0 else -.5),
               f'{100 * valor:+.2f}%'.replace('.', ','), ha='center',
               va='bottom' if valor >= 0 else 'top', fontsize=8)
a.set_xticks(x, labels); a.axhline(0, color='#444444', lw=.8)
a.set_ylim(-23, 16); a.set_ylabel('Retorno médio de seis carteiras (%)')
a.set_title('Operação no teste (2025)')
a.legend(loc='upper right', frameon=False, fontsize=9)
a.grid(axis='y', alpha=.15); a.set_axisbelow(True)
fig.suptitle('Mamba16: Huber × MSE | mesmas seis seeds e demais configurações', fontsize=13, fontweight='bold')
fig.savefig(p / 'comparacao.png', dpi=180, facecolor='white')
fig.savefig(p / 'comparacao.svg', facecolor='white')
plt.close(fig)
