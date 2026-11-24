"""Fechamento documental, preservando o texto/índices anteriores."""
from pathlib import Path
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone

RAIZ=Path(__file__).resolve().parents[4]
DEST=Path(__file__).resolve().parent
def ler(nome):return json.loads((RAIZ/nome).read_text(encoding='utf-8'))
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def salvar(nome,v):(RAIZ/nome).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def trocar(nome,antes,depois):
    p=RAIZ/nome;t=p.read_text(encoding='utf-8');assert antes in t,nome
    p.write_text(t.replace(antes,depois,1),encoding='utf-8')

nomes=['docs/resultados_backtest_carteira.md','README.md','plano.md','docs/andamento.md',
       'docs/README.md','docs/roteiro_redacao_tcc.md','registros/README.md',
       'registros/catalogo_estudos.json','registros/backtest_carteira/estado.json']
for nome in nomes:
    d=DEST/'indices_antes'/nome
    assert not d.exists();d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(RAIZ/nome,d)

p=RAIZ/'docs/resultados_backtest_carteira.md';t=p.read_text(encoding='utf-8')
for a,b in {'.369 simulações':'. 369 simulações',',17 séries':', 17 séries',
            'seed17':'seed 17','seed42':'seed 42','seção6':'seção 6','de100':'de 100',
            'USD:246':'USD: 246',',213':', 213','e262':'e 262','de146':'de 146',
            ',113':', 113','e162':'e 162','de1%':'de 1%','noUSDT':'no USDT',
            'mamba 16_seis':'Mamba16 (6 seeds)','mamba 16_tres':'Mamba16 (3 seeds)',
            'cryptomamba_seis':'CryptoMamba adaptado (6 seeds)',
            'cryptomamba_tres':'CryptoMamba adaptado (3 seeds)','lstm_tres':'LSTM (3 seeds)',
            '| naive |':'| Naive |','| arima |':'| ARIMA |','| validacao |':'| Validação |',
            '| teste |':'| Teste |','| diaria 24 |':'| Saída diária (24h) |',
            '| vanilla |':'| Vanilla (1%) |','| smart |':'| Smart (2%) |',
            '| smart_constante |':'| Smart com previsão constante |',
            '| comprar_manter |':'| Comprar e manter |', '| caixa |':'| Caixa |',
            'circular14dias':'circular de 14 dias', 'circular 14 dias':'circular de 14 dias',
            '2000réplicas':'2.000 réplicas','2000 réplicas':'2.000 réplicas',
            'IC95%':'IC de 95%','2024participou':'2024 participou','2025já':'2025 já',
            'de2024':'de 2024','de2025':'de 2025','em2024':'em 2024','em2025':'em 2025',
            'Todas as 369simulações':'Todas as 369 simulações',
            'O controle diária 24':'O controle de saída diária em 24h'}.items():t=t.replace(a,b)
t=re.sub(r'(\d{4}-\d{2}-\d{2}) T (\d{2}:)',r'\1T\2',t)
t=t.replace('N | Retorno base | Drawdown médio','N | Retorno base | Queda máxima média')
linhas=t.splitlines()
for i,l in enumerate(linhas):
    if l.startswith('| ') and ('| Validação |' in l or '| Teste |' in l):
        campos=l.split('|')
        # Queda máxima é magnitude de perda, não um retorno positivo.
        campos[6]=campos[6].replace('+','')
        linhas[i]='|'.join(campos)
t='\n'.join(linhas)+'\n'
t+='\nNa preparação sintética, uma incompatibilidade de unidades temporais foi encontrada e corrigida antes do congelamento; testes e fontes anteriores estão em `registros/backtest_carteira/preparacao/incidente_unidades_temporais/`. Isso não foi treinamento nem simulação de mercado descartada.\n'
p.write_text(t,encoding='utf-8')

