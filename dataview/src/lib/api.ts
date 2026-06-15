import type {
  OHLCVCandle,
  FeatureRecord,
  PredictionResult,
  TrainingMetrics,
  ModelComparison,
  DatasetInfo,
  Par,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI<T>(endpoint: string): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`);
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function getOHLCV(par: Par): Promise<OHLCVCandle[]> {
  return fetchAPI<OHLCVCandle[]>(`/data/ohlcv/${par}`);
}

export async function getFeatures(par: Par): Promise<FeatureRecord[]> {
  return fetchAPI<FeatureRecord[]>(`/data/features/${par}`);
}

export async function getPredictions(par: Par): Promise<PredictionResult[]> {
  return fetchAPI<PredictionResult[]>(`/predictions/${par}`);
}

export async function getTrainingMetrics(): Promise<TrainingMetrics[]> {
  return fetchAPI<TrainingMetrics[]>("/training/metrics");
}

export async function getModelComparison(par: Par): Promise<ModelComparison> {
  return fetchAPI<ModelComparison>(`/comparison/${par}`);
}

export async function getDatasetInfo(par: Par): Promise<DatasetInfo> {
  return fetchAPI<DatasetInfo>(`/dataset/${par}`);
}
