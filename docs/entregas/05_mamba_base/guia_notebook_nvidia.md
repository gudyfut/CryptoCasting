# Entrega 5 — piloto no notebook NVIDIA

**Preparado em 13/10/2026; execução CUDA ainda pendente.** Este roteiro qualifica o Mamba-1 oficial e o treinamento pareado em uma célula de desenvolvimento. O computador da revisão tem GPU AMD e PyTorch CPU: os testes locais não certificam os kernels NVIDIA. A compatibilidade será confirmada no notebook pela verificação anterior ao treino.

## 1. O que este teste vai responder

Verificar se o classificador Mamba base consegue receber as janelas corretas, propagar gradientes, treinar, escolher a época pela validação, salvar pesos e reproduzir suas previsões após recarga. A LSTM usa os mesmos dados e regras; o AR(1) fornece a referência estatística.

Uma BA baixa **não invalida automaticamente a implementação**. O aceite técnico depende da integridade do procedimento. Um piloto de BTC/D1 não responde se Mamba é superior em todas as moedas, períodos ou granularidades; isso pertence aos experimentos seguintes.

O piloto CPU anterior permanece preservado e em revisão. Aqui mudam backend, inicialização interna, kernels e ambiente. Uma eventual melhora **não poderá ser atribuída apenas à GPU**. O fallback não é reinicializado nem corrigido retrospectivamente nesta execução.

## 2. Configuração fechada do piloto

Arquivo: `configuracoes/treino_piloto_nvidia.json`.

| Item | Valor e significado |
|---|---|
| Ativo | BTCUSDT |
| Candle / passado de cada exemplo | 1 dia / 7 dias: tensor com 7 passos e 5 features |
| Entradas | Open, high, low, close, volume; StandardScaler ajustado em candles únicos do treino |
| Alvo | Alta (`retorno > 0`) versus não alta nas próximas 24h; sem excluir retornos pequenos |
| Fold | D1; treino anterior a outubro/2022, validação outubro–dezembro/2022, teste de desenvolvimento janeiro–março/2023, com purga e elegibilidade |
| Amostras esperadas no dataset oficial | 495 treino, 91 validação, 82 teste; 525 candles únicos no ajuste do scaler |
| Mamba | **Mamba-1 oficial**, largura 32, 2 camadas, estado 16, convolução 4, expansão 2, dropout 0,1, último passo |
| LSTM | Unidirecional, largura 32, 2 camadas, dropout 0,1, último passo |
| Inicialização | Pesos novos para cada rede, seed 42; preservar inicialização específica do Mamba oficial |
| Treino | AdamW, taxa 0,0002, weight decay 0,001, cross-entropy sem pesos, clipping 1 |
| Batch / microbatch | 32 / 32; apenas o treino embaralha exemplos |
| Seleção | Maior BA de validação; primeiro checkpoint em empate; até 100 épocas, paciência 10 |
| Precisão | Parâmetros float32, sem AMP; opções TF32/determinismo registradas, sem promessa de igualdade bit a bit entre máquinas |
| Decisão | Alta somente se `p(alta) > 0,5`; sem escolher limiar pelo teste |
| Quantidade | **Uma célula, dois treinos neurais** e um ajuste/reuso do AR(1) |

O treinador aplica weight decay global a todos os parâmetros das duas redes, conforme a regra implementada do projeto. As anotações internas `_no_weight_decay` do pacote Mamba não são interpretadas automaticamente pelo AdamW. Usar o bloco oficial não significa adotar a receita de treinamento de modelos de linguagem dos autores; não acrescentar grupos de otimização ou alterar inicialização para procurar uma BA melhor neste piloto.

**Não começar por `treino_desenvolvimento_wsl.json`:** esse arquivo contém 64 células e 128 treinos neurais. F1–F8 continuam bloqueados. O custo desta pequena janela diária não estima o custo de 672 passos em candles de 15 minutos.

## 3. Levar código e dados ao notebook

Copiar a versão atual completa do repositório, incluindo `run_verificacao.py`, `experimentos/qualificacao.py` e a configuração NVIDIA. Se usar Git no notebook, conferir que esses arquivos existem na revisão recebida; alterações locais ainda não publicadas não chegam por `git pull`.

Copiar também **a pasta inteira** `dados/processados/daeec76f001afb50a8fe/`, mantendo seu nome e estrutura. Ela é ignorada pelo Git: clonar o repositório não traz o dataset. Os hashes serão conferidos pelo leitor. Não é necessário coletar/processar novamente para este piloto e não se deve copiar apenas um parquet.

Em WSL, preferir uma pasta dentro do Linux, como `~/projetos/CryptoCasting`, e criar um ambiente Python Linux próprio. O ambiente virtual do Windows não pode ser reutilizado como ambiente Linux.

## 4. Preparar o ambiente

### Sistema e GPU

