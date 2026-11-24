# Fundamentos de SSM/Mamba e leitura crítica do CryptoMamba

Material de estudo elaborado em 28/10/2026 a pedido do pesquisador. Complementa a [revisão anterior](revisao_mamba_criptomamba.md). Não altera o ciclo de pré-normalização autorizado, suas fontes ou seus resultados. O estado desse ciclo deve ser consultado nos recibos próprios, não inferido desta revisão.

## Da memória ao SSM

Uma sequência pode ser processada mantendo um estado interno: números que resumem o passado relevante para a tarefa. Um estado aprendido não tem automaticamente significado econômico, como tendência ou volatilidade. Essas interpretações precisam de análise, não decorrem do nome da arquitetura.

Exemplo didático escalar: `h_t = a*h_(t-1) + u_t`. Se houver um impulso de valor 1 seguido somente de zeros, resta `a^k` após k passos. Com a=0,3 a informação desaparece rapidamente; com a=0,95 conserva-se aproximadamente 59,87% após dez passos. É uma construção matemática ilustrativa, não um experimento de mercado ou a implementação completa de Mamba. Combinar diferentes escalas de memória permite representar efeitos rápidos e lentos.

O SSM linear clássico usa `dh/dt = A*h + B*u`, `z = C*h + D*u`. A define a dinâmica do estado; B escreve a entrada no estado; C lê o estado; D permite um caminho direto. Para observações discretas, escreve-se `h_t = A_bar*h_(t-1) + B_bar*u_t`. O S4 aplica estrutura a essas operações para processar sequências longas eficientemente. SSM é uma família ampla, não sinônimo de Mamba. Fonte: [S4, Gu, Goel e Ré](https://arxiv.org/html/2111.00396v3).

No Mamba-1, B, C e o passo de discretização Delta dependem da entrada transformada, enquanto A é um parâmetro aprendido compartilhado ao longo da sequência. A transição discreta também depende de Delta. As funções que calculam esses valores têm pesos treinados; na inferência elas adaptam o processamento à entrada sem atualizar os pesos por gradiente. Delta é um controle interno aprendido, não a duração física do candle. A seletividade não conhece antecipadamente quais movimentos terão valor econômico.

A estrutura afim da recorrência permite compor trechos: para `h_1=a_1*h_0+b_1` e `h_2=a_2*h_1+b_2`, resulta `h_2=(a_2*a_1)*h_0+(a_2*b_1+b_2)`. Essa composição é associativa e fundamenta um scan paralelo. Paralelizar o cálculo não torna o modelo não causal. O treinamento ainda precisa de atualizações sucessivas do otimizador. Fonte: [Mamba, Gu e Dao](https://arxiv.org/html/2312.00752v2).

## O bloco e a previsão

O núcleo oficial combina projeção da entrada, convolução causal curta, ativação, SSM seletivo, uma porta multiplicativa e projeção de saída. A rede completa pode empilhar blocos com residuais e normalização. No nosso projeto, cada retorno horário é projetado para 32 dimensões; os dois blocos processam as horas do contexto e uma cabeça linear lê o último instante para prever um escalar. Fonte: [implementação versionada](https://github.com/state-spaces/mamba/blob/v2.2.6.post3/mamba_ssm/modules/mamba_simple.py) e `previsao24/redes.py`.

O aprendizado compara esse escalar com o retorno real futuro, calcula a perda e ajusta os pesos por gradientes. O estado interno muda ao ler cada entrada; os pesos mudam durante o treinamento. Não confundir os dois mecanismos. Nosso pipeline reapresenta cada janela com estado novo, sem manter memória ilimitada entre origens.

Contexto, largura e dimensão de estado são diferentes. W336 são 336 retornos observados; largura32 é a representação interna de cada passo; expansão2 resulta em 64 canais internos; estado16 são 16 componentes por canal do SSM, não somente 16 candles de memória. Cada bloco tem 64×16 componentes de estado SSM por exemplo, além do estado da convolução, sem que isso equivalha a 1.024 observações armazenadas literalmente.

## Vantagens e limites para este TCC

Para dimensões fixas, Mamba oferece custo linear no comprimento da sequência e scan adequado à GPU. Na inferência recorrente, pode conservar estado de tamanho fixo, em vez de um histórico crescente. LSTM também tem custo linear e estado fixo; a vantagem teórica não é que LSTM seja quadrática. Sua transição depende não linearmente do estado anterior, diferente da composição afim usada no scan Mamba. A atenção densa convencional do Transformer compara posições e tem custo quadrático no comprimento; implementações eficientes podem reduzir materialização de memória sem eliminar todas essas operações.

Isso não estabelece velocidade real superior em janelas de 24–336 elementos ou em nossa GPU. Também não torna a memória sem perdas: estados de dimensão finita comprimem o passado e podem descartar detalhes. A seleção pode aprender correlações espúrias. Mais capacidade, contexto ou variáveis podem ajudar ou ampliar sobreajuste. A avaliação deve separar qualidade preditiva, custo computacional e resultado econômico.

Sob erro quadrático, para uma informação disponível X, `E[(Y-p)^2|X] = Var(Y|X) + (E[Y|X]-p)^2`. Assim, se a média condicional do retorno é próxima de zero, prever zero pode ser difícil de superar, mesmo com grande variância dos retornos. Uma rede não obtém informação que não existe nas entradas. A fórmula não prova que o mercado seja imprevisível; explica por que o Naive é uma referência relevante para nosso alvo.

## Decisões do CryptoMamba: fatos e interpretações

Artigo consultado: [Sepehri et al., versão 2](https://arxiv.org/html/2501.01010v2), ICBC 2025. Código consultado: commit `fef42727861a9c3a32241283ab981ef21a49e291`. A coluna de interpretação abaixo apresenta **hipóteses nossas sobre a função das escolhas**, salvo justificativa explicitamente indicada. O artigo não apresenta uma ablação que demonstre o ótimo de cada hiperparâmetro.

| Escolha observada | Função ou motivo plausível | Limite |
|---|---|---|
| Bitcoin, dados diários de Yahoo Finance | Série pública e experimento manejável | Não demonstra generalização para nossas quatro moedas ou Binance |
| Contexto de 14 dias | Capturar comportamento recente, com custo baixo | Não demonstra que duas semanas sejam melhores que 1/3/7 dias |
| Open/Close | Disponibilizar nível e deslocamento do preço | Correlação entre preços sucessivos pode favorecer persistência; nível não é retorno |
| High/Low | Disponibilizar amplitude intradiária e extremos | Não informa a ordem dos eventos dentro do candle |
| Volume | Informar intensidade de negociação | Há comparação com/sem volume, mas ela não isola perfeitamente a feature porque outros hiperparâmetros também diferem |
| Timestamp bruto | Pode permitir dependência de calendário ou tendência | Não é codificação explícita de dia da semana; pode induzir dependência frágil da data |
| Close do dia seguinte | Alvo escalar simples em unidades monetárias | Não prevê trajetória, probabilidade calibrada ou barreiras |
| Três estágios, quatro blocos cada, estado64 | Capacidade para transformar e combinar representações | Mais capacidade não implica melhor generalização; 64 não é um contexto de 64 dias |
| Dimensões14→16→32→1 | Transformar a janela até uma saída por variável | Eixos diferentes do nosso modelo temporal; números não são diretamente intercambiáveis |
| Pré-LayerNorm e residual | Condicionar a escala recebida pelo mixer e preservar caminho de informação | Não é equivalente a StandardScaler; não garante vantagem de previsão |
| RMSE, Adam, StepLR | Penalizar erros grandes e diminuir o passo de atualização ao longo do treino | Não é nossa perda escalada/AdamW; copiar learning rate isoladamente não reproduz o procedimento |

Entradas conferidas em [DataTransform](https://github.com/MShahabSepehri/CryptoMamba/blob/fef42727861a9c3a32241283ab981ef21a49e291/data_utils/data_transforms.py); arquitetura em [CMamba](https://github.com/MShahabSepehri/CryptoMamba/blob/fef42727861a9c3a32241283ab981ef21a49e291/models/cmamba.py). O tensor de um exemplo tem forma `[variáveis, 14 dias]`. A classe Mamba interpreta a primeira dessas dimensões como sequência: o scan percorre variáveis. No nosso caso, a sequência são horas. A leitura das formas é uma inspeção do código, não validação experimental das justificativas dos autores.

Os YAMLs usam Adam lr0,01, StepLR a cada100 épocas com fator0,5, batch padrão32; sem volume: máximo1.100 épocas e penalização0,0005; com volume:1.000 e0,001. O campo `normalize: False` desliga a normalização externa da implementação, mas não as LayerNorm internas. A transformação divide volume por1e9. São escolhas concretas do repositório, sem comprovação de que sejam ótimas. [Configuração com volume](https://github.com/MShahabSepehri/CryptoMamba/blob/fef42727861a9c3a32241283ab981ef21a49e291/configs/training/cmamba_v.yaml), [sem volume](https://github.com/MShahabSepehri/CryptoMamba/blob/fef42727861a9c3a32241283ab981ef21a49e291/configs/training/cmamba_nv.yaml).

A pesquisa anterior já documentou que o artigo menciona early stopping, mas o script público consultado mostra seleção de checkpoint sem callback de parada por paciência. Também documentou que a normalização opcional juntaria extremos das três partições se ativada; ela está desligada nos YAMLs CryptoMamba examinados. Esses achados não demonstram que as execuções do artigo tenham usado esse caminho ou que sejam inválidas.

## Resultados publicados e conferência adicional

Valores de preço, não retorno; menor é melhor. Fonte das quatro linhas neurais: tabela3 do artigo/README dos autores.

| Modelo | RMSE (USD) | MAE (USD) | MAPE (%) |
|---|---:|---:|---:|
| LSTM sem volume | 2.672,70 | 2.094,30 | 3,609 |
| CryptoMamba sem volume | 1.713,00 | 1.200,90 | 2,171 |
| LSTM com volume | 2.202,10 | 1.668,90 | 2,896 |
| CryptoMamba com volume | 1.598,10 | 1.120,70 | 2,034 |

A redução de RMSE é35,91% frente à LSTM sem volume e27,43% com volume. Comparando variantes CryptoMamba, a redução é6,71%; não atribuir tudo ao volume, porque época máxima e penalização também variam nos YAMLs. MAE é o erro absoluto médio; RMSE dá maior peso a erros grandes; MAPE é o erro absoluto relativo médio. MAPE2,034% não significa97,966% de acerto de direção e não é probabilidade de lucro. Não foram recalculadas previsões neurais nesta revisão.

**Conferência independente de persistência:** a tabela do artigo não inclui Naive. Baixamos o `test.csv` público do mesmo commit:365 linhas. O dataset publicado define `len=N-W-1`; para W14, isso produz350 exemplos, com alvo nas linhas14 a363 e informação até a linha anterior. Nessa população, a previsão `Close[t+1]=Close[t]` resulta em:

- RMSE **US$1.568,50**;
- MAE **US$1.091,90**;
- MAPE **1,97323%**.

São valores numericamente menores que os publicados para CryptoMamba com volume. A conferência é posterior, sem carregar checkpoints externos e sem certificar igualdade entre nossos350 exemplos e a população efetivamente usada para gerar a tabela do artigo. **Não é uma reprodução pareada nem prova de superioridade estatística do Naive sobre o modelo dos autores.** É evidência concreta de que a vitória sobre as redes publicadas não demonstra vantagem sobre persistência. Precisão float32/float64 produz diferença desprezível; uma segunda conta usando apenas CSV/math confirmou o RMSE float64. Usar todos os364 pares diários dá RMSE1.539,69, mas esse não é o recorte principal.

Evidências: [escopo registrado](../registros/revisoes/fundamentos_mamba_2026-10-28T151138.942559Z/escopo.json), [dados/fontes](../registros/revisoes/fundamentos_mamba_2026-10-28T151138.942559Z/fontes.json), [métricas](../registros/revisoes/fundamentos_mamba_2026-10-28T151138.942559Z/persistencia.json), [segunda conferência](../registros/revisoes/fundamentos_mamba_2026-10-28T151138.942559Z/verificacao.json). Código de cálculo e previsões Naive por origem estão na mesma pasta.

## Operação no artigo

O artigo relata que100 dólares iniciais chegaram a246,58 no Vanilla,213,20 no Smart e262,78 no Extended Smart para CryptoMamba com volume. Isso representa ganho simulado de146,58%,113,20% e162,78%, respectivamente, não acurácia. Não reproduzimos esses valores.

Na [rotina pública de operação](https://github.com/MShahabSepehri/CryptoMamba/blob/fef42727861a9c3a32241283ab981ef21a49e291/utils/trade.py), as compras/vendas não descontam taxa ou slippage explicitamente. O limiar de1% evita operações pequenas, mas não substitui cobrar custos das operações realizadas. As transações usam o preço de fechamento empregado na decisão, uma idealização de execução. O short não modela integralmente funding, margem ou liquidação. Portanto, não equiparar esses resultados a uma simulação executável de futuros ou à política Spot com custos do nosso projeto.

O parâmetro de risco de2% define uma faixa heurística ao redor da previsão e uma regra de tamanho de posição. Um erro médio percentual não fornece intervalo de previsão com cobertura probabilística conhecida, nem equivale ao nosso estudo histórico de barreiras. Uma previsão pontual e uma regra de operação são componentes distintos.

## Uso na fundamentação e no próximo ciclo

Foram localizadas referências a CryptoMamba na documentação técnica e no roteiro de redação. A busca local não localizou um capítulo final de fundamentação ou arquivo bibliográfico editável que permita confirmar a citação no texto acadêmico. Isso não demonstra ausência da referência em documento externo.

Usar três níveis na redação: SSM como formalismo, Mamba como arquitetura seletiva eficiente e CryptoMamba como aplicação empírica específica. Separar potencial de memória, resultados publicados e evidência de utilidade financeira. A crítica deve preservar tanto os resultados positivos relatados quanto os limites de comparadores, reprodução e simulação.

Concluir primeiro o ciclo de pré-normalização já autorizado e congelado. Não misturar novas features ou hiperparâmetros nesse ciclo. Depois, uma opção de extensão é **acrescentar somente volume transformado causalmente**, em um estudo com as mesmas populações, scalers apenas de treino e comparadores; forma, janela e normalização devem ser definidas antes da execução. É proposta futura, não autorização, e o artigo não isola perfeitamente o efeito dessa variável. Acrescentar OHLCV inteiro, trocar alvo para preço e adotar toda a arquitetura externa de uma vez impediria identificar a causa de uma eventual melhora.

A comparação com CryptoMamba não muda a validade do Naive no TCC; reforça sua importância. O estudo deve explicar se uma arquitetura acrescenta informação útil à persistência sob um protocolo claro, inclusive quando a resposta for negativa.
