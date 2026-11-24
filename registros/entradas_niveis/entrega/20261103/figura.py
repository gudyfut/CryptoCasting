"""Figura editorial de resultados preservados; sem novo experimento."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path.cwd()
P=ROOT/'registros/entradas_niveis/entrega/20261103'
r=json.loads((ROOT/'dados/experimentos/entradas_niveis_76f6c437e70eaaa605ad/publicacoes/tentativa_001/resultados.json').read_text())
blocos=['B1','B2','B3','B4'];rotulos=['2024 / 1º sem.','2024 / 2º sem.','2025 / 1º sem.','2025 / 2º sem.']
cores={'atual':'#2563eb','crua':'#e68728','niveis_padronizados':'#14968d','comprar_manter':'#697386'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(1,2,figsize=(14,5.6),layout='constrained')
x=np.arange(4)
for j,v in enumerate(['crua','niveis_padronizados']):
 vals=[100*(r['medias_por_bloco'][b]['teste'][v]['mse']/r['medias_por_bloco'][b]['teste']['atual']['mse']-1) for b in blocos]
 bars=axs[0].bar(x+(j-.5)*.32,vals,.30,color=cores[v],label='Crua' if v=='crua' else 'Níveis padronizados')
 for bar,vv in zip(bars,vals):axs[0].text(bar.get_x()+bar.get_width()/2,vv+(.13 if vv>=0 else -.15),f'{vv:+.2f}%',ha='center',va='bottom' if vv>=0 else 'top',fontsize=9)
axs[0].axhline(0,color='#64748b',linewidth=.8);axs[0].set_ylim(-7.4,5)
axs[0].set_title('Erro de previsão frente à entrada atual',loc='left',fontweight='bold',pad=15)
axs[0].set_ylabel('Variação do MSE de teste (%) · abaixo de zero é melhor')
axs[0].set_xticks(x,rotulos);axs[0].legend(loc='upper center',ncol=2,frameon=False)
axs[0].grid(axis='y',alpha=.15);axs[0].set_axisbelow(True)
for j,v in enumerate(['atual','crua','niveis_padronizados','comprar_manter']):
 vals=[100*(r['carteiras'][f'{b}/benchmark/benchmark/comprar_manter/base']['retorno_liquido'] if v=='comprar_manter' else r['medias_operacionais_por_bloco'][b][v+'/smart/base']['retorno_liquido']) for b in blocos]
 lab={'atual':'Atual','crua':'Crua','niveis_padronizados':'Níveis padronizados','comprar_manter':'Comprar e manter'}[v]
 bars=axs[1].bar(x+(j-1.5)*.20,vals,.19,color=cores[v],label=lab)
 for bar,vv in zip(bars,vals):axs[1].text(bar.get_x()+bar.get_width()/2,vv+(.7 if vv>=0 else -.7),f'{vv:.1f}',ha='center',va='bottom' if vv>=0 else 'top',fontsize=8)
axs[1].axhline(0,color='#64748b',linewidth=.8);axs[1].set_ylim(-27,58)
axs[1].set_title('Carteiras Smart e referência passiva, com custos',loc='left',fontweight='bold',pad=15)
axs[1].set_ylabel('Retorno líquido de cada bloco (%)')
axs[1].set_xticks(x,rotulos);axs[1].legend(loc='upper center',ncol=2,frameon=False,fontsize=9)
axs[1].grid(axis='y',alpha=.15);axs[1].set_axisbelow(True)
fig.suptitle('OHLCV cru: diferença de erro depende do período; lucro segue outro padrão',fontweight='bold',fontsize=14)
fig.supxlabel('Oito seeds por versão/bloco; médias de modelos individuais. Carteiras independentes. Taxa 0,10% + slippage 0,05% por lado.',fontsize=10)
fig.savefig(P/'resultados.png',dpi=160)
print(P/'resultados.png')
