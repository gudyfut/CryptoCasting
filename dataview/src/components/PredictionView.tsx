"use client";

import { useState, useEffect, useRef } from "react";

interface Prediction {
  timestamp: string;
  close: number;
  atual: number;
  previsto: number;
  correto: boolean;
  probabilidade_alta: number;
}

interface PredictionData {
  par: string;
  intervalo: string;
  janela: number;
  total_amostras: number;
  resumo: { accuracy: number; baseline_accuracy: number };
  previsoes: Prediction[];
  walk_forward: Array<{
    fold: number;
    periodo: string;
    n_amostras: number;
    accuracy: number;
    f1: number;
  }>;
  historico: {
    train_loss: number[];
    val_loss: number[];
    val_acc: number[];
  };
  metricas_modelo: Record<string, number>;
  metricas_baseline: Record<string, Record<string, number>>;
}

function buildPredictionChartOption(data: PredictionData) {
  const timestamps = data.previsoes.map((p) => p.timestamp);
  const closes = data.previsoes.map((p) => p.close);
  const correct = data.previsoes.map((p) => (p.correto ? p.close : null));
  const incorrect = data.previsoes.map((p) => (!p.correto ? p.close : null));

  return {
    backgroundColor: "transparent",
    animation: false,
    grid: { left: 70, right: 30, top: 40, bottom: 60 },
    xAxis: {
      type: "category",
      data: timestamps,
      axisLabel: {
        fontSize: 10,
        color: "#6b7280",
        formatter: (v: string) => v.slice(5, 16),
      },
      axisLine: { lineStyle: { color: "#374151" } },
    },
    yAxis: {
      type: "value",
      scale: true,
      splitLine: { lineStyle: { color: "#1f2937" } },
      axisLabel: { fontSize: 10, color: "#9ca3af" },
    },
    dataZoom: [
      { type: "inside", start: 0, end: 100 },
      {
        type: "slider",
        bottom: 5,
        height: 20,
        borderColor: "#374151",
        backgroundColor: "#111827",
        fillerColor: "rgba(59,130,246,0.15)",
        handleStyle: { color: "#3b82f6" },
        textStyle: { color: "#6b7280" },
      },
    ],
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(17,24,39,0.95)",
      borderColor: "#374151",
      textStyle: { color: "#f3f4f6", fontSize: 12 },
      formatter: (params: unknown[]) => {
        const p = params as Record<string, unknown>[];
        if (!p || p.length === 0) return "";
        const idx = p[0].dataIndex as number;
        const pred = data.previsoes[idx];
        if (!pred) return "";
        const dirIcon = pred.previsto === 1 ? "▲" : "▼";
        const actualIcon = pred.atual === 1 ? "▲" : "▼";
        const clr = pred.correto ? "#22c55e" : "#ef4444";
        return `<div style="font-weight:600;margin-bottom:4px">${pred.timestamp}</div>
          <div>Close: $${pred.close.toLocaleString()}</div>
          <div style="color:${clr}">Previsão: ${dirIcon} ${pred.previsto === 1 ? "Alta" : "Baixa"} (${(pred.probabilidade_alta * 100).toFixed(1)}%)</div>
          <div>Real: ${actualIcon} ${pred.atual === 1 ? "Alta" : "Baixa"}</div>
          <div style="color:${clr};font-weight:600">${pred.correto ? "✓ Correto" : "✗ Incorreto"}</div>`;
      },
    },
    legend: {
      top: 0,
      textStyle: { color: "#9ca3af", fontSize: 11 },
      data: ["Preço", "✓ Correto", "✗ Incorreto"],
    },
    series: [
      {
        name: "Preço",
        type: "line",
        data: closes,
        showSymbol: false,
        lineStyle: { width: 1.5, color: "#60a5fa" },
      },
      {
        name: "✓ Correto",
        type: "scatter",
        data: correct,
        symbolSize: 5,
        itemStyle: { color: "#22c55e", opacity: 0.7 },
      },
      {
        name: "✗ Incorreto",
        type: "scatter",
        data: incorrect,
        symbolSize: 5,
        itemStyle: { color: "#ef4444", opacity: 0.7 },
      },
    ],
  };
}