trocar('README.md','**Estado atual: referências OHLCV, estados8/16/32/64 e taxa concluídos/conferidos; CryptoMamba adaptado concluído e conferido.**',
'''**Estado atual: treinamentos OHLCV e CryptoMamba adaptado concluídos/conferidos; backtest de carteira também encerrado em 30/10/2026.** As 369 simulações reutilizam previsões preservadas, sem novos treinos. [Resultados e gráficos operacionais](docs/resultados_backtest_carteira.md), [protocolo](docs/protocolo_backtest_carteira.md) e [estado verificável](registros/backtest_carteira/estado.json). Smart/Mamba16: −8,79% líquidos em média no teste retrospectivo, sem seed lucrativa; a mudança de operação não demonstrou vantagem preditiva. As rodadas de treinamento e o SpotR0 permanecem separados.''')
trocar('plano.md','Atualizado em 29/10/2026.','Atualizado em 30/10/2026.')
trocar('plano.md','## Etapas','''A camada operacional posterior está concluída: [backtest de carteira retida](docs/resultados_backtest_carteira.md), 369 simulações com previsões já existentes e zero treinamentos. A Smart reduziu a perda do Mamba16 frente à saída diária, mas não produziu lucro no teste retrospectivo nem demonstrou ganho sobre seu controle constante. Nenhuma estratégia ou configuração foi promovida por esse resultado; novas hipóteses exigem escopo próprio.

## Etapas''')
trocar('docs/andamento.md','# Andamento do CryptoCasting', '''# Andamento do CryptoCasting

## Backtest de carteira concluído e conferido em 30/10/2026

Grade `8ec8a66648313caa48e3` concluída às 02:44:15 de Brasília: 369 simulações, 17 séries herdadas e zero treinamentos/inferências novas. Smart, Vanilla, controle de saída diária, caixa, comprar/manter e controle de previsão constante foram mantidos no orçamento original. As 369 carteiras têm verificador de lançamentos independente. Conferência posterior de 19 fontes atuais/copiadas, 84 insumos, 2.585 arquivos publicados e 1.163 anteriores preservados; médias e três contrastes bootstrap recalculados sem repetir o executor. [Relatório único](resultados_backtest_carteira.md), [estado](../registros/backtest_carteira/estado.json) e [recibo posterior](../registros/backtest_carteira/entrega/fechamento_20261030/conferencia.json).

Mamba16/seis seeds no teste: Smart −8,79%, saída diária no mesmo motor −18,47%, Vanilla −0,80%; controle Smart constante −8,66%, comprar/manter −5,80% e caixa 0%. Nenhuma seed Mamba16/Smart foi lucrativa; IC95% do contraste com viés inclui zero. Smart aumenta exposição/drawdown frente à saída diária; não atribuir toda diferença ao custo. Vanilla/LSTM +1,58% em três seeds, porém duas carteiras fizeram a mesma única compra e uma não operou. Em 2024, desenvolvimento, Smart/Mamba16 +81,45% contra comprar/manter +118,69%. Não promover por lucro isolado ou tratar como holdout novo/walk-forward.

A tentativa inicial interrompida antes da primeira simulação permanece intacta. O novo leitor alterou apenas a cópia da matriz pandas; o protocolo congelado, a correção, as fontes antigas e os testes sintéticos estão identificados nos registros. Relatório automático e figuras originais preservados; revisão de apresentação usa os mesmos dados. Fonte/receita/modelos/previsões dos ciclos anteriores não mudaram. Não há novo treinamento autorizado por este fechamento.
''')
trocar('docs/README.md','A avaliação operacional posterior usa [carteira retida](protocolo_backtest_carteira.md), conforme ADR0015, com [estado próprio](../registros/backtest_carteira/estado.json). São simulações sobre previsões já treinadas, sem modificar os modelos ou o SpotR0. Resultados continuam retrospectivos e incluem controles de exposição/viés/custos.',
'''A avaliação operacional posterior de [carteira retida](protocolo_backtest_carteira.md), ADR0015, está concluída e conferida: [resultados e interpretação](resultados_backtest_carteira.md), [estado próprio](../registros/backtest_carteira/estado.json). São 369 simulações sobre previsões já treinadas, sem modificar modelos ou SpotR0. Resultados retrospectivos incluem controles de exposição, viés e custos; nenhuma vantagem operacional robusta do Mamba foi demonstrada.''')
trocar('docs/README.md','Contrato técnico e implementação preparados; ainda sem treinamento de mercado.',
       'Distingue a preparação histórica preservada das rodadas modulares já concluídas; seus resultados estão nos estados próprios.')
