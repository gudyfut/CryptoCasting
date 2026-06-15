export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const PARES = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"] as const;

export const SPLIT_COLORS = {
  train: "#3b82f6",
  validation: "#f59e0b",
  test: "#ef4444",
} as const;

export const DIRECTION_LABELS: Record<0 | 1, string> = {
  0: "Baixa",
  1: "Alta",
};

export const DIRECTION_COLORS: Record<0 | 1, string> = {
  0: "#ef4444",
  1: "#22c55e",
};