function buildTrainingChartOption(data: PredictionData) {
  const epochs = data.historico.train_loss.map((_, i) => i + 1);
  return {
    backgroundColor: "transparent",
    animation: false,
    grid: { left: 50, right: 50, top: 35, bottom: 30 },
    xAxis: {
      type: "category",
      data: epochs,
      axisLabel: { fontSize: 10, color: "#6b7280" },
      axisLine: { lineStyle: { color: "#374151" } },
    },
    yAxis: [
      {
        type: "value",
        name: "Loss",
        nameTextStyle: { color: "#9ca3af", fontSize: 10 },
        splitLine: { lineStyle: { color: "#1f2937" } },
        axisLabel: { fontSize: 10, color: "#9ca3af" },
      },
      {
        type: "value",
        name: "Acc",
        nameTextStyle: { color: "#9ca3af", fontSize: 10 },
        min: 0,
        max: 1,
        splitLine: { show: false },
        axisLabel: {
          fontSize: 10,
          color: "#9ca3af",
          formatter: (v: number) => `${(v * 100).toFixed(0)}%`,
        },
      },
    ],
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(17,24,39,0.95)",
      borderColor: "#374151",
      textStyle: { color: "#f3f4f6", fontSize: 11 },
    },
    legend: {
      top: 0,
      textStyle: { color: "#9ca3af", fontSize: 11 },
      data: ["Train Loss", "Val Loss", "Val Acc"],
    },
    series: [
      {
        name: "Train Loss",
        type: "line",
        data: data.historico.train_loss,
        showSymbol: false,
        lineStyle: { width: 1.5, color: "#3b82f6" },
      },
      {
        name: "Val Loss",
        type: "line",
        data: data.historico.val_loss,
        showSymbol: false,
        lineStyle: { width: 1.5, color: "#f59e0b" },
      },
      {
        name: "Val Acc",
        type: "line",
        data: data.historico.val_acc,
        showSymbol: false,
        yAxisIndex: 1,
        lineStyle: { width: 1.5, color: "#22c55e" },
      },
    ],
  };
}

function buildWalkForwardOption(data: PredictionData) {
  const folds = data.walk_forward.map((f) => `Fold ${f.fold}`);
  const accs = data.walk_forward.map((f) => f.accuracy);
  const colors = accs.map((a) => (a >= 0.5 ? "#22c55e" : "#ef4444"));

  return {
    backgroundColor: "transparent",
    animation: false,
    grid: { left: 50, right: 20, top: 35, bottom: 30 },
    xAxis: {
      type: "category",
      data: folds,
      axisLabel: { fontSize: 10, color: "#6b7280" },
      axisLine: { lineStyle: { color: "#374151" } },
    },
    yAxis: {
      type: "value",
      min: 0,
      max: 1,
      splitLine: { lineStyle: { color: "#1f2937" } },
      axisLabel: {
        fontSize: 10,
        color: "#9ca3af",
        formatter: (v: number) => `${(v * 100).toFixed(0)}%`,
      },
    },
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(17,24,39,0.95)",
      borderColor: "#374151",
      textStyle: { color: "#f3f4f6", fontSize: 11 },
      formatter: (params: unknown[]) => {
        const p = params as Record<string, unknown>[];
        if (!p || p.length === 0) return "";
        const idx = p[0].dataIndex as number;
        const f = data.walk_forward[idx];
        if (!f) return "";
        return `<div>Fold ${f.fold} (${f.periodo})</div>
          <div>Acc: ${(f.accuracy * 100).toFixed(1)}%</div>
          <div>F1: ${f.f1.toFixed(4)}</div>
          <div>Amostras: ${f.n_amostras}</div>`;
      },
    },
    series: [
      {
        type: "bar",
        data: accs.map((v, i) => ({ value: v, itemStyle: { color: colors[i] } })),
        barWidth: "50%",
        markLine: {
          silent: true,
          symbol: "none",
          lineStyle: { color: "#6b7280", type: "dashed", width: 1 },
          data: [
            {
              yAxis: 0.5,
              label: { formatter: "50%", fontSize: 9, color: "#6b7280" },
            },
          ],
        },
      },
    ],
  };
}

function MetricCard({
  label,
  value,
  sublabel,
  color,
}: {
  label: string;
  value: string;
  sublabel?: string;
  color?: string;
}) {
  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
      <h3 className="text-xs font-medium text-gray-500 uppercase">{label}</h3>
      <div
        className="mt-1 text-2xl font-bold"
        style={color ? { color } : undefined}
      >
        {value}
      </div>
      {sublabel && (
        <div className="mt-0.5 text-xs text-gray-500">{sublabel}</div>
      )}
    </div>
  );
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type ChartInstance = any;

