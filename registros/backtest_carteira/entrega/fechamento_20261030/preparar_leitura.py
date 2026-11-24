"""Apresentação posterior; lê resultados encerrados, sem repetir simulações."""
from pathlib import Path
import hashlib
import json
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

RAIZ = Path(__file__).resolve().parents[4]
PASTA = RAIZ / 'dados/experimentos/backtest_carteira_8ec8a66648313caa48e3'
DEST = Path(__file__).resolve().parent
r = json.loads((PASTA / 'resultados/comparacao.json').read_text())
assert not json.loads((PASTA / 'processo.json').read_text())['ativo']
seeds = [17,42,2026,7,123,31415]

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,
                     'axes.spines.right':False,'axes.spines.top':False})
fig, axs = plt.subplots(1,2,figsize=(13,5.4))
ax = axs[0]
for pol, label, cor, estilo in [('smart','Mamba16: previsão variável','#22668C','-'),
                               ('smart_constante','Controle: previsão constante','#AE7D37',':')]:
    ds = [pd.read_parquet(PASTA/f'resultados/teste/base/{pol}/estado16_{s}/diarios.parquet') for s in seeds]
    ax.plot(pd.to_datetime(ds[0].origem_utc)+pd.Timedelta(days=1),
            np.mean([d.capital_fim.to_numpy() for d in ds],axis=0),
            label=label,color=cor,linestyle=estilo,lw=1.9)
d = pd.read_parquet(PASTA/'resultados/teste/base/comprar_manter/benchmark/diarios.parquet')
ax.plot(pd.to_datetime(d.origem_utc)+pd.Timedelta(days=1),d.capital_fim,
        label='Comprar e manter',color='#555555',ls='--',lw=1.4)
ax.axhline(10000,color='#999999',lw=1,label='Caixa')
ax.set_title('Smart: o sinal variável acrescentou valor?',loc='left',pad=12)
ax.set_ylabel('Capital (USDT)')
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b/%y'))
ax.legend(frameon=False,fontsize=8,loc='upper left')
ax=axs[1];x=np.arange(3)
for j,(cenario,cor,nome) in enumerate([('ideal','#B9C6D0','Sem custos'),('base','#22668C','Custos base'),('agravado','#BE8441','Custos agravados')]):
    valores=[100*r['medias']['teste'][cenario][pol]['mamba16_seis']['retorno_liquido']
             for pol in ['diaria24','vanilla','smart']]
    ax.bar(x+(j-1)*.25,valores,.23,color=cor,label=nome)
    if cenario=='base':
        for pos,valor in zip(x,valores):
            ax.text(pos,valor-1,f'{valor:.2f}%'.replace('.',','),ha='center',va='top',fontsize=9)
ax.set_xticks(x,['Saída diária (24h)','Vanilla (1%)','Smart (2%)'])
ax.set_ylim(-35,5);ax.axhline(0,color='#777777',lw=.8)
ax.set_ylabel('Retorno médio (%)')
ax.set_title('Mesmos modelos; políticas operacionais distintas',loc='left',pad=12)
ax.legend(frameon=False,fontsize=8,loc='lower right')
for ax in axs:
    ax.grid(axis='y',color='#E2E7EB');ax.set_axisbelow(True)
