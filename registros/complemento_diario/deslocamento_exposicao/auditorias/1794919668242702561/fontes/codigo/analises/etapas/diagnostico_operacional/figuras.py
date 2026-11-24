"""Figuras posteriores; não modifica observações ou escolhe políticas."""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def gerar(dest):
    t=json.loads((dest/'tabelas.json').read_text(encoding='utf-8'))
    canais=pd.DataFrame(json.loads((dest/'canais.json').read_text(encoding='utf-8')))
    figuras=dest/'figuras'; figuras.mkdir()
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':145})
    receitas=['R0','P0','C01','C02','C03','C04','C05','C06']
    s=pd.DataFrame(t['receitas']); s=s[s.fase=='comparacao'].set_index('receita').loc[receitas]
    fig,ax=plt.subplots(1,2,figsize=(12,4.8))
    xx=np.arange(len(s)); ax[0].bar(xx-.17,s.precisao_alta*100,.34,label='Preço sobe, quando prefere comprar')
    ax[0].bar(xx+.17,s.precisao_queda*100,.34,label='Preço cai, quando prefere vender')
    ax[0].set_xticks(xx,receitas); ax[0].set_ylabel('Precisão direcional (%)'); ax[0].set_ylim(0,100)
    ax[0].axhline(50,color='gray',linestyle=':',linewidth=1); ax[0].legend(fontsize=8,loc='upper right')
    c=canais[canais.fase=='comparacao'].groupby('receita').razao_std.mean().reindex(receitas)
    ax[1].bar(receitas,c*100,color='#7755aa'); ax[1].set_ylabel('Variação da previsão / variação do alvo (%)')
    ax[1].set_title('Amplitude média por célula/canal')
    fig.suptitle('Preferência por lado e amplitude das previsões — S, abr–dez/2023')
    fig.text(.5,.01,'R0: retorno terminal; demais: payoffs por lado. Preferência por lado não é probabilidade de alta/queda.',ha='center',fontsize=9)
    fig.tight_layout(rect=[0,.055,1,.94]); fig.savefig(figuras/'01_direcao_amplitude.png'); plt.close(fig)
    fig,axs=plt.subplots(2,4,figsize=(13,7),sharex=True,sharey=True)
    for ax,r in zip(axs.flat,receitas):
        for fase,label in [('calibracao','C: usado na calibração'),('comparacao','S: período seguinte')]:
            q=pd.DataFrame(t['quintis']); q=q[(q.receita==r)&(q.fase==fase)].sort_values('quintil_c')
            ax.plot(q.quintil_c,q.payoff_escolhido_medio*100,'o-',label=label)
        ax.axhline(0,color='gray',linewidth=.8); ax.set_title(r); ax.set_xticks([1,2,3,4,5]); ax.grid(alpha=.15)
    axs[0,0].legend(fontsize=8); fig.suptitle('Sinais mais fortes antecipam payoffs melhores?')
    fig.supxlabel('Quintil de score, limites definidos em C por modelo/seed/recorte')
    fig.supylabel('Payoff líquido médio hipotético (%)')
    fig.text(.5,.045,'Eventos horários sobrepostos; estas médias NÃO são rentabilidade de carteira. Sem ajuste de filtro em S.',ha='center',fontsize=9)
    fig.tight_layout(rect=[.02,.08,1,.95]); fig.savefig(figuras/'02_forca_sinal.png'); plt.close(fig)
    f=pd.DataFrame(t['faixas']); f=f[(f.receita=='R0')&(f.fase=='comparacao')&(f.n>0)&(f.minimo>=0)]
    fig,ax=plt.subplots(1,2,figsize=(11,4.8)); labels=[f'{lo*100:g}–{hi*100:g}%' if pd.notna(hi) else f'≥{lo*100:g}%' for lo,hi in zip(f.minimo,f.maximo)]
    ax[0].bar(labels,f.acuracia*100,color='#267582'); ax[0].axhline(50,color='gray',linestyle=':'); ax[0].set_ylim(0,100)
    ax[0].set_ylabel('Acerto da preferência de lado (%)'); ax[1].bar(labels,f.n,color='#899bad'); ax[1].set_ylabel('Previsões (três seeds; dependentes)')
    for a in ax: a.tick_params(axis='x',rotation=25)
    fig.suptitle('R0: intensidade prevista da variação de preço em 24h')
    fig.text(.5,.01,'Não confundir magnitude com confiança. Grupos com menos dias exigem cautela; suporte completo nas tabelas.',ha='center',fontsize=9)
    fig.tight_layout(rect=[0,.06,1,.94]); fig.savefig(figuras/'03_magnitude_terminal.png'); plt.close(fig)
    tr=pd.read_parquet(dest/'operacoes_herdadas.parquet'); tr=tr[(tr.fase=='comparacao')&(tr.cenario=='base')]
    fig,ax=plt.subplots(1,2,figsize=(11,5))
    por=tr.groupby('lado')[['bruto_com_slippage','comissao','funding','liquido']].sum()/3
    for i,col in enumerate(por.columns): ax[0].bar(np.arange(len(por))+(i-1.5)*.2,por[col]*( -1 if col=='comissao' else 1),.2,label=col.replace('_',' '))
    ax[0].set_xticks(np.arange(len(por)),['Venda' if x<0 else 'Compra' for x in por.index]); ax[0].axhline(0,color='gray',linewidth=.8)
    ax[0].set_ylabel('USDT por carteira, média das três seeds'); ax[0].legend(fontsize=8)
    saidas=tr.groupby('motivo').liquido.sum()/3; ax[1].bar(saidas.index,saidas,color=['#bc6262' if v<0 else '#267582' for v in saidas]); ax[1].axhline(0,color='gray',linewidth=.8); ax[1].set_ylabel('PnL líquido médio (USDT)')
    fig.suptitle('C05/D2 — operações efetivamente simuladas em S (jul–set/2023)')
    fig.text(.5,.01,'Capital inicial: 10.000 USDT. Bruto já inclui slippage. Atribuição contábil, sem simular novas saídas.',ha='center',fontsize=9)
    fig.tight_layout(rect=[0,.06,1,.94]); fig.savefig(figuras/'04_operacoes.png'); plt.close(fig)
