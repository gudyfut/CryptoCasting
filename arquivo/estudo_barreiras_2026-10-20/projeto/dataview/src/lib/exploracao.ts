/** Contrato de apresentação; classes mantêm a ordem do experimento. */
export const classesEventos = ["Inferior primeiro", "Expiração", "Superior primeiro"];
export const modelosExplorador = ["lstm", "mamba", "ar1"] as const;
export type Modelo = typeof modelosExplorador[number];
export type Celula = { id: string; par: string; contexto: number; horizonte: number; fold: string; seed: number; n: number; inicio: number; fim: number; execucaoInicio: string; execucaoFim: string };
export type Observacao = { origem: number; entrada: number; expiracao: number; saida: number; saidaConhecida: number; precoEntrada: number; precoSaida: number; distancia: number; classe: number; ambiguo: boolean; probabilidades: Record<Modelo, number[]> };
export type Metricas = { n: number; log_loss: number; brier: number; balanced_accuracy: number; recall: number[]; precisao: (number | null)[]; matriz_confusao: number[][]; calibracao: { n: number; previsao_media: number | null; frequencia: number | null }[][] };
export type SeriePrevisoes = { celula: Celula; metricas: Record<Modelo, Metricas>; observacoes: Observacao[] };
export type IndicePublico = { ciclo: string; dataset: string; geradoUtc: string; celulas: Celula[]; recallMedio: Record<Modelo, number[]>; inicioPrecos: number; fimPrecos: number };
export type Candle = { time: number; open?: number; high?: number; low?: number; close?: number; volume?: number };
export const classePrevista = (p: number[]) => p.indexOf(Math.max(...p));
export const dataUtc = (segundos: number, segundosVisiveis = false) => new Date(segundos * 1000).toLocaleString("pt-BR", { timeZone: "UTC", day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit", ...(segundosVisiveis ? { second: "2-digit" } : {}) });

export function agregarCandles(linhas: number[][], minutos: number): Candle[] {
  const grupos = new Map<number, number[][]>();
  for (const linha of linhas) {
    const tempo = Math.floor(linha[0] / (minutos * 60)) * minutos * 60;
    const grupo = grupos.get(tempo) ?? [];
    grupo.push(linha); grupos.set(tempo, grupo);
  }
  return [...grupos.entries()].sort(([a], [b]) => a - b).map(([time, grupo]) => {
    // Candle incompleto permanece vazio; não inventar OHLC com parte da hora.
    if (grupo.length !== minutos || grupo.some(r => r.length !== 6 || r.slice(1).some(v => !Number.isFinite(v))) || new Set(grupo.map(r => r[0])).size !== minutos) return { time };
    grupo.sort((a, b) => a[0] - b[0]);
    return { time, open: grupo[0][1], high: Math.max(...grupo.map(r => r[2])), low: Math.min(...grupo.map(r => r[3])), close: grupo.at(-1)![4], volume: grupo.reduce((s, r) => s + r[5], 0) };
  });
}
