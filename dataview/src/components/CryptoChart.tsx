"use client";

import { useEffect, useRef } from "react";

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

interface CryptoChartProps {
  data: ChartData;
  height?: number;
}

function extractValue(raw: unknown): number | null {
  if (raw == null) return null;
  if (typeof raw === "number") return raw;
  if (Array.isArray(raw)) return Number(raw[1]) || null;
  if (typeof raw === "object") {
    const obj = raw as Record<string, unknown>;
    if (typeof obj.value === "number") return obj.value;
  }
  return null;
}

function buildOption(data: ChartData): Record<string, unknown> {
  const volumeColors = data.ohlc.map((c) =>
    c[1] >= c[0] ? "rgba(34,197,94,0.6)" : "rgba(239,68,68,0.6)"
  );

  const macdHistColors = data.indicators.macdHist.map((v) =>
    v === null
      ? "transparent"
      : v >= 0
        ? "rgba(34,197,94,0.7)"
        : "rgba(239,68,68,0.7)"
  );

  return {
    backgroundColor: "transparent",
    animation: true,
    animationDuration: 400,
    grid: [
      { left: 80, right: 30, top: 30, height: "38%" },
      { left: 80, right: 30, top: "48%", height: "10%" },
      { left: 80, right: 30, top: "63%", height: "12%" },
      { left: 80, right: 30, top: "80%", height: "12%" },
    ],
    xAxis: [
      {
        type: "category",
        data: data.dates,
        gridIndex: 0,
        show: false,
        boundaryGap: true,
      },
      {
        type: "category",
        data: data.dates,
        gridIndex: 1,
        show: false,
        boundaryGap: true,
      },
      {
        type: "category",
        data: data.dates,
        gridIndex: 2,
        show: false,
        boundaryGap: true,
      },
      {
        type: "category",
        data: data.dates,
        gridIndex: 3,
        show: true,
        boundaryGap: true,
        axisLabel: {
          fontSize: 10,
          color: "#6b7280",
          formatter: (value: string) => {
            const d = value.split(" ");
            return d.length > 1
              ? `${d[0].slice(5)}\n${d[1].slice(0, 5)}`
              : d[0].slice(5);
          },
        },
        axisLine: { lineStyle: { color: "#374151" } },
      },
    ],
    yAxis: [
      {
        type: "value",
        gridIndex: 0,
        scale: true,
        splitLine: { lineStyle: { color: "#1f2937" } },
        axisLabel: { fontSize: 10, color: "#9ca3af" },
      },
      {
        type: "value",
        gridIndex: 1,
        splitLine: { show: false },
        axisLabel: { fontSize: 10, color: "#9ca3af" },
      },
      {
        type: "value",
        gridIndex: 2,
        min: 0,
        max: 100,
        splitLine: { lineStyle: { color: "#1f2937" } },
        axisLabel: { fontSize: 10, color: "#9ca3af" },
      },
      {
        type: "value",
        gridIndex: 3,
        splitLine: { lineStyle: { color: "#1f2937" } },
        axisLabel: { fontSize: 10, color: "#9ca3af" },
      },
    ],
    dataZoom: [
      {
        type: "inside",
        xAxisIndex: [0, 1, 2, 3],
        start: 0,
        end: 100,
      },
      {
        type: "slider",
        xAxisIndex: [0, 1, 2, 3],
        bottom: 0,
        height: 20,
        borderColor: "#374151",
        backgroundColor: "#111827",
        fillerColor: "rgba(59,130,246,0.15)",
        handleStyle: { color: "#3b82f6" },
        textStyle: { color: "#6b7280" },
        dataBackground: {
          lineStyle: { color: "#3b82f6" },
          areaStyle: { color: "rgba(59,130,246,0.1)" },
        },
      },
    ],
    tooltip: {
      trigger: "axis",
      axisPointer: {
        type: "cross",
        crossStyle: { color: "#6b7280" },
        lineStyle: { color: "#6b7280", type: "dashed" },
      },
      backgroundColor: "rgba(17,24,39,0.95)",
      borderColor: "#374151",
      textStyle: { color: "#f3f4f6", fontSize: 12 },
      formatter: (params: unknown[]) => {
        const p = params as Record<string, unknown>[];
        if (!p || p.length === 0) return "";
        const date = p[0].axisValue as string;
        let html = `<div style="font-weight:600;margin-bottom:4px">${date}</div>`;

        for (const item of p) {
          const seriesName = item.seriesName as string;
          const color = item.color as string;
          const raw = item.data;

          if (seriesName === "Price") {
            const d = raw as number[];
            const chg = d[1] - d[0];
            const pct = ((chg / d[0]) * 100).toFixed(2);
            const clr = chg >= 0 ? "#22c55e" : "#ef4444";
            html += `<div style="color:${color}">O: ${d[0].toFixed(2)} H: ${d[3].toFixed(2)} L: ${d[2].toFixed(2)} C: <span style="color:${clr}">${d[1].toFixed(2)} (${pct}%)</span></div>`;
          } else if (seriesName === "Volume") {
            const v = extractValue(raw);
            html += `<div style="color:${color}">Vol: ${v != null ? v.toFixed(2) : "—"}</div>`;
          } else {
            const v = extractValue(raw);
            html += `<div style="color:${color}">${seriesName}: ${v != null ? v.toFixed(4) : "—"}</div>`;
          }
        }
        return html;
      },
    },
    legend: {
      top: 0,
      textStyle: { color: "#9ca3af", fontSize: 11 },
      itemWidth: 14,
      itemHeight: 10,
      data: ["Price", "SMA 7", "SMA 21", "SMA 50"],
    },
    series: [
      {
        name: "Price",
        type: "candlestick",
        data: data.ohlc,
        xAxisIndex: 0,
        yAxisIndex: 0,
        itemStyle: {
          color: "#22c55e",
          color0: "#ef4444",
          borderColor: "#22c55e",
          borderColor0: "#ef4444",
        },
      },
      {
        name: "SMA 7",
        type: "line",
        data: data.indicators.sma7,
        xAxisIndex: 0,
        yAxisIndex: 0,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 1.2, color: "#f59e0b" },
      },
      {
        name: "SMA 21",
        type: "line",
        data: data.indicators.sma21,
        xAxisIndex: 0,
        yAxisIndex: 0,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 1.2, color: "#3b82f6" },
      },
      {
        name: "SMA 50",
        type: "line",
        data: data.indicators.sma50,
        xAxisIndex: 0,
        yAxisIndex: 0,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 1.2, color: "#a855f7" },
      },
      {
        name: "Volume",
        type: "bar",
        data: data.volumes.map((v, i) => ({
          value: v,
          itemStyle: { color: volumeColors[i] },
        })),
        xAxisIndex: 1,
        yAxisIndex: 1,
      },
      {
        name: "RSI 14",
        type: "line",
        data: data.indicators.rsi14,
        xAxisIndex: 2,
        yAxisIndex: 2,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 1.5, color: "#06b6d4" },
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(6,182,212,0.15)" },
              { offset: 1, color: "rgba(6,182,212,0)" },
            ],
          } as unknown,
        },
        markLine: {
          silent: true,
          symbol: "none",
          lineStyle: { color: "#374151", type: "dashed", width: 1 },
          data: [
            {
              yAxis: 70,
              label: { formatter: "70", fontSize: 9, color: "#6b7280" },
            },
            {
              yAxis: 30,
              label: { formatter: "30", fontSize: 9, color: "#6b7280" },
            },
          ],
        },
      },
      {
        name: "MACD",
        type: "line",
        data: data.indicators.macd,
        xAxisIndex: 3,
        yAxisIndex: 3,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 1.5, color: "#3b82f6" },
      },
      {
        name: "Signal",
        type: "line",
        data: data.indicators.macdSignal,
        xAxisIndex: 3,
        yAxisIndex: 3,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 1.5, color: "#f59e0b" },
      },
      {
        name: "Histogram",
        type: "bar",
        data: data.indicators.macdHist.map((v, i) => ({
          value: v,
          itemStyle: { color: macdHistColors[i] },
        })),
        xAxisIndex: 3,
        yAxisIndex: 3,
      },
    ],
  };
}

export default function CryptoChart({ data, height = 800 }: CryptoChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<unknown>(null);
  const dataRef = useRef(data);

  useEffect(() => {
    dataRef.current = data;
  });

  useEffect(() => {
    if (!containerRef.current) return;

    import("echarts").then((echarts) => {
      if (!containerRef.current) return;
      const chart = echarts.init(containerRef.current, "dark");
      chartRef.current = chart;
      chart.setOption(buildOption(dataRef.current));
      window.addEventListener("resize", () => chart.resize());
    });

    return () => {
      if (chartRef.current) {
        (chartRef.current as { dispose: () => void }).dispose();
        chartRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    const chart = chartRef.current as {
      setOption: (opt: Record<string, unknown>) => void;
    } | null;
    if (chart) {
      chart.setOption(buildOption(data));
    }
  }, [data]);

  return (
    <div
      ref={containerRef}
      style={{ width: "100%", height: `${height}px` }}
    />
  );
}
