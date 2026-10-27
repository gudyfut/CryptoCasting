# Arquivo científico — estudo encerrado na reformulação de 20/10/2026

Este diretório preserva o projeto anterior como existia antes da migração. Não é o protocolo ativo e não deve ser importado pela aplicação nova.

## Onde encontrar

- Protocolo executado: `projeto/docs/protocolo_experimental.md`.
- Configurações: `projeto/configuracoes/`; ciclo 002 permaneceu proposto, não executado.
- Relatório completo: `projeto/historico/analises/ciclo_001_resultados.md`.
- Diagnóstico posterior: `projeto/historico/analises/diagnostico_previsoes_2026-10-19.md`.
- Dados brutos, processados e checkpoints: `projeto/dados/` (binários locais, fora do Git).
- Fontes científicas, testes e interface: estrutura original dentro de `projeto/`.
- Cronograma acadêmico original: `projeto/docs/Cronograma_Atividades_TCC2_Murilo_Monferrari.pdf`.

Ciclo concluído `4e232a796fcda0ea34c3`, dataset `9341610dbb329a858784`: 96 células, 192 ajustes neurais e 16 ajustes AR(1), desenvolvimento 2023/seed42. Resultados: não demonstraram superioridade de Mamba ou rentabilidade consistente. Preservar também resultados negativos e qualificações sintéticas, identificadas como tais.

## Integridade e reprodução

`manifesto_antes.json` contém caminhos relativos à antiga raiz, tamanhos e SHA-256 dos arquivos movimentados. `verificacao.json` registra a conferência integral depois da movimentação. `commit_origem.txt` e `estado_git.txt` identificam o ponto de partida. Não houve reescrita Git nem descarte de tentativas.

Para consultar fontes antigas, considerar `projeto/` como sua raiz original. Não executar CLIs antigas sobre a raiz nova. Os arquivos adicionais de infraestrutura web foram copiados para preservar a configuração de dependências. O manifesto histórico de cada ciclo continua dentro de seus artefatos.

**Esta preservação é local, no mesmo disco, e não é um backup externo.** Checkpoints e arquivos brutos não são protegidos por Git; copiar este diretório para outra mídia se for necessário backup contra falha de disco.
