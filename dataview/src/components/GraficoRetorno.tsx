"use client";
import { useEffect, useRef } from "react";
import { createChart, CandlestickSeries, LineSeries, HistogramSeries, ColorType, LineStyle, type UTCTimestamp } from "lightweight-charts";
import type { Serie,Origem } from "@/lib/tipos";
import { cores,nomes,retornoPercentual } from "@/lib/tipos";

export default function GraficoRetorno({serie,origem,modelo,selecionar}:{serie:Serie;origem:Origem;modelo:string;selecionar:(tempo:number)=>void}) {
  const elemento = useRef<HTMLDivElement>(null);
  const callback = useRef(selecionar);
  useEffect(()=>{ callback.current=selecionar; },[selecionar]);
  useEffect(()=>{
    const alvo=elemento.current;
    if (!alvo) return;
    const chart=createChart(alvo,{height:510,autoSize:true,handleScroll:{vertTouchDrag:false},layout:{background:{type:ColorType.Solid,color:"#ffffff"},textColor:"#566c7c",fontFamily:"Arial",fontSize:11},grid:{vertLines:{color:"#f0f3f6"},horzLines:{color:"#edf1f5"}},rightPriceScale:{borderColor:"#d9e2e9",minimumWidth:95},timeScale:{timeVisible:true,secondsVisible:false,borderColor:"#d9e2e9"},localization:{locale:"pt-BR",timeFormatter:(t:unknown)=>typeof t==="number"?new Date(t*1000).toLocaleString("pt-BR",{timeZone:"UTC",day:"2-digit",month:"2-digit",hour:"2-digit",minute:"2-digit"}):String(t)}});
    const candles=chart.addSeries(CandlestickSeries,{upColor:"#1d9174",downColor:"#cf5664",wickUpColor:"#1d9174",wickDownColor:"#cf5664",borderVisible:false,priceFormat:{type:"price",precision:serie.par==="XRPUSDT"?5:2,minMove:serie.par==="XRPUSDT"?.00001:.01}});
    candles.setData(serie.precos.map(p=>p.close===undefined?{time:p.time as UTCTimestamp}:{time:p.time as UTCTimestamp,open:p.open!,high:p.high!,low:p.low!,close:p.close}));
    const volume=chart.addSeries(HistogramSeries,{priceScaleId:"volume",priceFormat:{type:"volume"},lastValueVisible:false,priceLineVisible:false});
    chart.priceScale("volume").applyOptions({scaleMargins:{top:.87,bottom:0}});
    candles.priceScale().applyOptions({scaleMargins:{top:.13,bottom:.2}});
    volume.setData(serie.precos.filter(p=>p.close!==undefined).map(p=>({time:p.time as UTCTimestamp,value:p.volume!,color:p.close!>=p.open!?"#1d91742a":"#cf56642a"})));
    const previsao=origem.previsoes[modelo];
    if (previsao!==undefined) {
      const preco=origem.preco*Math.exp(previsao);
      const linha=chart.addSeries(LineSeries,{color:cores[modelo],lineWidth:2,lineStyle:LineStyle.Dashed,pointMarkersVisible:true,pointMarkersRadius:5,priceLineVisible:false,lastValueVisible:false});
      linha.setData([{time:origem.tempo as UTCTimestamp,value:origem.preco},{time:origem.destino as UTCTimestamp,value:preco}]);
      candles.createPriceLine({price:preco,color:cores[modelo],lineWidth:1,lineStyle:LineStyle.Dashed,axisLabelVisible:true,title:`${nomes[modelo]} · ${retornoPercentual(previsao)}`});
    }
    const observado=chart.addSeries(LineSeries,{color:"#192f43",lineVisible:false,pointMarkersVisible:true,pointMarkersRadius:6,priceLineVisible:false,lastValueVisible:false});
    observado.setData([{time:origem.tempo as UTCTimestamp,value:origem.preco},{time:origem.destino as UTCTimestamp,value:origem.preco_real}]);
    chart.timeScale().setVisibleRange({from:Math.max(serie.precos[0].time,origem.tempo-72*3600) as UTCTimestamp,to:(origem.destino+12*3600) as UTCTimestamp});
    chart.subscribeClick(param=>{if(typeof param.time==="number") callback.current(param.time);});
    return ()=>chart.remove();
  },[serie,origem,modelo]);
  return <div ref={elemento} className="grafico-profissional" aria-label={`Candles horários e previsão terminal de ${nomes[modelo]}`} />;
}

