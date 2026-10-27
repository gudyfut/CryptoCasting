"use client";
import { useEffect, useRef, useState } from "react";
import { CandlestickSeries, ColorType, CrosshairMode, HistogramSeries, LineSeries, LineStyle, createChart, createSeriesMarkers, type UTCTimestamp, type Time, type SeriesMarker } from "lightweight-charts";
import { classesEventos, dataUtc, type Candle, type Modelo, type Observacao } from "@/lib/exploracao";
import { numero, nomes, probabilidadeLegivel } from "@/lib/didatica";

const cores = ["#ef7d86", "#b5a4ef", "#42c9a5"];
export default function GraficoPrevisoes({ candles, observacao, observacoes, modelo, resolucao, selecionar }: { candles: Candle[]; observacao: Observacao; observacoes: Observacao[]; modelo: Modelo; resolucao: number; selecionar: (origem: number) => void }) {
  const recipiente = useRef<HTMLDivElement>(null);
  const callback = useRef(selecionar);
  useEffect(() => { callback.current = selecionar; }, [selecionar]);
  const chave = `${observacao.origem}/${modelo}/${resolucao}/${candles[0]?.time}`;
  const [cursor, setCursor] = useState<{ chave: string; texto: string; previsao?: Observacao }>();
  const leitura = cursor?.chave === chave ? cursor : undefined;
  const probabilidades = observacao.probabilidades[modelo];
  useEffect(() => {
    const elemento = recipiente.current;
    if (!elemento || !candles.length) return;
    const grafico = createChart(elemento, {
      autoSize: true, height: 590,
      layout: { background: { type: ColorType.Solid, color: "#101b2d" }, textColor: "#b9c6d9", fontFamily: "Arial, sans-serif", fontSize: 11, attributionLogo: true, panes: { separatorColor: "#2a3950", separatorHoverColor: "#466180" } },
      grid: { vertLines: { color: "#1d2b40" }, horzLines: { color: "#1d2b40" } },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: { borderColor: "#30405a", minimumWidth: 115 },
      timeScale: { timeVisible: true, secondsVisible: false, borderColor: "#30405a", rightOffset: 4 },
      localization: { locale: "pt-BR", timeFormatter: (t: Time) => dataUtc(Number(t)) },
    });
    const casas = observacao.precoEntrada < 10 ? 5 : 2;
    const precos = grafico.addSeries(CandlestickSeries, { upColor: "#42c9a5", downColor: "#ef7d86", borderVisible: false, wickUpColor: "#42c9a5", wickDownColor: "#ef7d86", priceFormat: { type: "price", precision: casas, minMove: 10 ** -casas }, lastValueVisible: false, priceLineVisible: false });
    precos.setData(candles.map(c => c.open === undefined ? { time: c.time as UTCTimestamp } : { time: c.time as UTCTimestamp, open: c.open, high: c.high!, low: c.low!, close: c.close! }));
    const volume = grafico.addSeries(HistogramSeries, { priceFormat: { type: "volume" }, lastValueVisible: false, priceLineVisible: false }, 1);
    volume.setData(candles.filter(c => c.volume !== undefined).map(c => ({ time: c.time as UTCTimestamp, value: c.volume!, color: c.close! >= c.open! ? "#42c9a570" : "#ef7d8670" })));
    const selecao = observacoes.filter(o => o.origem >= candles[0].time && o.origem <= candles.at(-1)!.time);
    for (let classe = 0; classe < 3; classe++) {
      const serie = grafico.addSeries(LineSeries, { color: cores[classe], lineWidth: 1, lastValueVisible: false, priceLineVisible: false, priceFormat: { type: "custom", formatter: (p: number) => `${Math.round(p * 100)}%` }, autoscaleInfoProvider: () => ({ priceRange: { minValue: 0, maxValue: 1 } }) }, 2);
      // Marcadores vazios quebram a linha em lacunas de origens, sem interpolar previsões ausentes.
      const pontos: ({ time: UTCTimestamp; value?: number })[] = [];
      selecao.forEach((o, i) => { if (i && o.origem - selecao[i - 1].origem > 3600) pontos.push({ time: (selecao[i - 1].origem + 3600) as UTCTimestamp }); pontos.push({ time: o.origem as UTCTimestamp, value: o.probabilidades[modelo][classe] }); });
      serie.setData(pontos);
    }
    for (const [valor, cor, titulo] of [[observacao.precoEntrada * Math.exp(observacao.distancia), cores[2], `Superior · ${probabilidadeLegivel(observacao.probabilidades[modelo][2])}`], [observacao.precoEntrada * Math.exp(-observacao.distancia), cores[0], `Inferior · ${probabilidadeLegivel(observacao.probabilidades[modelo][0])}`], [observacao.precoEntrada, "#a6bad2", "Entrada"]] as const) {
      const linha = grafico.addSeries(LineSeries, { color: cor, lineWidth: 1, lineStyle: LineStyle.Dashed, lastValueVisible: false, priceLineVisible: false, crosshairMarkerVisible: false, title: titulo });
      linha.setData([{ time: observacao.entrada as UTCTimestamp, value: valor }, { time: observacao.expiracao as UTCTimestamp, value: valor }]);
    }
    // Série auxiliar coloca os instantes exatos no eixo; preços nunca são inventados.
    const eventos = grafico.addSeries(LineSeries, { color: "transparent", lineVisible: false, pointMarkersVisible: false, lastValueVisible: false, priceLineVisible: false, crosshairMarkerVisible: false });
    const pontosEventos = new Map<number, number>([[observacao.origem, observacao.precoEntrada], [observacao.entrada, observacao.precoEntrada], [observacao.saida, observacao.precoSaida], [observacao.expiracao, observacao.precoEntrada]]);
    eventos.setData([...pontosEventos.entries()].sort(([a], [b]) => a - b).map(([time, value]) => ({ time: time as UTCTimestamp, value })));
    const marcadores: SeriesMarker<Time>[] = [{ time: observacao.entrada as UTCTimestamp, position: "belowBar", shape: "arrowUp", color: "#a6bad2", text: "Entrada" }, { time: observacao.saida as UTCTimestamp, position: "aboveBar", shape: "circle", color: cores[observacao.classe], text: observacao.classe === 1 ? "Expiração" : "Primeiro toque" }];
    createSeriesMarkers(eventos, marcadores.sort((a, b) => Number(a.time) - Number(b.time)));
    const marcoOrigem = document.createElement("div"), marcoPrazo = document.createElement("div");
    marcoOrigem.className = "marco-grafico origem"; marcoOrigem.innerHTML = "<span>Previsão</span>";
    marcoPrazo.className = "marco-grafico prazo";
    const legendaPrazo = document.createElement("span");
    legendaPrazo.textContent = `Expiração · ${probabilidadeLegivel(observacao.probabilidades[modelo][1])}`;
    marcoPrazo.append(legendaPrazo);
    elemento.append(marcoOrigem, marcoPrazo);
    const posicionar = () => {
      for (const [marco, tempo] of [[marcoOrigem, observacao.origem], [marcoPrazo, observacao.expiracao]] as const) {
        const x = grafico.timeScale().timeToCoordinate(tempo as UTCTimestamp);
        marco.style.display = x === null || x < 0 || x > elemento.clientWidth - 115 ? "none" : "block";
        marco.style.left = `${x ?? 0}px`;
        marco.style.height = `${marco === marcoOrigem ? elemento.clientHeight - 28 : grafico.panes()[0].getHeight()}px`;
        const legenda = marco.firstElementChild as HTMLElement;
        if (x !== null) {
          const preferido = marco === marcoPrazo ? x - legenda.offsetWidth - 4 : x + 5;
          legenda.style.left = `${Math.max(2, Math.min(preferido, elemento.clientWidth - 115 - legenda.offsetWidth - 2)) - x}px`;
          legenda.style.right = "auto";
        }
      }
    };
    grafico.panes()[0].setHeight(350); grafico.panes()[1].setHeight(75); grafico.panes()[2].setHeight(140);
    grafico.timeScale().setVisibleRange({ from: candles[0].time as UTCTimestamp, to: candles.at(-1)!.time as UTCTimestamp });
    grafico.timeScale().subscribeVisibleLogicalRangeChange(posicionar);
    const resize = new ResizeObserver(posicionar); resize.observe(elemento); posicionar();
    const previsoesPorOrigem = new Map(observacoes.map(o => [o.origem, o]));
    grafico.subscribeCrosshairMove(e => {
      const candle = e.seriesData.get(precos);
      const previsao = e.time ? previsoesPorOrigem.get(Math.floor(Number(e.time) / 3600) * 3600) : undefined;
      const texto = e.time && candle && "open" in candle ? `${dataUtc(Number(e.time))} UTC · A ${numero(candle.open, casas)}  M ${numero(candle.high, casas)}  m ${numero(candle.low, casas)}  F ${numero(candle.close, casas)}` : "Mova o cursor sobre um candle para consultar seus preços · UTC";
      setCursor({ chave, texto, previsao });
    });
    grafico.subscribeClick(e => {
      if (!e.time || !observacoes.length) return;
      const t = Number(e.time);
      const perto = observacoes.reduce((a, b) => Math.abs(a.origem - t) <= Math.abs(b.origem - t) ? a : b);
      if (Math.abs(perto.origem - t) <= 3600) callback.current(perto.origem);
    });
    return () => { resize.disconnect(); marcoOrigem.remove(); marcoPrazo.remove(); grafico.remove(); };
  }, [candles, observacao, observacoes, modelo, resolucao, chave]);
  return <div className="grafico-mercado">
    <div className="previsao-no-grafico"><div className="identidade-previsao"><b>{nomes[modelo]} · previsão selecionada</b><span>{dataUtc(observacao.origem)} UTC</span></div><div className="probabilidades-no-grafico">{classesEventos.map((nome, k) => <div key={nome} style={{ borderColor: cores[k] }}><span>{nome}</span><strong style={{ color: cores[k] }}>{probabilidadeLegivel(probabilidades[k])}</strong><small>{observacao.classe === k ? observacao.ambiguo ? "Rótulo adotado · ordem ambígua" : "Desfecho observado" : ""}</small></div>)}</div><p>Probabilidades de qual evento acontece primeiro. Expiração = nenhum limite atingido até o prazo; não significa preço parado.</p></div>
    <div className="cursor-ohlc">{leitura?.texto || "Mova o cursor para consultar abertura, máxima, mínima e fechamento · UTC"}</div>
    <div ref={recipiente} className="canvas-mercado" role="img" aria-label={`Candles reais; inferior ${probabilidadeLegivel(probabilidades[0])}, expiração ${probabilidadeLegivel(probabilidades[1])}, superior ${probabilidadeLegivel(probabilidades[2])}, previsão de ${dataUtc(observacao.origem)} UTC. Abaixo: volume e probabilidades de ${nomes[modelo]}.`}/>
    <div className="probabilidades-cursor">{leitura?.previsao ? <><b>No cursor · previsão emitida em {dataUtc(leitura.previsao.origem)} UTC:</b>{classesEventos.map((nome, k) => <span key={nome} style={{ color: cores[k] }}>{nome}: <strong>{probabilidadeLegivel(leitura.previsao!.probabilidades[modelo][k])}</strong></span>)}</> : <span>Mova o cursor: os valores da previsão emitida no início daquela hora aparecem aqui, sem interpolação de probabilidades.</span>}</div>
    <div className="legenda-mercado"><span>Preço em USDT · candles de {resolucao} min</span><span>Volume na moeda base</span><span>Probabilidades de {nomes[modelo]}:</span>{["Inferior", "Expiração", "Superior"].map((c, i) => <span key={c}><i style={{ background: cores[i] }}/>{c}</span>)}</div></div>;
}