trocar('docs/roteiro_redacao_tcc.md','## Estrutura da nova etapa OHLCV para o artigo','''## Estrutura da nova etapa OHLCV para o artigo

O [backtest de carteira retida](resultados_backtest_carteira.md) é uma avaliação operacional posterior de previsões já treinadas, não uma nova rede ou ganho de MSE. Descrever regras, causalidade, custos, exposição, drawdown e contraste com previsão constante; 2024 participou da seleção dos checkpoints e 2025 já era conhecido. Separar retorno médio entre seeds de ensemble, diferença de custos de mudança de exposição e lucros isolados de vantagem robusta. Não chamar as simulações de operações reais, nem Smart 2% de stop ou faixa probabilística calibrada. O protocolo, a tentativa inicial interrompida, a revisão do leitor e o fechamento têm identidades próprias; nenhuma tentativa foi descartada para obter lucro.''')
with (RAIZ/'registros/README.md').open('a',encoding='utf-8') as arq:
    arq.write('\nO backtest foi concluído: `backtest_carteira/entrega/fechamento_20261030/` contém conferência posterior, verificador e versões editoriais anteriores. O manifesto original da execução e suas figuras não foram substituídos; `apresentacao.json` vincula o relatório interpretativo e a figura de leitura aos mesmos dados. O índice raiz aponta o fechamento em `revisao_loader/`, mantendo `execucao.json` da tentativa inicial. Nenhuma hipótese de treinamento decorre automaticamente desse resultado.\n')

fim=ler('registros/backtest_carteira/revisao_loader/fechamento.json')
estado=ler('registros/backtest_carteira/estado.json')
estado.update(situacao='concluido_conferido',simulacoes_concluidas=369,
              fechamento='registros/backtest_carteira/revisao_loader/fechamento.json',
              resultado=fim['resultado'],resultado_sha256=fim['resultado_sha256'],
              relatorio='docs/resultados_backtest_carteira.md',
              conferencia_posterior={'arquivo':'registros/backtest_carteira/entrega/fechamento_20261030/conferencia.json',
                                      'sha256':h(DEST/'conferencia.json')},
              treinamento_novo_autorizado=False,
              atualizado_utc=datetime.now(timezone.utc).isoformat())
salvar('registros/backtest_carteira/estado.json',estado)
catalogo=ler('registros/catalogo_estudos.json')
linha=catalogo['avaliacoes_operacionais'][-1];assert linha['execucao']=='8ec8a66648313caa48e3'
linha.update(situacao='concluido_conferido',simulacoes_concluidas=369,
             fechamento=estado['fechamento'],resultado=fim['resultado'],
             resultado_sha256=fim['resultado_sha256'],relatorio=estado['relatorio'],
             conferencia_posterior=estado['conferencia_posterior'],
             encerramento_utc=fim['utc'])
catalogo['etapa_atual']['backtest_carteira']=linha.copy()
catalogo['etapa_atual']['situacao']='backtest_carteira_concluido_conferido'
catalogo['etapa_atual']['limite']='Rodadas OHLCV e avaliações operacionais concluídas; divisão fixa retrospectiva, sem alegação de walk-forward/holdout intocado. Nenhum novo treino ou busca automática.'
salvar('registros/catalogo_estudos.json',catalogo)
ap=ler('registros/backtest_carteira/entrega/fechamento_20261030/apresentacao.json')
ap['relatorio_sha256']=h(RAIZ/'docs/resultados_backtest_carteira.md')
salvar('registros/backtest_carteira/entrega/fechamento_20261030/apresentacao.json',ap)
salvar('registros/backtest_carteira/entrega/fechamento_20261030/indices_documentais.json',
       {'utc':datetime.now(timezone.utc).isoformat(),
        'arquivos':{n:h(RAIZ/n) for n in nomes},
        'fontes_cientificas_alteradas':False,'copias_anteriores':'indices_antes/'})
print('Índices e relatório atualizados. Fontes, resultados e ponteiro inicial preservados.')
