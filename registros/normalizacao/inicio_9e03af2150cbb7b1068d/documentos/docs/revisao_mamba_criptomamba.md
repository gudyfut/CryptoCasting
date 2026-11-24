# Mamba utilizado, comparação com CryptoMamba e próximo teste proposto

Revisão de 27/10/2026, horário de São Paulo; recibos em 28/10 UTC. Solicitada depois dos resultados dos ciclos de referência e penalização. **Pesquisa e inspeção concluídas; alteração arquitetural apenas proposta, sem implementação ou novo treinamento.**

Atualização de 28/10/2026: a afirmação acima descreve o encerramento desta pesquisa, cuja versão foi preservada. Depois dela, o pesquisador autorizou implementar e executar a pré-normalização somente no Mamba. O método novo está no [protocolo próprio](protocolo_normalizacao_mamba.md); consultar [andamento](andamento.md) para o estado real. A penalização foi reconferida no mesmo commit atual dos autores: Adam uniforme no CryptoMamba, diferente do nosso AdamW com isenções. O ciclo novo mantém nossa política corrigida para isolar a normalização.

## Parecer

1. O núcleo usado é o **Mamba-1 seletivo oficial**, da biblioteca `mamba-ssm`, e não uma aproximação de LSTM com outro nome. O número `2.2.6.post3` identifica a versão do pacote, não a arquitetura Mamba-2.
2. A rede completa é uma **adaptação compacta para regressão**, com projeção, dois blocos Mamba, normalizações e cabeça escalar próprias. Não é reprodução do CryptoMamba nem a arquitetura completa de linguagem do repositório oficial.
3. A configuração é executável, qualificada e coerente com o contrato do estudo. Isso não significa que tenha sido otimizada para cripto. As fontes consultadas não estabelecem uma configuração universal que deva superar LSTM ou persistência.
4. Recomenda-se testar primeiro **a posição da LayerNorm em torno dos blocos**, passando de pós-normalização para pré-normalização, mantendo todo o restante igual ao Mamba com penalização corrigida. É hipótese fundamentada de adaptação, não correção de erro comprovado ou promessa de ganho.

O [registro da proposta](adr/0005-proposta-prenormalizacao-mamba.md) distingue recomendação de autorização. A [revisão de frequência](diagnostico_frequencia_e_configuracoes.md) continua válida: apenas avaliar diariamente não resolveu a desvantagem; treinar diariamente ainda não foi testado.

## Identidade do modelo: o que foi conferido

A inspeção no WSL importou `mamba_ssm.modules.mamba_simple.Mamba` e verificou PyTorch `2.6.0+cu118`, pacote `mamba-ssm 2.2.6.post3`, CUDA disponível e extensões compiladas `selective_scan_cuda`/`causal_conv1d_cuda`. O arquivo instalado `mamba_simple.py` coincide **byte a byte** com a fonte oficial da tag `v2.2.6.post3`. Seu SHA-256 é `a17e4c51b582dc0d4d690a649eba521cd0c1ee3dc8f0473a0967cdc9ec0874e3`, também igual ao registrado na qualificação anterior à extensão.

O módulo implementa projeções dependentes da entrada para B, C e o passo de discretização, convolução causal, mecanismo de seleção e scan do estado. É o núcleo SSM seletivo descrito pelos autores. A projeção do projeto produz tensores `[lote, horas de contexto, 32]`; o scan percorre as horas. A previsão usa a representação do último instante. Os pesos são aprendidos do zero por moeda/bloco/seed; não usamos um modelo pré-treinado em criptomoedas.

Esta revisão instanciou as redes em CPU apenas para contar e inspecionar atributos, sem forward ou treino. A execução CUDA, atualização, repetição e recarga continuam comprovadas pelos recibos anteriores: a preparação da penalização aprovou 12 casos de qualificação e a execução preservou auditorias por ajuste. Não apresentar esta leitura como nova repetição dos treinamentos.