fig.suptitle('Mamba16: reduzir a perda não foi suficiente para produzir lucro',x=.07,y=.98,ha='left',fontsize=15,fontweight='bold')
fig.text(.07,.035,'2025 · Spot BTC/USDT · decisões diárias · média de seis carteiras individuais · avaliação retrospectiva',fontsize=9,color='#555555')
fig.subplots_adjust(left=.07,right=.98,bottom=.17,top=.83,wspace=.26)
arquivos={}
for ext in ['png','svg']:
    p=RAIZ/f'docs/figuras/backtest_carteira_8ec8a66648313caa48e3/leitura_resultados.{ext}'
    assert not p.exists()
    fig.savefig(p,dpi=170,facecolor='white',bbox_inches='tight')
    arquivos[p.relative_to(RAIZ).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
plt.close(fig)

p=RAIZ/'docs/resultados_backtest_carteira.md'
texto=p.read_text(encoding='utf-8')
# Correções editoriais de espaçamento; números científicos ficam inalterados.
texto=re.sub(r'(?<=\d)(?=[A-Za-zÀ-ÿ])',' ',texto)
texto=re.sub(r'(?<=[A-Za-zÀ-ÿ])(?=\d)',' ',texto)
texto=re.sub(r',(?=[A-Za-zÀ-ÿ])',', ',texto)
texto=texto.replace('Smart 2%','Smart (2%)').replace('Vanilla 1%','Vanilla (1%)')
# As expressões regulares não se aplicam aos destinos/IDs/links originais.
original=(DEST/'relatorio_automatico_preservado.md').read_text(encoding='utf-8')
for antes in re.findall(r'`[^`]*`|\]\([^\n]*?\)',original):
    depois=re.sub(r'(?<=\d)(?=[A-Za-zÀ-ÿ])',' ',antes)
    depois=re.sub(r'(?<=[A-Za-zÀ-ÿ])(?=\d)',' ',depois)
    depois=re.sub(r',(?=[A-Za-zÀ-ÿ])',', ',depois)
    texto=texto.replace(depois,antes)
texto=texto.replace('drawdown médio por minuto-close de +34,43%','drawdown médio por fechamento de minuto de 34,43%')
inicio=texto.index('## Resultado principal e interpretação')
fim=texto.index('## Como a estratégia usa o modelo')
novo='''## Resultado principal e interpretação

**Não encontramos uma estratégia Mamba lucrativa e estável neste teste.** As previsões e os modelos são os mesmos; somente a camada operacional mudou. Com capital inicial de 10.000 USDT, a Smart aplicada ao Mamba16 terminou com **9.120,54 USDT em média: −8,79% líquidos**, desvio entre seeds de 1,57 ponto percentual. Nenhuma das seis seeds teve lucro: resultados entre −9,94% e −5,77%. A média é de seis carteiras individuais, não de um modelo ensemble.

No mesmo motor e nos mesmos instantes, a regra de saída diária perdeu 18,47%; a Smart perdeu 8,79%. Isso é melhora descritiva de **9,67 pontos percentuais**, mas não é ganho isolado de custos: a Smart também mudou os momentos e o tamanho da exposição. Ficou, em média, 89,40% investida, contra 15,94% na regra diária. Seu drawdown médio foi 34,43%, contra 28,33% na diária. Perder menos no encerramento não significou suportar menos risco durante o caminho.

O giro médio caiu de 111,87 para 4,91 vezes o capital inicial. As comissões e o slippage contabilizados somaram aproximadamente 1.678,02 USDT na saída diária e 73,63 USDT na Smart. Esses lançamentos já estão embutidos na carteira; não devem ser subtraídos de novo. A diferença entre cenários de custo não equivale exatamente à soma dos custos, pois o saldo disponível e as ordens posteriores também mudam.

Mesmo sem comissão e slippage, a Smart/Mamba16 perdeu 8,10%; com custos agravados perdeu 9,49%. Portanto, neste caso, o custo excessivo da regra antiga era parte do problema, mas removê-lo não revelou uma estratégia lucrativa.

O controle substituiu cada previsão diária por um único número: a média das previsões desse modelo em 2024, sem usar a média futura de 2025. Essa Smart de previsão constante perdeu **8,66%**, muito perto dos −8,79% do modelo variável. O contraste temporal principal teve IC95% incluindo zero. Não foi demonstrado que variar as previsões acrescenta valor econômico a esse viés constante. Esse controle não iguala perfeitamente a exposição; por isso também publicamos caixa, comprar/manter e exposição.

Comprar e manter perdeu 5,80% e permanecer em caixa retornou 0%. Assim, a Smart/Mamba16 teve desempenho descritivo pior que ambos. Isso não estabelece uma diferença estatística definitiva entre todas as políticas ou superioridade universal do caixa.

## Lucros isolados, período e comparação entre modelos

A Vanilla/Mamba16 perdeu 0,80% em média: a seed17 ganhou 9,06%, a seed42 perdeu 13,84% e as outras quatro não fizeram operações. Promover apenas a seed17 seria selecionar um resultado favorável depois de observá-lo. O retorno próximo de zero da média também não demonstra qualidade: a maioria das carteiras ficou inteiramente em caixa.

A Vanilla/LSTM retornou 1,58% em média nas três seeds: duas ganharam 2,37% cada e uma ficou parada. Cada carteira ativa teve somente uma compra e a venda terminal. As duas sementes lucrativas fizeram essencialmente a mesma aposta longa, não centenas de operações independentes. É um resultado descritivo positivo, insuficiente para declarar uma estratégia operacional robusta. Na comparação Smart pareada nas três seeds comuns, Mamba16 perdeu 8,29%, LSTM 5,20% e CryptoMamba adaptado 9,49%; as três médias foram negativas.

No desenvolvimento de 2024, a Smart/Mamba16 lucrou 81,45%, mas comprar/manter lucrou 118,69%. O CryptoMamba adaptado lucrou 109,41% nesse ano e perdeu 9,47% em 2025. Como suas previsões quase não variam, essa mudança entre anos ilustra como uma estratégia pode ganhar num período de alta por ficar comprada, sem demonstrar capacidade de antecipar movimentos. O ano de 2024 participou da seleção dos checkpoints; não é confirmação independente.

## O que foi encontrado no CryptoMamba publicado

O [artigo, seção6](https://arxiv.org/html/2501.01010v2) informa saldos finais partindo de100 USD:246,58 na Vanilla,213,20 na Smart e262,78 na Extended Smart. Isso corresponde a retornos de146,58%,113,20% e162,78%, respectivamente; não são percentuais fornecidos diretamente na tabela.

No [código público fixado por commit](https://github.com/MShahabSepehri/CryptoMamba/blob/fef42727861a9c3a32241283ab981ef21a49e291/utils/trade.py), as posições são mantidas entre decisões. A Vanilla usa limiar de1%; a Smart compra parte do caixa ou vende parte do BTC segundo a distância entre preço e previsão. Não há débito explícito de comissão ou slippage. O limiar de1% é um filtro, não um custo realmente pago. A Extended Smart permite posição vendida e não foi transferida para nosso estudo Spot sem dados de margem/financiamento.

Isso ajuda a entender a diferença para nossa saída diária, mas não reproduz os lucros publicados: são dados, modelos, calendários e hipóteses de execução diferentes. O desempenho precisa ser comparado a comprar/manter no próprio período, e o lucro por si só não mede a contribuição da previsão.

'''
texto=texto[:inicio]+novo+texto[fim:]
texto=texto.replace('![Curvas e comparações](figuras/backtest_carteira_8ec8a66648313caa48e3/carteiras.png)',
'''![Resultado operacional e controle de previsão constante](figuras/backtest_carteira_8ec8a66648313caa48e3/leitura_resultados.png)

[Figura completa de desenvolvimento/teste, custos e seeds](figuras/backtest_carteira_8ec8a66648313caa48e3/carteiras.png). As figuras automáticas originais permanecem intactas; a ilustração acima reorganiza os mesmos dados.''')
texto+='''
## Fechamento e continuidade

Conclusão da grade em30/10/2026, às02:44:15 de Brasília:369 simulações, zero treinamentos/inferências novas,19 fontes atuais e copiadas,84 insumos e1.163 arquivos anteriores conferidos. A conferência posterior recalculou médias, saldos, custos, retornos diários e os três contrastes bootstrap, além dos manifestos. [Recibo e verificador](../registros/backtest_carteira/entrega/fechamento_20261030/conferencia.json).

A tentativa inicial `b9fce5ae0300ce91ba69` falhou antes da primeira simulação por leitura de matriz somente leitura. Seus fontes, incidente e ponteiro permanecem preservados. A execução `8ec8a66648313caa48e3` acrescenta um leitor com cópia explícita, sem mudar política ou descartar resultados;12 testes sintéticos foram aprovados. O protocolo congelado conserva o lançador original; o lançador corrigido é `run_backtest_revisado.py`, indicado nos registros e na ADR. A execução concluída não deve ser repetida para regenerar relatório.

Este fechamento não promove uma estratégia ou inicia outra busca. Recomenda-se usar a camada operacional para avaliar futuras hipóteses preditivas com modelos e regras identificados, sem escolher configurações pela seed lucrativa nem recalibrar políticas repetidamente sobre2025. A referência Mamba16 e os testes de configuração anteriores continuam separados. Uma eventual hipótese Adam→AdamW pertence ao CryptoMamba adaptado; não é alteração já executada neste backtest. O Mamba16 de referência já utiliza AdamW.
'''
texto=texto.replace('em30/10','em 30/10').replace('às02:','às 02:').replace(':369 ',': 369 ').replace(',19 ', ', 19 ').replace(',84 ', ', 84 ').replace('e1.163', 'e 1.163').replace(';12 ', '; 12 ').replace('sobre2025','sobre 2025')
p.write_text(texto,encoding='utf-8')
(DEST/'apresentacao.json').write_text(json.dumps({'resultado_sha256':hashlib.sha256((PASTA/'resultados/comparacao.json').read_bytes()).hexdigest(),
 'figuras_novas':arquivos,'relatorio':p.relative_to(RAIZ).as_posix(),'relatorio_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
 'original_preservado':'registros/backtest_carteira/entrega/fechamento_20261030/relatorio_automatico_preservado.md',
 'alteracao_cientifica':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Apresentação concluída; dados, fontes e figuras automáticas preservados.')
