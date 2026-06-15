import { NextResponse } from "next/server";
import {
  readCSVFile,
  listAvailablePairs,
  aggregateCandles,
  type Timeframe,
} from "@/lib/csv";
import { computeAllIndicators } from "@/lib/indicators";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ par: string }> }
) {
  const { par } = await params;
  const tf = new URL(_request.url).searchParams.get("tf") as Timeframe || "1h";
  const validTfs: Timeframe[] = ["5m", "15m", "1h", "4h", "1d"];
  const timeframe: Timeframe = validTfs.includes(tf) ? tf : "1h";

  try {
    const available = await listAvailablePairs();
    if (!available.includes(par)) {
      return NextResponse.json({ error: "Par não encontrado" }, { status: 404 });
    }

    const rawCandles = await readCSVFile(par);
    const candles = aggregateCandles(rawCandles, timeframe);

    const dates = candles.map((c) => c.timestamp);
    const closes = candles.map((c) => c.close);
    const ohlc = candles.map((c) => [c.open, c.close, c.low, c.high]);
    const volumes = candles.map((c) => c.volume);

    const indicators = computeAllIndicators(closes);

    const first = closes[0];
    const last = closes[closes.length - 1];
    const priceChange = last - first;
    const priceChangePercent = (priceChange / first) * 100;

    return NextResponse.json({
      par,
      timeframe,
      candles: candles.length,
      dates,
      ohlc,
      volumes,
      closes,
      indicators,
      stats: {
        start: dates[0],
        end: dates[dates.length - 1],
        firstPrice: first,
        lastPrice: last,
        priceChange,
        priceChangePercent,
        high: Math.max(...candles.map((c) => c.high)),
        low: Math.min(...candles.map((c) => c.low)),
        avgVolume: volumes.reduce((a, b) => a + b, 0) / volumes.length,
      },
    });
  } catch (e) {
    return NextResponse.json(
      { error: `Erro ao ler dados: ${(e as Error).message}` },
      { status: 500 }
    );
  }
}
