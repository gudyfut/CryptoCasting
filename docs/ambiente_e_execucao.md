# Ambiente e execução

Guia técnico de trabalho. Os comandos não autorizam experimentos; consultar o [plano](../plano.md), as [diretrizes](diretrizes_pesquisa.md) e o [procedimento de pesquisa](registro_de_experimentos.md) para o escopo da tarefa. Protocolos e implementações congelados conservam os requisitos próprios.

## Localização e responsabilidades

O [README](../README.md#estrutura) apresenta as pastas principais. Dentro de `codigo/`:

| Camada | Responsabilidade e referência |
|---|---|
| `mercado_binance/`, `mercado_futuros/` | Coleta, proveniência e validação de observações; [dados](arquitetura_dados.md) |
| `entradas_modelo/` | Canais causais, alvos, contexto, divisões, purga e escalas; mudar entrada não exige recoleta automaticamente |
| `modelos/` | Arquiteturas e contratos; dimensões derivam das entradas; [modelos](arquitetura_modelos.md) |
| `treinamento/`, `avaliacao/` | Ajustes, seleção, checkpoints e métricas; [treinamento](arquitetura_treinamento.md) |
| `simulacao_operacoes/` | Sinais, política e contabilidade separados; [operações](arquitetura_operacoes.md) |
| `experimentos/`, `analises/` | Ciclos identificados e leituras posteriores; [análises](../codigo/analises/README.md) |
| `infraestrutura/`, `qualificacao/`, `manutencao/`, `comandos/` | Artefatos/caminhos, auxiliares sintéticos, auditoria e entrada dos comandos |

`estudo_ohlcv/` e `experimento_cryptomamba/` conservam dependências de compatibilidade. Não fundir versões científicas nem restaurar todo o legado na área de trabalho. Mercado, preparação de entradas e decisão operacional têm responsabilidades diferentes; preços/alvos futuros observados não entram na decisão.

As arquiteturas descrevem implementações e referências identificadas; consultá-las antes de alterar a camada. Contratos antigos não restringem novas perguntas científicas, mas uma alteração deve ter seu alcance e sua identidade explícitos.

## Python e comandos

Usar o ambiente já instalado e qualificado. No Windows, preferir `.venv/Scripts/python.exe`; no WSL/CUDA, o Python do ambiente científico daquela máquina. São ambientes distintos. Não reinstalar ou atualizar CUDA/PyTorch por rotina. `requirements.txt` conserva as dependências de referência.

A instalação editável registra os namespaces existentes a partir de `codigo/`. Executar na raiz, no ambiente escolhido:

```sh
python -m pip install --no-deps --no-build-isolation -e .
python -B -m comandos.dados --help
python -B -m comandos.modelos --help
python -B -m comandos.treinamento --help
```

Obter caminhos por `infraestrutura.caminhos.RAIZ`, `CODIGO` e `TESTES`, sem depender do diretório corrente ou de uma quantidade fixa de pais. Novas assinaturas incluem os caminhos reais e as dependências efetivas. Auxiliares sintéticos compartilhados ficam em `codigo/qualificacao/`; produção não importa suítes de testes.

## Antes de executar ou retomar

- Conferir identidade, escopo, orçamento e autorização do ciclo. Tetos não são metas de consumo; a autorização já dada não precisa ser repetida.
- Verificar host, PID Linux/Windows, boot, GPU, locks, logs e progresso. Timeout, arquivo de PID remoto ou documentação não provam encerramento. Não duplicar processo vivo nem retomar automaticamente uma falha.
- Qualificar o que a mudança afetar: contratos/dimensões, forward/backward, atualização, reprodução e recarga, antes de treino de mercado. Controles reais exigidos pelo protocolo precedem a grade; conservar época, retorno e demais condições exatas quando exigidas.
- Reproduções das identidades Mamba-1 deste acervo exigem a implementação oficial, CUDA e scan de referência previsto, sem fallback ou fused silencioso. Uma proposta de implementação diferente deve ser declarada e qualificada sob outra identidade.
- Fontes reorganizadas não substituem fontes congeladas. Recuperar executor encerrado em área isolada com layout e ambiente originais, conforme [preservação](armazenamento_e_reproducao.md); não chamá-lo para regenerar relatórios. Leituras posteriores têm identidade e recibo próprios.

Não iniciar treino para compensar arquivos ausentes em outra máquina. Recursos pagos, conta de negociação, alavancagem real e ordens não estão autorizados por tarefas de pesquisa ou simulação.

## Verificação proporcional à mudança

Na raiz, com o Python escolhido:

```sh
python -B -m unittest discover -s testes -t . -v
python -B -m unittest discover -s testes/dados -t . -v
python -B -m manutencao.arquivo_fontes conferir
python -B -m manutencao.auditar_repositorio --integridade --exigir-completo
```

O segundo comando exemplifica uma suíte por camada; não é necessário repetir tudo depois de cada edição textual. Testes CUDA/locks Linux exigem WSL qualificado: omissão ou indisponibilidade não certifica essa parte. Não afrouxar asserções ou iniciar treino de mercado para validar manutenção. Auditorias delimitam sua cobertura; ver [armazenamento](armazenamento_e_reproducao.md).

Em `dataview/`, executar npm nessa pasta:

```sh
npm test
npm run lint
npm run build
node --test tests/panorama.integration.mjs tests/api.integration.mjs
```

Os testes de integração exigem servidor ativo conforme o [README da interface](../dataview/README.md). Conferir navegação e apresentação quando alteradas. Para documentação, verificar links, coerência das instruções e preservação dos originais pertinentes; não executar uma grade científica como teste de edição.

Na entrega, informar o que foi conferido, falhas, skips e limitações do ambiente. Distinguir teste de código, equivalência numérica, auditoria de artefatos e evidência científica: uma dessas verificações não substitui as outras.
