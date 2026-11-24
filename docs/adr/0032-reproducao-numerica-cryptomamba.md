# ADR0032 — Reinício técnico do CryptoMamba diário

Data: 05/11/2026. Autorizado pelo pesquisador neste chat investigar/corrigir reprodução e iniciar novamente treinos e testes, escolhendo continuidade ou reinício conforme evidência.

A execução `6de6464912e674da1540` encerrou por reprovação do controle real após dois ajustes de 1.000 épocas. A sonda posterior isolou divergências de gradientes no selective scan CUDA instalado, inclusive com lote1; a convolução isolada foi exata nos casos ensaiados. Isso não é evidência de dados diferentes ou uma busca por melhor métrica. Sondas não atualizam pesos nem consultam retornos do teste.

Decisão: reiniciar todas as seeds, sem herdar pesos/checkpoints. A correção troca explicitamente o caminho fused por forward não fundido do Mamba-1 oficial e `selective_scan_ref` oficial em tensores CUDA. A recorrência, arquitetura, pesos treináveis, Adam, perda, calendário, dados e política permanecem os da ADR0031. A execução passa a exigir determinismo estrito no PyTorch; pacotes instalados e fontes históricas não são modificados. É uma alteração de execução numérica, não prova de equivalência bit a bit com a trajetória antiga.

Não continuar a partir de pesos produzidos por um caminho diferente desde a primeira atualização. Os checkpoints antigos são de seleção e não incluem todo estado de Adam/scheduler/RNG para retomada exata. A tentativa reprovada permanece preservada por hash; a autorização para apagá-la é uma possibilidade concedida pelo usuário, não uma necessidade técnica.

Namespace novo: `experimentos/cryptomamba_reproducivel/`, `registros/cryptomamba_reproducivel/`. Escopo: três seeds42/17/2026 e controle42, 1.000 épocas cada, 70 carteiras; nenhuma alteração de hipóteses ou relaxamento de tolerâncias. Qualificar equivalência de saídas/gradientes, repetições exatas e treinamento artificial com recarga; controle real antes das outras seeds. Falha interrompe e é preservada. A referência original e esta reexecução são identificadas separadamente no catálogo.

Limite: reprodução verificada neste hardware/ambiente, não garantia de identidade entre GPUs/versões. O caminho de referência pode ser mais lento. Ver [protocolo da reexecução](../protocolo_cryptomamba_reproducivel.md).
