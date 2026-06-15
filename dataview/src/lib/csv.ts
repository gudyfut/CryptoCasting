import { promises as fs } from "fs";
import path from "path";

export interface OHLCVCandle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export type Timeframe = "5m" | "15m" | "1h" | "4h" | "1d";

export function parseCSV(content: string): OHLCVCandle[] {
  const lines = content.trim().split("\n");
  const candles: OHLCVCandle[] = [];
  for (let i = 1; i < lines.length; i++) {
    const cols = lines[i].split(",");
    if (cols.length < 6) continue;
    candles.push({
      timestamp: cols[0].trim(),
      open: parseFloat(cols[1]),
      high: parseFloat(cols[2]),
      low: parseFloat(cols[3]),
      close: parseFloat(cols[4]),
      volume: parseFloat(cols[5]),
    });
  }
  return candles;
}

export function getDataDir(): string {
  return path.resolve(process.cwd(), "..", "dados");
}

export async function readCSVFile(par: string): Promise<OHLCVCandle[]> {
  const filePath = path.join(getDataDir(), `${par}.csv`);
  const content = await fs.readFile(filePath, "utf-8");
  return parseCSV(content);
}

export async function listAvailablePairs(): Promise<string[]> {
  const dir = getDataDir();
  const files = await fs.readdir(dir);
  return files
    .filter((f) => f.endsWith(".csv"))
    .map((f) => f.replace(".csv", ""))
    .sort();
}

function getGroupKey(timestamp: string, tf: Timeframe): string {
  const d = new Date(timestamp);
  switch (tf) {
    case "5m":
      return timestamp;
    case "15m": {
      const m = Math.floor(d.getMinutes() / 15) * 15;
      return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")} ${String(d.getHours()).padStart(2, "0")}:${String(m).padStart(2, "0")}:00`;
    }
    case "1h":
      return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")} ${String(d.getHours()).padStart(2, "0")}:00:00`;
    case "4h": {
      const block = Math.floor(d.getHours() / 4) * 4;
      return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")} ${String(block).padStart(2, "0")}:00:00`;
    }
    case "1d":
      return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")} 00:00:00`;
  }
}

export function aggregateCandles(
  candles: OHLCVCandle[],
  timeframe: Timeframe
): OHLCVCandle[] {
  if (timeframe === "5m") return candles;

  const groups = new Map<string, OHLCVCandle[]>();
  for (const c of candles) {
    const key = getGroupKey(c.timestamp, timeframe);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(c);
  }

  const result: OHLCVCandle[] = [];
  for (const [key, group] of groups) {
    result.push({
      timestamp: key,
      open: group[0].open,
      high: Math.max(...group.map((c) => c.high)),
      low: Math.min(...group.map((c) => c.low)),
      close: group[group.length - 1].close,
      volume: group.reduce((s, c) => s + c.volume, 0),
    });
  }
  return result;
}