O caminho documentado é **Linux ou Ubuntu em WSL2**. No Windows, instalar/atualizar o driver NVIDIA no Windows e confirmar que `nvidia-smi` também funciona dentro do WSL. A NVIDIA orienta **não instalar um driver Linux de GPU dentro do WSL**; quando houver compilação, instalar apenas o CUDA Toolkit para WSL. Consulte o [guia oficial NVIDIA](https://docs.nvidia.com/cuda/wsl-user-guide/index.html).

```bash
nvidia-smi
nvcc --version
```

O primeiro identifica placa/driver; o segundo identifica o compilador. O campo “CUDA Version” do `nvidia-smi` não prova que o toolkit ou o PyTorch CUDA estejam instalados. O modelo exato da placa ainda precisa ser conferido; placas antigas podem exigir outra combinação. Uma combinação que instala sem erro ainda precisa passar no forward/backward.

### Combinação proposta para qualificação

Python **3.12**, PyTorch **2.9.1 com CUDA 12.8**, `mamba-ssm==2.2.6.post3` e `causal-conv1d==1.6.0`, com `transformers==4.51.3` como dependência auxiliar do pacote oficial. É uma combinação versionada para verificar no notebook, **ainda não validada neste projeto em GPU**. A distribuição CUDA 12.8 do PyTorch 2.9.1 consta na [documentação oficial](https://pytorch.org/get-started/previous-versions/). Fixar a versão do Mamba evita que uma atualização automática altere as dependências e a implementação usada.

Os comandos abaixo pressupõem Python 3.12 com `venv`, compilador C++ e **CUDA Toolkit 12.8** já disponíveis no Linux/WSL. A instalação das extensões é feita a partir das fontes para casar com o PyTorch instalado e não reaproveitar um wheel compilado para outra GPU/ABI. Pode demorar e consumir RAM. O [setup oficial do Mamba](https://github.com/state-spaces/mamba/blob/v2.2.6.post3/setup.py) inclui alvos Blackwell quando o compilador é CUDA 12.8 ou posterior; isso não substitui a verificação na placa real.

Na raiz do projeto, no terminal Linux/WSL:

```bash
python3.12 -m venv ~/.venvs/cryptocasting-nvidia
source ~/.venvs/cryptocasting-nvidia/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install torch==2.9.1 --index-url https://download.pytorch.org/whl/cu128
python -m pip install packaging ninja einops transformers==4.51.3
python -m pip install -r requirements.txt
export CUDA_HOME=/usr/local/cuda-12.8
export PATH="$CUDA_HOME/bin:$PATH"
export MAX_JOBS=2
CAUSAL_CONV1D_FORCE_BUILD=TRUE python -m pip install --no-build-isolation --no-cache-dir causal-conv1d==1.6.0
MAMBA_FORCE_BUILD=TRUE python -m pip install --no-build-isolation --no-cache-dir mamba-ssm==2.2.6.post3
python -m pip check
```

Se o toolkit estiver em outro caminho, ajustar `CUDA_HOME` ao local **real** do toolkit 12.8. Não apontar para uma pasta inexistente. O instalador antigo `scripts/setup_wsl_mamba.sh` foi preservado como receita histórica; ele contém wheels e alterações em `site-packages` de outro ambiente e não deve ser usado neste procedimento. Não editar o pacote instalado para ocultar erros de importação.

## 5. Verificar antes de treinar

```bash
python run_treino.py --configuracao configuracoes/treino_piloto_nvidia.json --planejar
python run_verificacao.py --configuracao configuracoes/treino_piloto_nvidia.json
```

O planejamento deve mostrar **uma célula, dois treinos neurais e avaliação final bloqueada**. A verificação deve terminar com `Verificação concluido: ...`. Se disser `falhou`, corrigir o ambiente/dados antes de iniciar o treino. O atalho `python scripts/test_mamba.py` executa essa mesma verificação.

A verificação não treina: lê os arquivos necessários, confere hashes/rótulos/folds, ajusta apenas o scaler do treino e executa forward, backward e inferência sobre dois exemplos sintéticos, **sem passo de otimizador**. Confere todos os gradientes e a inicialização `softplus(dt_bias)` padrão entre 0,001 e 0,1 das duas camadas oficiais. Não é prova formal de equivalência entre backends nem teste de memória do batch completo.

O relatório fica em `dados/experimentos/verificacao_<id>/resultado.json`, inclusive nas falhas, com `dependencias.txt`. Em caso de sucesso, registra ambiente, fontes instaladas, configuração, contagens e verificações. Guardar esse diretório junto do resultado do treino.

## 6. Executar o treino

Somente depois da verificação aprovada:

```bash
python run_treino.py --configuracao configuracoes/treino_piloto_nvidia.json
```

O treinamento também verifica os kernels antes de ajustar a LSTM, para não descobrir um erro básico de Mamba apenas depois do primeiro treino. Registra essa checagem em `qualificacao_modelos.json`. Cada rede é reinicializada com a seed definida após a checagem sintética.

Guardar o caminho `dados/experimentos/pareado_<id>` impresso. Os históricos mostram **loss de treino e BA de validação** a cada época. A avaliação de desenvolvimento é calculada após carregar o checkpoint escolhido pela validação. Não esperar obrigatoriamente 100 épocas: a parada antecipada é parte do protocolo.

Em falha/interrupção, preservar a pasta e o erro. `--nova-tentativa` reinicia em outra pasta, desde a primeira época; não retoma pesos parciais. Se faltar memória, primeiro encerrar outros processos CUDA; reduzir microbatch exige outra configuração registrada, mantendo batch efetivo 32. Não escolher entre tentativas pelo melhor teste.

## 7. Recarregar, auditar e guardar

Substituir `ID_REAL` pelo identificador impresso ao concluir. Usar o **mesmo ambiente e código** do treino:

```bash
python run_verificacao.py --execucao dados/experimentos/pareado_ID_REAL
python run_avaliacao.py --execucoes dados/experimentos/pareado_ID_REAL --saida dados/experimentos/resumo_nvidia_D1_01
python run_registro.py --execucao dados/experimentos/pareado_ID_REAL --titulo "Piloto NVIDIA Mamba oficial BTC 1d D1" --situacao em_revisao --observacao "Entrega 5: anexar caminhos dos relatórios de preparação e reprodução, hardware, conclusão técnica e limitações."
```

A reprodução confere os hashes e as métricas, reconstitui o scaler, verifica a primeira melhor época e a parada antecipada, carrega ambos os checkpoints e compara probabilidades com os parquets pelos timestamps. Aceita arredondamento de `atol=1e-6`, `rtol=1e-5`; as **classes devem ser idênticas**. Uma divergência interrompe o aceite, mesmo que a BA pareça boa. Não altera os arquivos da execução.

Registrar também os dois diretórios `verificacao_<id>` com `run_registro.py`, identificando-os no título como verificações técnicas sem treinamento. Usar inicialmente `em_revisao`; acrescentar a conclusão do exame em `acompanhamento.md`. O registro leve não faz backup dos pesos: copiar os diretórios completos das execuções, verificações e dataset para armazenamento seguro.

## 8. Aceite que corresponde à Entrega 5

- [ ] Preparação aprovada no notebook com backend oficial/CUDA, contagens corretas e gradientes finitos.
- [ ] Treino pareado concluído, sem trocar a configuração ou o backend silenciosamente.
- [ ] Dois checkpoints, históricos, scaler, código, protocolo, ambiente e seis parquets presentes.
- [ ] Reprodução dos checkpoints e auditoria aprovadas; épocas/seleção/purga conferidas.
- [ ] BA, F1 macro, recalls, confusão, comparação com AR(1)/LSTM/50% e PT interpretados separadamente.
- [ ] Duração e pico de memória registrados; resultado e falhas preservados no histórico.

Depois disso, o piloto oficial terá evidência de aceite técnico. As conclusões científicas da grade maior e os resultados finais permanecem pendentes. O próximo passo será medir o custo de uma janela intradiária e planejar a execução de E0 nos folds de desenvolvimento, mantendo o mesmo backend qualificado.

### Diagnóstico de falhas comuns

| Mensagem/sintoma | O que conferir |
|---|---|
| CUDA indisponível | Terminal Linux/WSL correto, ambiente ativado, driver NVIDIA e wheel CUDA do PyTorch |
| Manifesto ausente | Copiar o dataset completo; ele não vem pelo Git |
| `nvcc` ausente ou toolkit divergente | Instalar/localizar toolkit compatível, sem driver Linux dentro do WSL |
| `undefined symbol`, erro ao importar extensão | PyTorch/Python/ABI diferentes dos usados ao compilar; reconstruir extensões nesse ambiente |
| `no kernel image` / GPU não suportada | Conferir placa e arquitetura suportada pelo PyTorch/toolkit; não tratar isso como resultado do modelo |
| Compilação encerrada com `Killed` | Possível falta de RAM durante compilação; registrar erro e reduzir `MAX_JOBS` para 1 |
| Determinismo em modo aviso | Preservar o aviso; sementes não garantem igualdade bit a bit dos kernels CUDA |
| Reprodução divergente | Preservar arquivos e relatório; verificar código, ambiente e proximidade das probabilidades a 0,5 antes de aceitar |

Fontes técnicas adicionais: [Mamba oficial versionado](https://github.com/state-spaces/mamba/tree/v2.2.6.post3), [inicialização do Mamba-1](https://github.com/state-spaces/mamba/blob/v2.2.6.post3/mamba_ssm/modules/mamba_simple.py), [causal-conv1d versionado](https://github.com/Dao-AILab/causal-conv1d/tree/v1.6.0). A consulta às fontes sustenta o procedimento; o funcionamento no notebook só será confirmado pela execução registrada.
