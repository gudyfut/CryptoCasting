// Registro editorial do protocolo 1.6. Valores históricos citam as entregas;
// resultados novos são lidos separadamente pela API local.
export const moedas = [
  { sigla: "BTC", nome: "Bitcoin", papel: "Reserva e transferência de valor", rede: "Prova de trabalho", cor: "#b77836", volatilidade: 3.05, descricao: "Ativo nativo de uma rede de pagamentos, com emissão programada e oferta limitada. Referência para comparar o comportamento das demais moedas." },
  { sigla: "ETH", nome: "Ether", papel: "Contratos inteligentes", rede: "Prova de participação desde 2022", cor: "#6876a5", volatilidade: 4.13, descricao: "Ativo usado para taxas e validação da Ethereum. O período estudado inclui a transição de mecanismo de consenso em 2022." },
  { sigla: "BNB", nome: "BNB", papel: "Ecossistema BNB Chain", rede: "Rede e usos na Binance", cor: "#ab9140", volatilidade: 4.26, descricao: "Ativo nativo da BNB Chain, também usado em serviços da Binance. Essa ligação é relevante porque os preços de todos os pares vêm da mesma corretora." },
  { sigla: "XRP", nome: "XRP", papel: "Pagamentos e liquidação", rede: "Consenso entre validadores", cor: "#577970", volatilidade: 5.13, descricao: "Ativo nativo do XRP Ledger, voltado a pagamentos e liquidação. Oferece outro contexto de rede para a análise comparativa." },
];

export const entregas = [
  { numero: 1, titulo: "Protocolo experimental", prazo: "08–13 set", estado: "Documentada", tipo: "concluida", detalhe: "Versão 1.6: perguntas, duas baselines, métricas, população comum e folds temporais definidos.", documento: "protocolo" },
  { numero: 2, titulo: "Coleta e auditoria", prazo: "14–20 set", estado: "Executada", tipo: "concluida", detalhe: "240 arquivos mensais da Binance Spot. 216 completos e 24 com lacunas documentadas; checksums oficiais válidos.", documento: "coleta" },
  { numero: 3, titulo: "Dados e amostras", prazo: "21–27 set", estado: "Executada", tipo: "concluida", detalhe: "Dataset auditado com 1.661 origens diárias comuns, 67 arquivos e estudo de volatilidade. Lacunas preservadas.", documento: "dados" },
  { numero: 4, titulo: "Infraestrutura e baselines", prazo: "28 set–04 out", estado: "Validada no piloto CPU", tipo: "concluida", detalhe: "AR(1) BTC/D1–D4 executado. Piloto pareado BTC/1d/D1 concluído: LSTM treinada, métricas recalculadas e checkpoints auditados. A grade completa pertence às próximas entregas.", documento: "infraestrutura" },
  { numero: 5, titulo: "Mamba base", prazo: "05–11 out", estado: "CPU validada · CUDA pendente", tipo: "implementada", detalhe: "Mamba PyTorch treinado e auditado no piloto D1: BA 41,46%, época 4 selecionada na validação. Backend oficial não validado: máquina com GPU AMD e sem o ambiente CUDA previsto.", documento: "mamba" },
  { numero: 6, titulo: "Resolução e contexto", prazo: "12–18 out", estado: "Planejada", tipo: "planejada", detalhe: "Avaliar quatro resoluções, 7 e 14 dias de contexto e um horizonte comum de 24h, somente no desenvolvimento." },
  { numero: 7, titulo: "Representação das entradas", prazo: "19–25 out", estado: "Planejada", tipo: "planejada", detalhe: "Comparar OHLCV com OHLCV + três indicadores causais, aplicados igualmente a Mamba e LSTM." },
  { numero: 8, titulo: "Normalização e arquitetura", prazo: "26 out–01 nov", estado: "Planejada", tipo: "planejada", detalhe: "Comparar StandardScaler/MinMaxScaler e larguras 32/64. Congelar decisões usando apenas 2021–2023." },
  { numero: 9, titulo: "Robustez temporal", prazo: "02–08 nov", estado: "Planejada", tipo: "planejada", detalhe: "Após o congelamento: oito folds de 2024–2025, três seeds e resultados em todas as células previstas." },
  { numero: 10, titulo: "Análise científica", prazo: "09–15 nov", estado: "Planejada", tipo: "planejada", detalhe: "Comparar ganhos frente às duas baselines, distância de 50%, PT e estabilidade entre ativos e períodos." },
  { numero: 11, titulo: "Escrita e revisão", prazo: "16–22 nov", estado: "Planejada", tipo: "planejada", detalhe: "Consolidar metodologia, resultados, limitações, referências e conclusões sustentadas pelas evidências." },
  { numero: 12, titulo: "Apresentação e submissão", prazo: "23 nov", estado: "Planejada", tipo: "planejada", detalhe: "Preparar a versão final, apresentação e arquivos reproduzíveis do trabalho." },
] as const;

export const decisoes = [
  { titulo: "O que significa prever alta?", texto: "Alta é retorno futuro maior que zero. Baixa ou empate formam a classe não alta. Nenhuma observação é excluída por ter uma variação futura pequena." },
  { titulo: "Por que ARIMA e LSTM?", texto: "ARIMA(1,0,0) nos log-retornos é o AR(1) estatístico simples. A LSTM recebe as mesmas sequências e features do Mamba. São dois confrontos: superar um método simples e superar outra arquitetura sequencial." },
  { titulo: "Como impedir informação do futuro?", texto: "Treino, validação e teste seguem datas. O scaler aprende somente com candles únicos das janelas de treino. Rótulos que atravessam a fronteira do bloco são retirados. Validação e teste mantêm a ordem temporal." },
  { titulo: "O que pode ser escolhido no desenvolvimento?", texto: "Features, normalização e larguras usam somente D1–D4. Mamba e LSTM recebem as mesmas entradas; cada rede escolhe entre suas larguras 32 e 64. Contextos de 7 e 14 dias são reportados separadamente." },
  { titulo: "O que fica reservado para o final?", texto: "Os oito trimestres de 2024–2025. A execução final continua bloqueada nesta infraestrutura até a etapa de congelamento. Exposições a resultados antigos precisam ser declaradas antes de chamar esse período de intocado." },
  { titulo: "Mais acerto significa mais lucro?", texto: "O trabalho mede previsão direcional. Rentabilidade exigiria regras de execução, custos, slippage e gestão de risco. Esses elementos estão fora do escopo atual." },
];

export type ResultadoLocal = {
  pasta: string;
  id: string;
  par: string;
  granularidade: string;
  contexto: number;
  tarefa: string;
  fold: string;
  seed: number;
  features: string;
  normalizador: string;
  larguraMamba: number;
  larguraLstm: number;
  backend: string;
  dispositivo: string;
  codigo: string;
  amostras: number;
  ba: { mamba: number | null; lstm: number | null; ar1: number | null };
  diferencas: { mamba_menos_ar1: number | null; mamba_menos_lstm: number | null; mamba_menos_50: number | null };
};
export type RespostaResultados = { resultados: ResultadoLocal[]; avisos: string[]; atualizacao: string };
