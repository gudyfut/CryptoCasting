# CryptoCasting — retorno em 24 horas

Pesquisa de TCC sobre previsão do retorno de BTC, ETH, BNB e XRP com Mamba, LSTM, ARIMA e Naive. Entrada horária; contextos de 1, 3, 7 e 14 dias; alvo sempre 24 horas à frente.

Em 26/10/2026 foi autorizado um experimento controlado para corrigir o tratamento de `weight_decay` do Mamba. O estudo de referência permanece preservado. A extensão tem protocolo e identidade próprios, e não transforma os testes de 2024–2025, já consultados, em um novo holdout intocado.

A extensão `7868a4d847c1410fc681` terminou em 27/10/2026: 384 ajustes corrigidos e dois controles, com duas publicações e preservação dos 7.082 arquivos da referência. Em 2024–2025, a correção variou o MSE em +0,0505% frente ao Mamba original, com intervalo incluindo zero; permaneceu pior que LSTM e Naive. A mediana Spot continuou em −10,48% com custos base. O [relatório da extensão](docs/resultados_penalizacao_mamba.md) separa desenvolvimento, avaliação retrospectiva, incerteza, seeds e simulação, com figuras PNG/PDF e registros de conferência.

- [Protocolo da correção de penalização](docs/protocolo_penalizacao_mamba.md)
- [Revisão das configurações e estruturas](docs/auditoria_configuracao_penalizacao.md)
- [Roteiro e fontes para a redação do TCC](docs/roteiro_redacao_tcc.md)

O ponto de entrada usado na extensão foi `python run_penalizacao.py executar`, no ambiente WSL qualificado. O ciclo está concluído; não repetir o executor para regenerar relatórios ou recibos. A referência mantém seu próprio ponteiro, e a extensão usa `registros/penalizacao/execucao.json`. O estado está em `progresso.json` na pasta indicada. A interface web continua apresentando os resultados do ciclo original; a comparação da extensão está publicada na documentação e nos artefatos próprios, sem substituir os anteriores.

- [Plano e entregas](plano.md)
- [Decisões do trabalho — ADRs](docs/adr/README.md)
- [Mapa dos registros de treinamentos e testes](registros/README.md)
- [Catálogo dos estudos e suas relações](registros/catalogo_estudos.json)
- [Como registrar mudanças e novos experimentos](docs/registro_de_experimentos.md)
- [Preservação no GitHub e reprodução entre máquinas](docs/armazenamento_e_reproducao.md)
- [Protocolo experimental](docs/protocolo_experimental.md)
- [Estado real da execução](docs/andamento.md)
- [Resultados auditados do desenvolvimento de 2023](docs/resultados_desenvolvimento.md)
- [Resultados auditados da avaliação de 2024–2025](docs/resultados_avaliacao.md)
- [Critérios de aceite das oito entregas](docs/aceite_execucao.md)
- [Decisões de reformulação](docs/decisoes.md)
- [Arquivo do estudo anterior](arquivo/estudo_barreiras_2026-10-20/README.md)

As oito entregas computacionais do protocolo estão concluídas e verificadas: desenvolvimento de 2023 e avaliação predefinida de 2024–2025, com 768 ajustes neurais, 64 referências e 288 candidatos ARIMA. O portal apresenta 832 resultados em 384 séries reais. Aceite em `registros/interface/aceite_final.json`; integridade global em `registros/auditorias/1e7c5ed662fba55ddd25/fechamento.json`. Dataset: `d25f6a93a9900725f51e`. Execução: `1e7c5ed662fba55ddd25`. Cada fase tem interpretação própria. Resultados do arquivo não representam este protocolo.

Na avaliação, LSTM teve menor erro que Mamba, mas não demonstrou redução de erro frente ao Naive. Não houve melhoria geral com mais contexto nem rentabilidade consistente na simulação Spot. Esta conclusão computacional não substitui redação, defesa ou aprovação acadêmica.

## Ambiente

Execução científica em Linux/WSL, Python 3.12, PyTorch CUDA e Mamba oficial. Dependências gerais em `requirements.txt`; registro completo do ambiente em `registros/qualificacao/`. Não há fallback silencioso para uma implementação diferente de Mamba.

A interface Next.js fica em `dataview/`. Execute npm nesse diretório. `npm run dev` abre o portal local; `npm run build`, `npm run lint` e `npm test` verificam código e séries exportadas. Com o servidor ativo, `node --test tests/api.integration.mjs` também verifica os endpoints de publicação.

## Execução e reprodução

O ponto de entrada é `run_previsao.py`, sempre a partir da raiz do projeto e no ambiente científico qualificado. A ordem do protocolo é:

1. `python run_previsao.py coletar` e `python run_previsao.py preparar` para obter os arquivos oficiais e construir o dataset.
2. Qualificação CUDA e testes de contrato antes de qualquer treinamento de mercado; os recibos de ambiente, configuração e fontes fazem parte da identidade da execução.
3. Piloto real curto/longo, seguido de `python run_previsao.py executar --fase desenvolvimento`.
4. `python manutencao/consolidar_resultados.py --fase desenvolvimento` para consolidar e conferir a publicação completa. Não aceita uma fase parcial.
5. `python run_previsao.py congelar`, depois `python run_previsao.py executar --fase avaliacao`.
6. `python manutencao/consolidar_resultados.py --fase avaliacao` e `python manutencao/exportar_portal.py`.
7. Inspeção científica e visual final descrita em `docs/aceite_execucao.md`.

A sequência desta execução terminou; seu estado está em `registros/continuacao_protocolo.json`. Os comandos acima descrevem a reprodução do fluxo, não solicitam nova execução automática. A interrupção operacional e a retomada estão preservadas em `registros/incidentes/`. Conferir processo/handle antes de qualquer retomada futura, sem duplicar processos por timeout de observação.

Preservar fontes científicas e recibos congelados desta identidade mesmo depois da conclusão. Mudanças de método exigem novo ciclo e nova identidade; os períodos de avaliação agora consultados não voltam a ser confirmação intocada. Os testes suplementares de publicação (`python manutencao/testar_consolidacao.py`) usam dados temporários identificados como sintéticos e não alteram os recibos do treinamento.

Código, documentação, decisões e evidências leves devem ser versionados no Git. Checkpoints, previsões completas, dataset processado e portal devem ser preservados em pacotes por ciclo no GitHub Releases, com inventário e hashes, além de uma cópia de segurança independente. A publicação desses pacotes ainda está pendente; um clone ou pull não os transfere automaticamente. Consulte a [política de preservação](docs/armazenamento_e_reproducao.md) para o procedimento e as pendências de sincronização.