export default function PredictionView({ par }: { par: string }) {
  const [data, setData] = useState<PredictionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const predRef = useRef<HTMLDivElement>(null);
  const trainRef = useRef<HTMLDivElement>(null);
  const wfRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetch(`/api/predictions/${par}`)
      .then((r) => {
        if (!r.ok) throw new Error("Previsões não disponíveis");
        return r.json();
      })
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [par]);

  useEffect(() => {
    if (!data) return;

    let charts: ChartInstance[] = [];
    let onResize: (() => void) | null = null;
    let cancelled = false;

    import("echarts").then((echarts) => {
      if (cancelled) return;

      const init = (
        ref: React.RefObject<HTMLDivElement | null>,
        option: Record<string, unknown>
      ) => {
        if (!ref.current) return;
        const chart = echarts.init(ref.current, "dark");
        chart.setOption(option);
        charts.push(chart);
      };

      init(predRef, buildPredictionChartOption(data));
      init(trainRef, buildTrainingChartOption(data));
      init(wfRef, buildWalkForwardOption(data));

      onResize = () => charts.forEach((c) => c?.resize());
      window.addEventListener("resize", onResize);
    });

    return () => {
      cancelled = true;
      if (onResize) window.removeEventListener("resize", onResize);
      charts.forEach((c) => c?.dispose());
    };
  }, [data]);

  if (loading) {
    return (
      <div className="flex h-[600px] items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
          <span className="text-sm text-gray-500">
            Carregando previsões...
          </span>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="rounded-lg border border-amber-800 bg-amber-900/20 p-6 text-center">
        <p className="text-amber-400">
          {error || "Nenhum dado disponível"}
        </p>
        <p className="mt-2 text-sm text-gray-500">
          Treine o modelo com{" "}
          <code className="rounded bg-gray-800 px-1.5 py-0.5">
            python run_treino.py --pares {par}
          </code>
        </p>
      </div>
    );
  }

  const acc = data.resumo.accuracy;
  const baseline = data.resumo.baseline_accuracy;
  const diff = acc - baseline;
  const accColor = diff >= 0 ? "#22c55e" : "#ef4444";
  const corretos = data.previsoes.filter((p) => p.correto).length;
  const fmtPct = (v: number) => `${(v * 100).toFixed(1)}%`;

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <MetricCard
          label="Acurácia"
          value={fmtPct(acc)}
          sublabel={`${corretos}/${data.total_amostras} corretas`}
          color={accColor}
        />
        <MetricCard
          label="Baseline"
          value={fmtPct(baseline)}
          sublabel="Momentum ingênuo"
        />
        <MetricCard
          label="Diferença"
          value={`${diff >= 0 ? "+" : ""}${fmtPct(diff)}`}
          sublabel="Mamba vs Baseline"
          color={accColor}
        />
        <MetricCard
          label="F1-Score"
          value={(data.metricas_modelo.f1 || 0).toFixed(4)}
          sublabel={
            data.metricas_modelo.recall
              ? `Recall: ${fmtPct(data.metricas_modelo.recall)}`
              : undefined
          }
        />
        <MetricCard
          label="Amostras"
          value={data.total_amostras.toString()}
          sublabel={`Janela: ${data.janela} • ${data.intervalo}`}
        />
      </div>

      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-2">
        <div className="mb-1 px-2 pt-1 text-sm font-medium text-gray-400">
          Preço — Previsões do Modelo (conjunto de teste)
        </div>
        <div ref={predRef} style={{ width: "100%", height: 420 }} />
        <div className="flex items-center gap-4 px-2 pb-1 text-xs text-gray-500">
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-green-500" /> Previsão
            correta
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-red-500" /> Previsão
            incorreta
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-0.5 w-4 bg-blue-400" /> Preço de fechamento
          </span>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-2">
          <div className="mb-1 px-2 pt-1 text-sm font-medium text-gray-400">
            Histórico de Treino
          </div>
          <div ref={trainRef} style={{ width: "100%", height: 250 }} />
        </div>

        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-2">
          <div className="mb-1 px-2 pt-1 text-sm font-medium text-gray-400">
            Walk-Forward Validation
          </div>
          <div ref={wfRef} style={{ width: "100%", height: 250 }} />
        </div>
      </div>
    </div>
  );
}
