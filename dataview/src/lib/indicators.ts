type NullableNumber = number | null;

export interface IndicatorData {
  sma7: NullableNumber[];
  sma21: NullableNumber[];
  sma50: NullableNumber[];
  rsi14: NullableNumber[];
  macd: NullableNumber[];
  macdSignal: NullableNumber[];
  macdHist: NullableNumber[];
}

function sma(closes: number[], period: number): NullableNumber[] {
  const result: NullableNumber[] = new Array(closes.length).fill(null);
  for (let i = period - 1; i < closes.length; i++) {
    let sum = 0;
    for (let j = i - period + 1; j <= i; j++) sum += closes[j];
    result[i] = sum / period;
  }
  return result;
}

function ema(data: number[], period: number): NullableNumber[] {
  const result: NullableNumber[] = new Array(data.length).fill(null);
  const k = 2 / (period + 1);
  let start = -1;
  for (let i = 0; i < data.length; i++) {
    if (start === -1) {
      if (i >= period - 1) {
        let sum = 0;
        for (let j = i - period + 1; j <= i; j++) sum += data[j];
        result[i] = sum / period;
        start = i;
      }
    } else {
      result[i] = data[i] * k + result[i - 1]! * (1 - k);
    }
  }
  return result;
}

function calcRsi(closes: number[], period: number): NullableNumber[] {
  const result: NullableNumber[] = new Array(closes.length).fill(null);
  if (closes.length < period + 1) return result;

  const gains: number[] = [];
  const losses: number[] = [];
  for (let i = 1; i < closes.length; i++) {
    const diff = closes[i] - closes[i - 1];
    gains.push(diff > 0 ? diff : 0);
    losses.push(diff < 0 ? -diff : 0);
  }

  let avgGain = 0;
  let avgLoss = 0;
  for (let i = 0; i < period; i++) {
    avgGain += gains[i];
    avgLoss += losses[i];
  }
  avgGain /= period;
  avgLoss /= period;

  const alpha = 1 / period;
  result[period] =
    avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);

  for (let i = period; i < gains.length; i++) {
    avgGain = avgGain * (1 - alpha) + gains[i] * alpha;
    avgLoss = avgLoss * (1 - alpha) + losses[i] * alpha;
    result[i + 1] =
      avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
  }
  return result;
}

function calcMacd(
  closes: number[],
  fast: number,
  slow: number,
  signal: number
): { macd: NullableNumber[]; signal: NullableNumber[]; hist: NullableNumber[] } {
  const emaFast = ema(closes, fast);
  const emaSlow = ema(closes, slow);

  const macdLine: NullableNumber[] = new Array(closes.length).fill(null);
  for (let i = 0; i < closes.length; i++) {
    if (emaFast[i] !== null && emaSlow[i] !== null) {
      macdLine[i] = emaFast[i]! - emaSlow[i]!;
    }
  }

  const macdValues: number[] = [];
  const macdIndices: number[] = [];
  for (let i = 0; i < macdLine.length; i++) {
    if (macdLine[i] !== null) {
      macdValues.push(macdLine[i]!);
      macdIndices.push(i);
    }
  }

  const signalEma = ema(macdValues, signal);
  const signalLine: NullableNumber[] = new Array(closes.length).fill(null);
  const hist: NullableNumber[] = new Array(closes.length).fill(null);
  for (let j = 0; j < macdIndices.length; j++) {
    const idx = macdIndices[j];
    signalLine[idx] = signalEma[j];
    if (macdLine[idx] !== null && signalEma[j] !== null) {
      hist[idx] = macdLine[idx]! - signalEma[j]!;
    }
  }

  return { macd: macdLine, signal: signalLine, hist };
}

export function computeAllIndicators(closes: number[]): IndicatorData {
  const { macd, signal, hist } = calcMacd(closes, 12, 26, 9);
  return {
    sma7: sma(closes, 7),
    sma21: sma(closes, 21),
    sma50: sma(closes, 50),
    rsi14: calcRsi(closes, 14),
    macd,
    macdSignal: signal,
    macdHist: hist,
  };
}
