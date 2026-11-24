'use client';
import { useEffect, useState } from 'react';
import Grafico from './Grafico';
import { formato, sinal, type DadosPanorama, type Etapa, type SerieIndice, type SerieReal } from '@/lib/panorama-tipos';

function nomeModelo(s:SerieIndice) {
  const nomes:Record<string,string>={ r0:s.modelo==='mamba'?'Mamba 16 · R0':s.modelo==='lstm'?'LSTM · R0':s.modelo==='naive'?'Naive · zero':'ARIMA', complemento:'Mamba 16 · complemento', estado8:'Mamba 8', estado32:'Mamba 32', estado64:'Mamba 64', crypto:'CryptoMamba · Adam', adamw:'CryptoMamba · AdamW', dinamica:'Mamba 16 · taxa dinâmica', huber:'Mamba 16 · Huber', blocos:s.modelo==='mse'?'A · Relativa / MSE':'Relativa / Huber', entradas:s.modelo==='crua'?'B · OHLCV cru':'C · Níveis padronizados', taxa:`${s.modelo.split('_')[0].replace('estado','Estado ')} · taxa 0,0001` };
  return nomes[s.ciclo]??s.modelo;
}
const dataISO=(t:number)=>new Date(t*1000).toISOString().slice(0,10);
const dataCurta=(t:number)=>new Date(t*1000).toLocaleDateString('pt-BR',{day:'2-digit',month:'short',timeZone:'UTC'});
export default function Previsoes({etapa,dados}:{etapa:Etapa;dados:DadosPanorama}) {
  const indice=dados.series.filter(s=>etapa.exemplos?.includes(s.ciclo)&&(etapa.id!=='entradas'||s.ciclo!=='blocos'||s.modelo==='mse'));
  if(!indice.length) return <div className="vazio"><span className="numero-conceito">↗</span><h3>Previsões indisponíveis nesta etapa.</h3><p>As fontes preservadas registram {etapa.categoria.toLowerCase()}. O explorador de previsões está disponível nas rodadas OHLCV de treinamento e nas comparações em blocos.</p></div>;
  return <Explorador key={etapa.id} indice={indice}/>;
}
function Explorador({indice}:{indice:SerieIndice[]}) {
  const primeira=indice.find(s=>s.seed===42&&(s.modelo==='mse'||s.modelo==='mamba'))??indice.find(s=>s.seed===42)??indice[0];
  const [bloco,setBloco]=useState(primeira.bloco);
  const [modelo,setModelo]=useState(`${primeira.ciclo}/${primeira.modelo}`);
  const [seed,setSeed]=useState(String(primeira.seed??'sem'));
  const [posicao,setPosicao]=useState(0);
  const [escala,setEscala]=useState('retorno');
  const [janela,setJanela]=useState(30);
  const [resposta,setResposta]=useState<{id:string; serie?:SerieReal; erro?:string}>();
  const modelos=[...new Map(indice.filter(s=>s.bloco===bloco).map(s=>[`${s.ciclo}/${s.modelo}`,nomeModelo(s)])).entries()];
  const grupo=indice.filter(s=>s.bloco===bloco&&`${s.ciclo}/${s.modelo}`===modelo).sort((a,b)=>(a.seed??0)-(b.seed??0));
  const atual=grupo.find(s=>String(s.seed??'sem')===seed)??grupo[0]??indice[0];
  const id=atual.id;
  useEffect(()=>{
    const controlador=new AbortController();
    fetch(`/api/panorama/serie?id=${id}`,{signal:controlador.signal}).then(async r=>{const j=await r.json();if(!r.ok)throw new Error(j.erro??'Não foi possível carregar a série.');return j as SerieReal;}).then(serie=>setResposta({id,serie})).catch(e=>{if(e.name!=='AbortError')setResposta({id,erro:e.message});});
    return ()=>controlador.abort();
  },[id]);
  const serie=resposta?.id===id?resposta.serie:undefined;
  const erro=resposta?.id===id?resposta.erro:undefined;
  const ponto=serie?.pontos[Math.min(posicao,serie.pontos.length-1)];
  const inicio=Math.max(0,Math.min(posicao-Math.floor(janela/2),(serie?.pontos.length??0)-janela));
  const trecho=serie?.pontos.slice(inicio,inicio+janela)??[];
  function escolherData(valor:string){
    const i=serie?.pontos.findIndex(p=>dataISO(p[0])===valor)??-1;
    if(i>=0)setPosicao(i);
  }
  function csv(){
    if(!serie)return;
    const texto=['origem_utc,destino_utc,preco_origem_usdt,preco_real_24h_usdt,alvo_log,previsao_log',...serie.pontos.map(p=>[new Date(p[0]*1000).toISOString(),new Date((p[0]+86400)*1000).toISOString(),...p.slice(1)].join(','))].join('\n');
    const url=URL.createObjectURL(new Blob([texto],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download=`${atual.ciclo}_${atual.celula}_exemplos_diarios.csv`;a.click();URL.revokeObjectURL(url);
  }
  return <div className="previsoes-conteudo"><section className="painel"><div className="cabecalho-painel"><div><p className="eyebrow">PREVISÕES DE TESTE</p><h2>Previsões e valores observados</h2></div><button className="botao texto" onClick={csv} disabled={!serie}>Baixar exemplos CSV ↓</button></div><p className="descricao-painel">Selecione um modelo e uma origem. O primeiro exemplo usa a seed 42 por convenção, sem escolha por desempenho.</p>
    <div className="filtros-previsao"><label>Período<select value={bloco} onChange={e=>{setBloco(e.target.value);setPosicao(0);}}>{[...new Set(indice.map(s=>s.bloco))].map(b=><option key={b} value={b}>{({B1:'B1 · 1º semestre 2024',B2:'B2 · 2º semestre 2024',B3:'B3 · 1º semestre 2025',B4:'B4 · 2º semestre 2025','2025':'2025 · divisão fixa'} as Record<string,string>)[b]}</option>)}</select></label><label>Modelo<select value={modelo} onChange={e=>{setModelo(e.target.value);setPosicao(0);}}>{modelos.map(([k,n])=><option key={k} value={k}>{n}</option>)}</select></label><label>Seed<select value={String(atual.seed??'sem')} onChange={e=>{setSeed(e.target.value);setPosicao(0);}}>{grupo.map(s=><option key={s.id} value={String(s.seed??'sem')}>{s.seed??'Sem treino'}</option>)}</select></label></div>
    {erro?<div className="aviso" role="alert">{erro}</div>:!serie||!ponto?<div className="carregando-grafico" role="status">Conferindo e carregando a série real…</div>:<>
      <div className="origem-controles"><label>Origem da previsão · 00h UTC<input type="date" value={dataISO(ponto[0])} min={dataISO(serie.pontos[0][0])} max={dataISO(serie.pontos.at(-1)![0])} onInput={e=>escolherData(e.currentTarget.value)} onChange={e=>escolherData(e.target.value)} onBlur={e=>escolherData(e.target.value)}/></label><div className="segmentado"><button aria-pressed={escala==='retorno'} onClick={()=>setEscala('retorno')}>Retorno %</button><button aria-pressed={escala==='preco'} onClick={()=>setEscala('preco')}>Preço em 24h</button></div><label>Janela visível<select value={janela} onChange={e=>setJanela(Number(e.target.value))}><option value="14">14 origens</option><option value="30">30 origens</option><option value="90">90 origens</option></select></label></div>
      <Grafico rotulo={escala==='retorno'?'Retornos previstos e observados em origens diárias':'Preços terminais previstos e observados, alinhados à origem da previsão'} altura={340} aoClicar={e=>setPosicao(inicio+e.dataIndex)} opcoes={{tooltip:{trigger:'axis',valueFormatter:v=>escala==='retorno'?`${sinal(Number(v),3)}%`:`${formato(Number(v))} USDT`},legend:{bottom:0},grid:{left:65,right:20,top:22,bottom:70},xAxis:{type:'category',data:trecho.map(p=>dataCurta(p[0])),boundaryGap:false,axisLabel:{color:'#73808c'}},yAxis:{type:'value',scale:escala==='preco',axisLabel:{formatter:v=>escala==='retorno'?`${v}%`:`${Number(v)/1000} mil`},splitLine:{lineStyle:{color:'#e9eae5'}}},series:[{name:'Observado em 24h',type:'line',symbolSize:5,showSymbol:true,lineStyle:{width:2,color:'#34445c'},itemStyle:{color:'#34445c'},data:trecho.map(p=>escala==='retorno'?Math.expm1(p[3])*100:p[2]),markLine:{symbol:'none',lineStyle:{color:'#bdad93',type:'dashed'},label:{show:false},data:[{xAxis:dataCurta(ponto[0])}]}},{name:'Previsto em 24h',type:'line',showSymbol:true,symbolSize:5,lineStyle:{width:2.5,color:'#de7558'},itemStyle:{color:'#de7558'},data:trecho.map(p=>escala==='retorno'?Math.expm1(p[4])*100:p[1]*Math.exp(p[4]))},{name:'Naive · sem mudança',type:'line',showSymbol:false,lineStyle:{type:'dashed',width:1,color:'#a6a38f'},itemStyle:{color:'#a6a38f'},data:trecho.map(p=>escala==='retorno'?0:p[1])}]}}/>
      <div className="navegacao-origem"><button className="botao pequeno secundario" disabled={posicao===0} onClick={()=>setPosicao(Math.max(0,posicao-1))}>← Origem anterior</button><input aria-label="Percorrer origens da previsão" type="range" min="0" max={serie.pontos.length-1} value={posicao} onChange={e=>setPosicao(Number(e.target.value))}/><button className="botao pequeno secundario" disabled={posicao===serie.pontos.length-1} onClick={()=>setPosicao(Math.min(serie.pontos.length-1,posicao+1))}>Próxima origem →</button></div>
      <div className="previsao-cartoes"><div><small>PREÇO CONHECIDO · {dataCurta(ponto[0])}</small><b>{formato(ponto[1])}<span> USDT</span></b></div><div className="previsto"><small>MODELO · DAQUI A 24H</small><b>{sinal(Math.expm1(ponto[4])*100,3)}%</b><span>{formato(ponto[1]*Math.exp(ponto[4]))} USDT</span></div><div><small>OBSERVADO · {dataCurta(ponto[0]+86400)}</small><b>{sinal(Math.expm1(ponto[3])*100,3)}%</b><span>{formato(ponto[2])} USDT</span></div></div>
      <div className="insight"><span>↳</span><p>{Math.sign(ponto[3])===Math.sign(ponto[4])?'O modelo acertou o sinal neste exemplo. Isso não basta para acertar a magnitude.':'O sinal da previsão não coincidiu com o movimento observado neste exemplo.'} O desvio em retorno simples foi de <b>{formato(Math.abs(Math.expm1(ponto[4])-Math.expm1(ponto[3]))*100,3)} pontos percentuais</b>. Um exemplo ilustra o comportamento; a conclusão usa todas as origens.</p></div>
      <p className="nota">Pontos do gráfico são previsões separadas, emitidas às 00h UTC. As linhas apenas ligam exemplos; não são uma trajetória prevista durante o dia. O preço observado futuro é mostrado somente para avaliação. {atual.n} origens diárias exibíveis; MSE publicado usa {formato(atual.n_horario,0)} origens horárias.</p>
    </>}
  </section>{serie&&serie.aprendizagem.length>0&&<section className="painel"><div className="cabecalho-painel"><div><p className="eyebrow">O TREINAMENTO DESTE MODELO</p><h2>Seleção da época de treinamento</h2></div><span className="etiqueta">Época {serie.epoca_selecionada}</span></div><p className="descricao-painel">A escolha usa o menor MSE de validação. O teste não escolhe o checkpoint.</p><Grafico rotulo="MSE de validação ao longo das épocas, com checkpoint selecionado" altura={240} opcoes={{tooltip:{trigger:'axis',valueFormatter:v=>`${formato(Number(v),3)} MSE ×10⁶`},grid:{left:60,right:25,top:20,bottom:40},xAxis:{type:'category',name:'Época',data:serie.aprendizagem.map(e=>String(e.epoca))},yAxis:{type:'value',scale:true,name:'MSE ×10⁶',splitLine:{lineStyle:{color:'#e9eae5'}}},series:[{type:'line',data:serie.aprendizagem.map(e=>e.mse_validacao*1e6),lineStyle:{color:'#24796f',width:2},itemStyle:{color:'#24796f'},markLine:{symbol:'none',data:[{xAxis:String(serie.epoca_selecionada)}],label:{formatter:'Selecionada'},lineStyle:{color:'#de7558',type:'dashed'}}}]}}/><p className="nota">Curva de validação na escala real do alvo. O eixo vertical é ampliado para mostrar a variação; não representa o erro começando em zero.</p></section>}</div>;
}
