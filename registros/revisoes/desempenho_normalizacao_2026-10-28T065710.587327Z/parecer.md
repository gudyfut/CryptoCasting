# Diagnóstico de duração e uso da GPU — pré-normalização

Consulta em 28/10/2026, sem alterações na execução congelada `9e03af2150cbb7b1068d`. O progresso no instante da coleta está em `resumo.json`; os tempos de 89 ajustes auditados estão em `tempos.json`.

Foram verificadas auditoria aprovada, recarga exata e presença de métricas de teste nos ajustes contabilizados. O processo PID425 foi identificado no NVIDIA-SMI como processo de computação CUDA, em RTX4050 Laptop GPU. A GPU foi amostrada 31 vezes durante aproximadamente 30 segundos: utilização média 34,97%, entre 24% e 44%; memória total ocupada observada 357MiB de 6141MiB. Isso não mede eficiência dos SMs nem representa a utilização de toda a execução. O maior pico de memória alocada pelo PyTorch nos 89 ajustes foi 118,53MiB; ele não inclui todo o custo do contexto/driver.

Na consulta seguinte, alimentação externa presente, plano Windows Equilibrado, GPU47°C e sem flags ativas de limitação térmica/potência. Contadores cumulativos do driver não foram interpretados como limitação atual. Não foi alterado plano de energia, potência ou configuração.

Medianas da rotina por contexto: W24=60,15s; W72=65,72s; W168=62,88s; W336=68,77s. A rotina inclui treino, validação, previsões, salvamento e recarga; não é tempo puro do kernel. A média de épocas ficou entre17,3 e19,6, com medianas de aproximadamente4s por época. Tempos ainda cobrem apenas DB1 e parte de DB2 e não são benchmark controlado entre contextos ou arquiteturas.

A grade contém 4 moedas ×4 contextos ×8 blocos ×3 seeds=384 ajustes independentes, além de dois controles. Os ajustes são executados um por vez. A estrutura paralela do selective scan opera dentro do cálculo de sequências/lotes, não paraleliza automaticamente ajustes independentes, épocas ou atualizações do otimizador.

O treinador move rede, séries, índices e alvos para CUDA, e a classe oficial tem caminho rápido habilitado. Há pontos explícitos de sincronização com CPU, incluindo checagem de finitude e conversão de perda para CPU em cada microbatch, além das transferências de previsões para cálculo de métricas. Redes pequenas, microbatch32 e sequências até336 passos podem deixar o custo fixo de Python/lançamento/sincronização relevante. A ocupação parcial e a diferença pequena de tempo entre contextos são compatíveis com essa hipótese; sem profiler, não quantificamos o gargalo nem prometemos speedup.

Não há evidência de treinamento silencioso em CPU nem de erro de normalização derivada deste diagnóstico. Também não há evidência de utilização máxima da GPU. Otimizações futuras devem ser medidas em benchmark separado e qualificadas com equivalência; aumentar batch, usar precisão mista ou executar múltiplos ajustes juntos não será introduzido no meio desta comparação congelada.

Fontes: código local congelado; implementação oficial https://github.com/state-spaces/mamba/blob/v2.2.6.post3/mamba_ssm/modules/mamba_simple.py ; artigo https://arxiv.org/abs/2312.00752 . Não existe neste diagnóstico comparação de velocidade Mamba versus LSTM em condições iguais.
