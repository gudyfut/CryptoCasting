# Histórico de pesquisa do CryptoCasting

Registro versionado do andamento do TCC: tentativas, resultados favoráveis ou desfavoráveis, falhas, dúvidas, correções e decisões. **Um experimento pode entrar aqui mesmo estando incorreto ou inconclusivo.** Registrar não significa aprovar.

- [Linha do tempo das execuções](LINHA_DO_TEMPO.md)
- [Marcos e decisões do projeto](DECISOES.md)
- [Modelo de acompanhamento de um experimento](MODELO_ACOMPANHAMENTO.md)
- [Diagnóstico do piloto Mamba](analises/2026-10-13_diagnostico_mamba.md)

## Estrutura e preservação

```text
historico/
  LINHA_DO_TEMPO.md                 # índice gerado pelo exportador
  DECISOES.md                       # mudanças de desenho e marcos, com referências
  analises/                        # investigações posteriores, separadas das execuções
  experimentos/<nome_da_execucao>/
    README.md                      # identificação e resumo inicial
    registro.json                  # data conhecida, situação, configuração, contagens, hashes
    acompanhamento.md              # revisões cronológicas; não apagar conclusões anteriores
    originais/                     # cópias dos JSONs, protocolo e fontes existentes
    previsoes/                     # CSVs derivados dos parquets leves
```

O protocolo em `docs/protocolo_experimental.md` continua sendo a referência para novos experimentos. `docs/entregas/` contém a síntese acadêmica; este histórico preserva as evidências que sustentam ou contradizem essa síntese. O código em `experimentos/` executa os procedimentos; essa pasta não é o arquivo documental.

**No Git:** configurações, resumos completos com métricas por classe, históricos por época, previsões com origem e alvo, cópia do código/protocolo se ela já existia na execução, análises e inventário com SHA-256. Arquivos individuais acima de 5 MiB ficam somente no inventário, com motivo explícito.

**Em `dados/experimentos/` e backup próprio:** checkpoints, binários, logs e artefatos grandes. O histórico registra seus hashes e localização, mas **um clone do Git não recupera esses arquivos**. Preservar uma cópia externa da pasta original antes de removê-la; nenhum backup externo foi criado automaticamente. Dados brutos/processados continuam fora do Git.

## Registrar uma execução

Na raiz, após uma tentativa concluída ou falha:

```text
python run_registro.py --execucao dados/experimentos/pareado_ID --titulo "BTC 1d D1: piloto inicial" --situacao em_revisao --observacao "Conferir generalização e implementação antes de usar no TCC."
```

Substituir `pareado_ID` pelo diretório real. A CLI não treina e não procura o melhor resultado. Aceita o piloto AR(1) antigo, a execução pareada atual ou uma pasta incompleta com `estado.json`. Confere a auditoria do contrato pareado quando possível; falhas são documentadas, não ocultadas. Não promove automaticamente uma tentativa a válida.

O exportador recusa sobreposição. Se algo mudar depois, acrescentar uma entrada datada em `acompanhamento.md`, com o motivo e vínculo para outra execução. Uma nova execução deve ter sua própria identidade; manter tentativas anteriores mesmo que sejam invalidadas. Para corrigir metadados documentais, deixar explícito no diff/commit e no acompanhamento; nunca reescrever previsões como se fossem as originais.

## Duas classificações independentes

| Campo | Exemplos | Significado |
|---|---|---|
| Estado de execução | concluído, falhou, interrompido | O programa terminou ou não |
| Revisão científica/técnica | em revisão, exploratório, inconclusivo, invalidado, validado tecnicamente | O quanto podemos confiar e para que o registro pode ser usado |

`validado_tecnicamente` não significa superioridade preditiva, experimento final ou ausência de todo possível erro. Neste histórico, o piloto neural permanece **em revisão**, apesar de ter passado pelas auditorias de integridade, por limitações científicas e pela diferença de inicialização identificada no fallback.

## Informações obrigatórias para novos registros

1. Pergunta/hipótese, motivo do teste e o que foi alterado em relação ao anterior.
2. Data UTC de execução e responsável. Data de importação é outro campo. Não inferir execução pelo horário dos arquivos.
3. Dataset, origem, hashes, moedas, candles, janela, horizonte, features, scaler e exclusões.
4. Folds, intervalos, purga, quantidades e classes de treino/validação/avaliação.
5. Arquitetura, inicialização/backend, parâmetros, seed, otimizador, taxa, batch, épocas e regra de seleção.
6. Ambiente/versões, custo observado e artefatos. Assinalar medições ausentes.
7. Métricas por bloco e classe, matrizes de confusão, diferenças versus baselines, referência de 50% e PT separados.
8. Verificações, problemas, conclusões provisórias e próximos testes previstos **antes** de avaliar novos resultados.

As execuções históricas AR(1) não preservaram horário nem snapshot completo do ambiente/código. Essas lacunas permanecem explícitas; não serão preenchidas com o ambiente atual. As exclusões exploratórias solicitadas em setembro não são revertidas: registramos sua existência e limitação na cronologia, sem inventar resultados removidos.
