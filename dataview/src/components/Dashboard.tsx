"use client";

import { useState, useEffect } from "react";
import CryptoChart from "./CryptoChart";
import type { Timeframe } from "@/lib/csv";

const TIMEFRAMES: { value: Timeframe; label: string }[] = [
  { value: "5m", label: "5 min" },
  { value: "15m", label: "15 min" },
  { value: "1h", label: "1 Hora" },
  { value: "4h", label: "4 Horas" },
  { value: "1d", label: "Diário" },
];

const PRIORITY_PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"];

interface ChartData {
  dates: string[];
  ohlc: number[][];
  volumes: number[];
  closes: number[];
  indicators: {
    sma7: (number | null)[];
    sma21: (number | null)[];
    sma50: (number | null)[];
    rsi14: (number | null)[];
    macd: (number | null)[];
    macdSignal: (number | null)[];
    macdHist: (number | null)[];
  };
}

interface Stats {
  start: string;
  end: string;
  firstPrice: number;
  lastPrice: number;
  priceChange: number;
  priceChangePercent: number;
  high: number;
  low: number;
  avgVolume: number;
}

export default function Dashboard() {
  const [pairs, setPairs] = useState<string[]>([]);
  const [selected, setSelected] = useState("BTCUSDT");
  const [timeframe, setTimeframe] = useState<Timeframe>("1h");
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/pairs")
      .then((r) => r.json())
      .then((d) => {
        const sorted = (d.pairs as string[]).sort((a, b) => {
          const ai = PRIORITY_PAIRS.indexOf(a);
          const bi = PRIORITY_PAIRS.indexOf(b);
          if (ai === -1 && bi === -1) return a.localeCompare(b);
          if (ai === -1) return 1;
          if (bi === -1) return -1;
          return ai - bi;
        });
        setPairs(sorted);
      });
  }, []);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`/api/chart-data/${selected}?tf=${timeframe}`);
        if (!res.ok) throw new Error("Erro ao carregar dados");
        const d = await res.json();
        if (cancelled) return;
        setChartData({
          dates: d.dates,
          ohlc: d.ohlc,
          volumes: d.volumes,
          closes: d.closes,
          indicators: d.indicators,
        });
        setStats(d.stats);
      } catch (e) {
        if (!cancelled) setError((e as Error).message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [selected, timeframe]);

  const formatPrice = (v: number) => {
    if (v >= 1000) return v.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    if (v >= 1) return v.toFixed(4);
    return v.toFixed(6);
  };

  const formatVolume = (v: number) => {
    if (v >= 1e6) return `${(v / 1e6).toFixed(2)}M`;
    if (v >= 1e3) return `${(v / 1e3).toFixed(1)}K`;
    return v.toFixed(2);
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="sticky top-0 z-50 border-b border-gray-800 bg-gray-950/95 backdrop-blur">
        <div className="mx-auto max-w-[1600px] px-4 py-3">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="h-2.5 w-2.5 rounded-full bg-blue-500" />
              <h1 className="text-lg font-bold tracking-tight">CryptoCasting</h1>
              <span className="text-sm text-gray-500">Dataview</span>
            </div>

            <div className="flex flex-wrap gap-1.5">
              {pairs.map((par) => (
                <button
                  key={par}
                  onClick={() => setSelected(par)}
                  className={`rounded-md px-3 py-1.5 text-sm font-medium transition-all ${
                    selected === par
                      ? "bg-blue-600 text-white shadow-lg shadow-blue-600/20"
                      : "bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-gray-200"
                  }`}
                >
                  {par.replace("USDT", "")}
                </button>
              ))}
            </div>

            <div className="flex gap-1">
              {TIMEFRAMES.map((tf) => (
                <button
                  key={tf.value}
                  onClick={() => setTimeframe(tf.value)}
                  className={`rounded px-2 py-1 text-xs font-medium transition-all ${
                    timeframe === tf.value
                      ? "bg-gray-700 text-white"
                      : "text-gray-500 hover:text-gray-300"
                  }`}
                >
                  {tf.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1600px] px-4 py-4">
        {stats && (
          <div className="mb-4 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
            <div>
              <span className="text-gray-500">Preço </span>
              <span className="text-lg font-semibold">${formatPrice(stats.lastPrice)}</span>
            </div>
            <div>
              <span
                className={`font-semibold ${
                  stats.priceChangePercent >= 0 ? "text-green-400" : "text-red-400"
                }`}
              >
                {stats.priceChangePercent >= 0 ? "+" : ""}
                {stats.priceChangePercent.toFixed(2)}%
              </span>
            </div>
            <div className="text-gray-500">
              Máx: <span className="text-gray-300">${formatPrice(stats.high)}</span>
            </div>
            <div className="text-gray-500">
              Mín: <span className="text-gray-300">${formatPrice(stats.low)}</span>
            </div>
            <div className="text-gray-500">
              Vol Médio: <span className="text-gray-300">{formatVolume(stats.avgVolume)}</span>
            </div>
            <div className="text-gray-500">
              Período:{" "}
              <span className="text-gray-300">
                {stats.start.slice(0, 10)} → {stats.end.slice(0, 10)}
              </span>
            </div>
          </div>
        )}

        {error && (
          <div className="mb-4 rounded-lg border border-red-800 bg-red-900/20 p-4 text-red-400">
            {error}
          </div>
        )}

        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-2">
          {loading && (
            <div className="flex h-[800px] items-center justify-center">
              <div className="flex flex-col items-center gap-3">
                <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
                <span className="text-sm text-gray-500">Carregando dados...</span>
              </div>
            </div>
          )}
          {!loading && chartData && (
            <CryptoChart data={chartData} height={800} />
          )}
        </div>

        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
            <h3 className="text-xs font-medium text-gray-500 uppercase">Pipeline</h3>
            <div className="mt-2 space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Janela</span>
                <span className="text-gray-200">60 períodos</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Features</span>
                <span className="text-gray-200">15 indicadores</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Normalização</span>
                <span className="text-gray-200">StandardScaler</span>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
            <h3 className="text-xs font-medium text-gray-500 uppercase">Split dos Dados</h3>
            <div className="mt-3 flex h-4 overflow-hidden rounded-full bg-gray-800">
              <div className="bg-blue-600" style={{ width: "70%" }} />
              <div className="bg-amber-500" style={{ width: "15%" }} />
              <div className="bg-red-500" style={{ width: "15%" }} />
            </div>
            <div className="mt-2 flex justify-between text-xs text-gray-400">
              <span>Treino 70%</span>
              <span>Val 15%</span>
              <span>Teste 15%</span>
            </div>
          </div>

          <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
            <h3 className="text-xs font-medium text-gray-500 uppercase">Indicadores</h3>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {[
                { label: "SMA 7", color: "bg-yellow-500" },
                { label: "SMA 21", color: "bg-blue-500" },
                { label: "SMA 50", color: "bg-purple-500" },
                { label: "RSI 14", color: "bg-cyan-500" },
                { label: "MACD", color: "bg-blue-400" },
                { label: "Signal", color: "bg-amber-400" },
              ].map((ind) => (
                <span
                  key={ind.label}
                  className="inline-flex items-center gap-1 rounded-full bg-gray-800 px-2 py-0.5 text-xs text-gray-300"
                >
                  <span className={`h-1.5 w-1.5 rounded-full ${ind.color}`} />
                  {ind.label}
                </span>
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
            <h3 className="text-xs font-medium text-gray-500 uppercase">Modelo</h3>
            <div className="mt-2 space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Arquitetura</span>
                <span className="text-gray-200">Mamba (SSM)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Framework</span>
                <span className="text-gray-200">PyTorch</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Target</span>
                <span className="text-gray-200">Classificação direcional</span>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
