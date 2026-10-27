"use client";
import {useEffect,useMemo,useState} from "react";
import type {IndiceSerie,Serie} from "@/lib/tipos";
import {nomes,cores,numero,dataUTC,retornoPercentual} from "@/lib/tipos";
import GraficoRetorno from "./GraficoRetorno";

export default function ExploradorRetorno({indice,idInicial}:{indice:IndiceSerie[];idInicial?:string}) {
  const [id,setId]=useState(indice.some(s=>s.id===idInicial)?idInicial!:indice[0]?.id??"");
  const [serie,setSerie]=useState<Serie|null>(null);
  const [erro,setErro]=useState("");
  const [indiceOrigem,setIndiceOrigem]=useState(0);
  const [modelo,setModelo]=useState("mamba");
  const [busca,setBusca]=useState("");
  const [carregando,setCarregando]=useState(false);
  useEffect(()=>{
    if(!id)return;
    const controle=new AbortController();
    async function carregar(){
      setCarregando(true);setErro("");
      try{
        const resposta=await fetch(`/api/estudo/serie?id=${id}`,{signal:controle.signal});
        const dados=await resposta.json();
        if(!resposta.ok)throw new Error(dados.erro??"Falha ao carregar série.");
        const nova=dados as Serie;
        const url=new URL(window.location.href);
        const tempo=Number(url.searchParams.get("origem"));
        const posicao=nova.origens.findIndex(o=>o.tempo===tempo);
        setSerie(nova);setIndiceOrigem(Math.max(0,posicao));
        setModelo(m=>nova.modelos.includes(m)?m:nova.modelos[0]);
      }catch(e){if(!controle.signal.aborted)setErro((e as Error).message);}
      finally{if(!controle.signal.aborted)setCarregando(false);}
    }
    void carregar();return()=>controle.abort();
  },[id]);
  const selecionada=indice.find(s=>s.id===id)??indice[0];
  const origem=serie?.origens[indiceOrigem];
  useEffect(()=>{if(!serie||!origem||serie.id!==id)return;const url=new URL(window.location.href);url.searchParams.set("id",serie.id);url.searchParams.set("origem",String(origem.tempo));window.history.replaceState(null,"",url);},[serie,origem,id]);
  const vizinhas=useMemo(()=>serie?.origens.slice(Math.max(0,indiceOrigem-3),indiceOrigem+5)??[],[serie,indiceOrigem]);
  function selecionar(tempo:number){if(!serie)return;const i=serie.origens.findIndex(o=>o.tempo===tempo);if(i>=0)setIndiceOrigem(i);}
  function filtro(chave:"par"|"fold"|"contexto"|"seed",valor:string){
    const possiveis=indice.filter(s=>String(s[chave])===valor);
    possiveis.sort((a,b)=>["par","fold","contexto","seed"].reduce((n,k)=>n+Number(b[k as keyof IndiceSerie]===selecionada[k as keyof IndiceSerie])-Number(a[k as keyof IndiceSerie]===selecionada[k as keyof IndiceSerie]),0));
    if(possiveis[0])setId(possiveis[0].id);
  }
  if(!indice.length)return <div className="aviso">Ainda não há previsões exportadas e auditadas.</div>;
  return <><div className="filtros-explorador">{([['par','Moeda'],['fold','Período'],['contexto','Contexto'],['seed','Seed']] as const).map(([chave,rotulo])=><label key={chave}>{rotulo}<select value={String(selecionada[chave])} onChange={e=>filtro(chave,e.target.value)}>{[...new Set(indice.map(s=>s[chave]))].sort((a,b)=>String(a).localeCompare(String(b),undefined,{numeric:true})).map(v=><option value={String(v)} key={v}>{chave==='contexto'?`${Number(v)/24} ${Number(v)===24?'dia':'dias'} · ${v} candles`:v}</option>)}</select></label>)}<label>Previsão no gráfico<select value={modelo} onChange={e=>setModelo(e.target.value)}>{(serie?.modelos??selecionada.modelos).map(m=><option key={m} value={m}>{nomes[m]}</option>)}</select></label></div>
    {erro&&<p role="alert" className="aviso">{erro}</p>}{carregando&&<p role="status">Carregando a série auditada…</p>}
    {serie&&origem&&serie.id===id&&!carregando&&<><div className="barra-inspecao"><div><span className="sobretitulo">ORIGEM DA PREVISÃO · UTC</span><strong>{dataUTC(origem.tempo)}</strong><small>Resultado terminal: {dataUTC(origem.destino)} UTC</small></div><div className="controles-origem"><button onClick={()=>setIndiceOrigem(i=>Math.max(0,i-1))} disabled={indiceOrigem===0} aria-label="Previsão anterior">←</button><span>{indiceOrigem+1} / {serie.origens.length}</span><button onClick={()=>setIndiceOrigem(i=>Math.min(serie.origens.length-1,i+1))} disabled={indiceOrigem===serie.origens.length-1} aria-label="Próxima previsão">→</button><input aria-label="Buscar data e hora UTC" type="datetime-local" value={busca} onChange={e=>setBusca(e.target.value)} onInput={e=>setBusca(e.currentTarget.value)}/><button onClick={()=>{const tempo=Date.parse(busca+"Z")/1000;if(!Number.isFinite(tempo))return;const i=serie.origens.reduce((melhor,o,i)=>Math.abs(o.tempo-tempo)<Math.abs(serie.origens[melhor].tempo-tempo)?i:melhor,0);setIndiceOrigem(i);}}>Ir</button></div></div>
    <div className="painel-grafico"><div className="cotacoes"><span>{serie.par} · candles 1h</span><b>Origem {numero(origem.preco,serie.par==='XRPUSDT'?5:2)} USDT</b><b>Após 24h {numero(origem.preco_real,serie.par==='XRPUSDT'?5:2)} USDT</b><strong className={origem.retorno_real>=0?'positivo':'negativo'}>{retornoPercentual(origem.retorno_real)} observado</strong></div><GraficoRetorno serie={serie} origem={origem} modelo={modelo} selecionar={selecionar}/><p className="legenda-grafico">Os pontos escuros mostram os preços observados na origem e após 24h. A linha tracejada liga a origem à previsão terminal; <b>não representa um percurso previsto</b>. Arraste para navegar, use a roda para zoom e clique em um horário com previsão para inspecioná-lo. Candles identificados pelo fechamento UTC. Candles e volume contextualizam o mercado; a entrada dos modelos contém somente retornos horários. Gráfico com TradingView Lightweight Charts™.</p></div>
    <div className="comparacao-previsoes">{serie.modelos.map(m=>{const r=origem.previsoes[m];return <button className={m===modelo?'selecionado':''} onClick={()=>setModelo(m)} key={m} style={{borderTopColor:cores[m]}}><span>{nomes[m]}</span><strong>{retornoPercentual(r)}</strong><small>{numero(origem.preco*Math.exp(r),serie.par==='XRPUSDT'?5:2)} USDT · preço implícito</small><small>Erro absoluto de log-retorno: {numero(Math.abs(r-origem.retorno_real)*100,3)} p.p.</small></button>})}</div>
    <p className="nota">Retornos muito pequenos usam mais casas decimais para não parecerem zero. Por exemplo, 1,0e−6% significa 0,000001%. Zero exato continua aparecendo como 0,00%.</p>
    {['lstm','mamba','naive','arima'].some(m=>!serie.modelos.includes(m))&&<p className="aviso">Ainda não disponíveis neste recorte: {['lstm','mamba','naive','arima'].filter(m=>!serie.modelos.includes(m)).map(m=>nomes[m]).join(', ')}. A execução está em andamento; ausência não significa previsão zero.</p>}
    <label className="navegador-tempo">Navegar pelas origens de teste<input type="range" min={0} max={serie.origens.length-1} value={indiceOrigem} onChange={e=>setIndiceOrigem(Number(e.target.value))}/></label>
    <details><summary>Previsões próximas à origem selecionada</summary><div className="tabela-scroll"><table><thead><tr><th>Origem UTC</th>{serie.modelos.map(m=><th key={m}>{nomes[m]}</th>)}<th>Observado</th></tr></thead><tbody>{vizinhas.map(o=><tr key={o.tempo} className={o.tempo===origem.tempo?'linha-selecionada':''}><td><button onClick={()=>selecionar(o.tempo)}>{dataUTC(o.tempo)}</button></td>{serie.modelos.map(m=><td key={m}>{retornoPercentual(o.previsoes[m])}</td>)}<td>{retornoPercentual(o.retorno_real)}</td></tr>)}</tbody></table></div></details></>}
  </>;
}
