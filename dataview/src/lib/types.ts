export interface OHLCVCandle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface FeatureRecord extends OHLCVCandle {
  sma_7: number;
  sma_21: number;
  sma_50: number;
  rsi_14: number;
  macd: number;
  macd_signal: number;
  macd_hist: number;
  retorno_diario: number;
  retorno_acumulado: number;
  volatilidade_21: number;
  direcao: 0 | 1;
}

export interface PredictionResult {
  timestamp: string;
  predicted: 0 | 1;
  actual: 0 | 1;
  correct: boolean;
}

export interface TrainingMetrics {
  epoch: number;
  train_loss: number;
  val_loss: number;
  train_accuracy: number;
  val_accuracy: number;
}

export interface ModelComparison {
  mamba_accuracy: number;
  baseline_accuracy: number;
  mamba_precision: number;
  baseline_precision: number;
  mamba_recall: number;
  baseline_recall: number;
  mamba_f1: number;
  baseline_f1: number;
}

export interface DatasetInfo {
  par: string;
  treino: number;
  validacao: number;
  teste: number;
  total: number;
  janela: number;
  features: number;
}

export type Par = "BTCUSDT" | "ETHUSDT" | "SOLUSDT" | "BNBUSDT";

export const PARES: Par[] = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"];