Evidências: [inspeção da instalação](../registros/revisoes/mamba_criptomamba_2026-10-28T000408.161229Z/instalacao.json), [comparação com a qualificação](../registros/revisoes/mamba_criptomamba_2026-10-28T000408.161229Z/comparacao_qualificacao.json), [arquitetura local](../previsao24/redes.py), [fonte oficial versionada](https://github.com/state-spaces/mamba/blob/v2.2.6.post3/mamba_ssm/modules/mamba_simple.py).

## O que os parâmetros atuais significam

| Escolha | Valor atual | Interpretação e limite |
|---|---|---|
| Entrada | Um retorno horário | Não inclui OHLC, volume, notícias ou outras variáveis |
| `d_model` | 32 | Dimensão interna após projetar cada retorno; não é o contexto |
| `d_state` | 16 | Dimensão de estado por canal interno; não significa lembrar apenas 16 candles |
| `d_conv` | 4 | Extensão da convolução local; o SSM recebe o contexto completo |
| `expand` | 2 | Expande a largura interna para 64 |
| `dt_rank` | Automático, resultando em 2 | Parametrização do passo seletivo; defaults oficiais mantidos |
| Profundidade | Dois blocos | Rede compacta, não busca pela profundidade ideal |
| Dropout | 0,1 antes da normalização final | Não é aplicado no mesmo lugar do dropout entre camadas da LSTM |
| Capacidade | Mamba 20.129; LSTM 12.961 parâmetros | Mesma largura não significa mesma capacidade nem orçamento igual |
| Otimizador | AdamW, lr 0,0002 | Constante; sem scheduler e sem busca neural individual |
| Penalização corrigida | 0 para A_log/D; 0,001 nos demais | 2.176 escalares isentos e 17.953 penalizados |
| Atualizações | Batch 64, microbatch 32, clipping 1 | Acumulação conferida na auditoria anterior |
| Parada | Até 100 épocas, paciência 10 | Seleção pelo menor MSE de validação, não pelo teste |

`d_state=16`, `d_conv=4` e `expand=2` são defaults da classe oficial consultada. Largura, profundidade, head, dropout, normalização e treinamento são decisões do nosso projeto. Default de biblioteca é ponto de partida técnico, não evidência de otimização financeira. A classe não inclui automaticamente toda a rede de previsão ou toda a política de treinamento.

A inicialização especial de `dt_proj.bias` não foi sobrescrita por inicialização genérica. A penalização indevida de A_log/D no primeiro ciclo foi isolada e corrigida em ciclo separado, com efeito pequeno e inconclusivo em 2024–2025. Esse achado não justifica atribuir todo o resultado ruim a um defeito de implementação. O diagnóstico anterior também encontrou aprendizagem no treino acompanhada frequentemente de piora na validação, compatível com sobreajuste; não observou encerramento pelo teto de 100 épocas nos ajustes da avaliação. Aumentar épocas ou capacidade não tem benefício demonstrado.

Não foi feita busca individual de hiperparâmetros com orçamento equivalente para Mamba e LSTM. Portanto, a conclusão é sobre **estas configurações e este procedimento**, não sobre o melhor desempenho possível de cada família.

## O que realmente é o CryptoMamba

O trabalho encontrado é *CryptoMamba: Leveraging State Space Models for Accurate Bitcoin Price Prediction*, de Sepehri, Mehradfar, Soltanolkotabi e Avestimehr. Foram consultados o [artigo v2](https://arxiv.org/html/2501.01010v2) e o [repositório dos autores](https://github.com/MShahabSepehri/CryptoMamba), fixado no commit `fef42727861a9c3a32241283ab981ef21a49e291` (27/05/2025). Dezessete arquivos de código/configuração/README/licença foram preservados com URLs e hashes. Não executamos esse código, não carregamos seus checkpoints e não reproduzimos seus números.

| Aspecto | CryptoCasting atual | CryptoMamba consultado |
|---|---|---|
| Mercado e fonte | Quatro pares USDT, Binance Spot | Bitcoin em USD, Yahoo Finance |
| Resolução / contexto | 1h; 1/3/7/14 dias | Diário; 14 dias |
| Entrada | Retornos horários | Timestamp e OHLC, com/sem volume |
| Alvo / perda | Log-retorno em 24h / MSE padronizado no treino | Close do dia seguinte / RMSE |
| Arquitetura | Dois blocos, largura 32, estado 16 | Três estágios de quatro blocos, dimensões 14→16→32→1, estado 64 |
| Normalização do bloco | Depois do residual e Mamba | Antes do Mamba, com residual |
| Treinamento publicado no código | AdamW 0,0002 constante; batch 64 | Adam 0,01; StepLR a cada 100 épocas, fator 0,5; batch padrão 32 |
| Repetições / comparação | Três seeds, quatro blocos por fase, Naive explícito | Seed padrão 23 no script; tabela do artigo sem Naive |

Os valores de treinamento acima vêm dos [YAMLs e scripts do commit consultado](https://github.com/MShahabSepehri/CryptoMamba/tree/fef42727861a9c3a32241283ab981ef21a49e291/configs/training), não de uma garantia de que reproduzem todos os resultados publicados. As configurações indicam 1.100 épocas/weight decay 0,0005 sem volume e 1.000/0,001 com volume. Adam com penalização e AdamW desacoplado não são intercambiáveis; comparar apenas o número de learning rate ou weight decay ignora diferenças de perda, escala e arquitetura.

Há uma diferença particularmente relevante na implementação: `DataTransform` constrói `[variáveis, 14 dias]`, e o Mamba espera `[lote, sequência, dimensão]`. No código consultado, portanto, o scan percorre **as variáveis**, enquanto a janela de dias ocupa a dimensão transformada pelos estágios. Isso é inferência direta das formas e operações do código, não uma reprodução numérica. Nosso scan percorre o tempo. Copiar `d_state=64` não nos transforma em CryptoMamba. A rede externa inclui uma cópia da classe Mamba e usa suas operações CUDA, enquanto nós importamos a classe do pacote oficial.

O artigo relata vantagem de CryptoMamba sobre os comparadores neurais apresentados. Entretanto, sua tabela preditiva não apresenta persistência/Naive. Não permite concluir que esse desenho supera o nosso comparador mais difícil. Preço em dólares e retorno logarítmico são objetivos distintos: um erro em nível depende também da escala do preço, e MAPE de preço não pode ser comparado ao nosso MSE. Também não significa a mesma utilidade econômica.

### Cuidados ao usar o repositório como referência

- O artigo afirma early stopping; o `scripts/training.py` consultado configura checkpoint pelo menor `val/rmse` quando solicitado, mas não registra callback de early stopping. Selecionar o melhor checkpoint e interromper por paciência são operações distintas. A execução exata usada pelos autores não foi reconstruída.
- As configurações CryptoMamba têm `normalize: False`. A rotina opcional `normalize()` de `data_module.py`, se ativada como está, calcula extremos conjuntamente em treino/validação/teste. Isso seria vazamento se importássemos essa opção. **Não é evidência de vazamento na variante CryptoMamba com a opção desligada**; não deve ser generalizado para invalidar o artigo.
- O otimizador mostrado passa todos os parâmetros para Adam; não reproduz automaticamente nossa política explícita de isenção de A_log/D. Não copiar essa parte e desfazer a correção já realizada.

Esses pontos reforçam a necessidade de citar artigo e commit separadamente. Uma reprodução do CryptoMamba seria outro estudo, com preparação, comparadores e verificação próprios; não é uma mudança de um único fator.

## Por que priorizar pré-normalização

No projeto atual, para cada bloco:

`saída = LayerNorm(entrada + Mamba(entrada))`

Na variante proposta:

`saída = entrada + Mamba(LayerNorm(entrada))`

A LayerNorm ajusta a escala da representação interna, dentro de cada exemplo/instante. Não é o StandardScaler ajustado no treino; esse scaler permanece igual. Pré-normalizar modifica o sinal recebido pelo bloco e o caminho pelo qual os gradientes se propagam, conservando o caminho residual antes da normalização final. É uma organização usada pelo [bloco oficial da versão instalada](https://github.com/state-spaces/mamba/blob/v2.2.6.post3/mamba_ssm/modules/block.py) e pelo [CMBlock do CryptoMamba](https://github.com/MShahabSepehri/CryptoMamba/blob/fef42727861a9c3a32241283ab981ef21a49e291/models/cmamba.py).

A proposta mantém os mesmos módulos, tensores e 20.129 parâmetros. Não muda LayerNorm para RMSNorm, epsilon, inicialização, dropout, head, biblioteca ou política de penalização. Também não reproduz todas as outras escolhas da arquitetura oficial. Pós-normalização é uma arquitetura possível; não foi demonstrado que ela esteja errada para este problema. Pré-normalização pode melhorar, piorar ou ser equivalente. Deve ser qualificada inclusive quanto à sensibilidade à magnitude de retornos projetados e aprendizagem de sinais sintéticos conhecidos; testes sintéticos não provam previsão financeira.

A prioridade é uma escolha metodológica: investigar uma diferença estrutural localizada e apoiada por duas referências, antes de aumentar capacidade ou alterar população. Reduzir as origens de treino para uma por dia também é legítimo, mas reduz aproximadamente 24 vezes os exemplos e atualizações por época; envolve um contraste de amostragem e orçamento mais difícil de interpretar. A presente revisão muda a prioridade sugerida, não os resultados ou a história da revisão anterior.

## Experimento seguinte, se adotado

Comparar pré-LayerNorm com o **Mamba pós-LayerNorm da extensão corrigida**, não com o Mamba original penalizado. Contraste principal: diferença pareada de MSE entre essas duas variantes. LSTM, Naive, ARIMA e Mamba original permanecem referências identificadas. Preservar dados, moedas, contextos, origem horária, horizonte 24h, scalers, folds/purga, seeds 17/42/2026, inicialização, orçamento, seleção por validação, bootstrap e política Spot.

O desenho comparável completo tem 192 novos ajustes no desenvolvimento e 192 na avaliação retrospectiva: 384 novos Mamba, sem retreinar referências inalteradas. Prever dois controles de reprodução da variante corrigida, com contextos curto/longo escolhidos antes da execução. A escolha concreta das células, tolerâncias de reprodução e qualificação deve constar do novo protocolo antes de iniciar; não selecionar controles pelo resultado. Pilotos pertencem à grade e não autorizam mudar parâmetros. Gates entre fases são técnicos, não condicionados a ganho: não omitir a avaliação prevista porque o desenvolvimento foi ruim.

Antes da execução, criar fontes/configuração/protocolo próprios, congelar identidade e comprovar que a única diferença científica é a posição da normalização. Conferir pesos iniciais pareados, ordem de dados, parâmetros/grupos, forward/backward, atualização, recarga e controles. Resultado principal agregado, efeitos por contexto/moeda/bloco e dispersão entre seeds; intervalos por blocos temporais. Relatar melhora estatística, magnitude e operação separadamente. A política Spot continua diária e sem futuros.

As mesmas regras de treino não garantem a mesma melhor época: se esta mudar por efeito da arquitetura, registrar como consequência do procedimento fixado. Não aumentar paciência ou learning rate para ajudar uma variante durante a comparação. Não há busca adicional prevista. Se não melhorar, encerrar e registrar o resultado negativo.

DB1–DB4 continuam desenvolvimento e B1–B4 são retrospectivos já consultados. Nenhum intervalo recalculado nos mesmos períodos corrige por completo a seleção de hipóteses entre ciclos. Uma confirmação nova exige período realmente não consultado e protocolo previamente fixado; ela não foi criada por esta revisão.

## Registro e limites da revisão

Fontes e recibos em [pasta da revisão](../registros/revisoes/mamba_criptomamba_2026-10-28T000408.161229Z/). O [fechamento](../registros/revisoes/mamba_criptomamba_2026-10-28T000408.161229Z/fechamento.json) verifica as fontes científicas locais lidas e preserva as versões documentais. A pesquisa não coletou dados, treinou redes, alterou previsões ou reexecutou auditoria integral de checkpoints. O estado anterior permanece sustentado pelos recibos próprios, em especial pela [auditoria de configuração](auditoria_configuracao_penalizacao.md) e pelo [diagnóstico posterior](diagnostico_frequencia_e_configuracoes.md).

Para o TCC: descrever o método como **regressor baseado no bloco Mamba-1 oficial**, explicitando a adaptação e a configuração. A evidência atual sustenta desempenho inferior desta configuração a LSTM e Naive nos períodos estudados; não demonstra inadequação de todos os SSMs para cripto. A comparação proposta testa uma hipótese de arquitetura específica, com possibilidade legítima de conclusão negativa.
