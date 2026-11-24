'use client';
import { useState } from 'react';
import Grafico, { cores } from './Grafico';
import { formato, sinal, metrica, objeto, numero, type DadosPanorama, type Etapa, type Registro } from '@/lib/panorama-tipos';

type Intervalo = { nome: string; media: number; baixo: number; alto: number; nivel: string };
function intervalos(etapa: Etapa, pub: Registro, fase: string, dias: string): Intervalo[] {
  const c = objeto(objeto(pub.contrastes)[fase]);
  if (etapa.id === 'entradas') return Object.entries(c).map(([nome,v]) => {
    const p = objeto(v), limites = objeto(objeto(p.intervalos)[dias]).ic_bonferroni_98_333 as number[];
    return { nome: ({ crua_menos_atual: 'B crua − A relativa', niveis_padronizados_menos_atual: 'C padronizada − A relativa', crua_menos_niveis_padronizados: 'B crua − C padronizada' } as Record<string,string>)[nome] ?? nome.replaceAll('_',' '), media: Number(p.diferenca_mse), baixo: limites[0], alto: limites[1], nivel:'98,33%' };
  });
  if (etapa.id === 'blocos') {
    const l = objeto(c.ic95_seeds_e_tempo)[dias] as number[];
    return l ? [{ nome:'Huber − MSE', media:Number(c.diferenca_mse_huber_menos_mse), baixo:l[0], alto:l[1], nivel:'95%' }] : [];
  }
  if (etapa.id === 'taxa') return Object.entries(c).map(([nome,v])=>{
    const p=objeto(v), l=objeto(p.ic9875_bonferroni_quatro)[dias] as number[];
    return { nome:`Estado${nome} · taxa menor − original`, media:Number(p.diferenca_mse_candidata_menos_referencia), baixo:l[0], alto:l[1], nivel:'98,75%' };
  });
  if (Array.isArray(pub.contrastes)) {
    const p=objeto(pub.contrastes[0]), itens=p.intervalos as Registro[];
    const l=itens?.find(x=>x.dias===Number(dias));
    return l ? [{ nome:etapa.id==='retornos'?'Mamba − LSTM':'Candidata − anterior', media:Number(p.diferenca_mse??p.diferenca), baixo:Number(l.inferior), alto:Number(l.superior), nivel:'95%' }] : [];
  }
  const nomes:Record<string,string>={ r0:'mamba_menos_naive', estado8:'estado8_pareadas_menos_estado16_pareadas', estado32:'estado32_tres_menos_estado16_tres', estado64:'estado64_tres_menos_estado16_tres', complemento:'estado16_seis_menos_estado8_seis', crypto:'cryptomamba_seis_menos_estado16_taxa0002', adamw:'adamw_seis_menos_adam_seis', dinamica:'scheduler_seis_menos_mamba16_seis', huber:'huber_seis_menos_mamba16_seis' };
  const p=objeto(c[nomes[etapa.id]]), l=objeto(p.ic95)[dias] as number[];
  return l ? [{ nome:etapa.id==='r0'?'Mamba − Naive':etapa.id==='complemento'?'Estado16 − estado8':'Candidata − referência', media:Number(p.diferenca_mse_a_menos_b), baixo:l[0], alto:l[1], nivel:'95%' }] : [];
}

function Faixas({ itens }: { itens:Intervalo[] }) {
  const limite=Math.max(...itens.flatMap(x=>[Math.abs(x.baixo),Math.abs(x.alto)]))*1.12;
  const x=(v:number)=>50+v/limite*46;
  return <div className="faixas"><div className="faixa-direcoes"><span>← Menor erro da candidata</span><span>Maior erro da candidata →</span></div>{itens.map(i=><div className="faixa-item" key={i.nome}><div><strong>{i.nome}</strong><span className={i.alto<0?'resultado-favoravel':'resultado-neutro'}>{i.alto<0?'Favorável à candidata':i.baixo>0?'Favorece a referência':'Inclui zero · inconclusivo'}</span></div><svg viewBox="0 0 600 46" role="img" aria-label={`${i.nome}: diferença ${i.media}, intervalo de ${i.baixo} a ${i.alto}`}><rect x="0" width="300" height="46" fill="#edf4f0"/><rect x="300" width="300" height="46" fill="#faf0e9"/><line x1="300" x2="300" y1="0" y2="46" stroke="#727b81" strokeDasharray="3 3"/><line x1={x(i.baixo)*6} x2={x(i.alto)*6} y1="23" y2="23" stroke="#34445c" strokeWidth="2"/><line x1={x(i.baixo)*6} x2={x(i.baixo)*6} y1="16" y2="30" stroke="#34445c"/><line x1={x(i.alto)*6} x2={x(i.alto)*6} y1="16" y2="30" stroke="#34445c"/><circle cx={x(i.media)*6} cy="23" r="6" fill={i.alto<0?'#24796f':'#34445c'}/></svg><p>Diferença <b>{sinal(i.media*1e6,3)}</b> · IC {i.nivel} [{sinal(i.baixo*1e6,3)}; {sinal(i.alto*1e6,3)}] · MSE ×10⁶</p></div>)}</div>;
}

export default function Resultados({ etapa, dados }: { etapa:Etapa; dados:DadosPanorama }) {
  const [fase,setFase]=useState(etapa.primaria??'teste');
  const [dias,setDias]=useState('14');
  const [cenario,setCenario]=useState('base');
  const [politica,setPolitica]=useState('smart');
  const [bloco,setBloco]=useState('B1');
  const pub=dados.publicacoes[etapa.publicacao??'']??{};
  const revisado=dados.custos_vigentes?.situacao==='concluido_conferido';
  if (dados.custos_vigentes?.situacao==='divergente') return <p role="status">Reavaliação de custos com integridade pendente.</p>;
  if (etapa.visual==='carteira'||etapa.visual==='publico') return <Financeiro etapa={etapa} pub={pub} revisado={revisado}/>;
  const grupos=etapa.grupos??[];
  if (!grupos.length) return <div className="vazio"><h3>Etapa de preparação</h3><p>{etapa.resumo}</p><p>Consulte o experimento e suas fontes para ver o escopo. Não há um MSE comparável a acrescentar aqui.</p></div>;
  const linhas=grupos.map(g=>({...g, metricas:metrica(pub,g.chave,fase)}));
  const faixas=intervalos(etapa,pub,fase,dias);
  const porBloco=objeto(pub.medias_por_bloco);
  const amplo=!!pub.medias_globais;
  const naive=numero(linhas[0]?.metricas.mse_naive);
  const barras=linhas.map(l=>({ nome:l.nome, mse:numero(l.metricas.mse) }));
  if (amplo && naive!==null) barras.push({ nome:'Naive · retorno zero', mse:naive });
  const base=numero(linhas[0]?.metricas.mse);
  const financeiro=(b:string,chave:string)=>chave==='comprar_manter'
    ?objeto(objeto(pub.benchmarks_blocos)[`${b}/benchmark/benchmark/comprar_manter/${cenario}`])
    :objeto(objeto(objeto(pub.medias_operacionais_por_bloco)[b])[`${chave}/${politica}/${cenario}`]);
  const gruposFinanceiros=[...grupos,{chave:'comprar_manter',nome:'Comprar e manter'}];
  return <div className="resultados-conteudo">
    <section className="painel"><div className="cabecalho-painel"><div><p className="eyebrow">ERRO DE PREVISÃO · MENOR É MELHOR</p><h2>Erro de previsão</h2></div>{!Array.isArray(pub.modelos)&&<div className="segmentado" aria-label="Partição avaliada">{(['validacao','teste'] as const).map(f=><button key={f} aria-pressed={fase===f} onClick={()=>setFase(f)}>{f==='validacao'?'Validação':'Teste'}</button>)}</div>}</div>
      <p className="descricao-painel">{amplo?'Média com peso igual entre quatro blocos e oito seeds por bloco.':'Médias das métricas individuais no recorte identificado abaixo.'} {fase===etapa.primaria?'Esta é a partição do critério principal.':'Recorte complementar; não altera o critério principal.'}</p>
      <Grafico rotulo="Comparação dos erros médios MSE" altura={Math.max(240,barras.length*49)} opcoes={{ grid:{left:8,right:78,top:16,bottom:32,containLabel:true}, tooltip:{trigger:'axis',axisPointer:{type:'shadow'},valueFormatter:v=>`${formato(Number(v),3)} (MSE ×10⁶)`}, xAxis:{type:'value',name:'MSE ×10⁶',nameLocation:'middle',nameGap:23,splitLine:{lineStyle:{color:'#e9eae5'}},min:0}, yAxis:{type:'category',inverse:true,data:barras.map(x=>x.nome),axisTick:{show:false},axisLine:{show:false},axisLabel:{color:'#34445c',fontSize:12,width:185,overflow:'break'}}, series:[{type:'bar',barMaxWidth:22,data:barras.map((b,i)=>({value:b.mse===null?null:b.mse*1e6,itemStyle:{color:b.nome.startsWith('Naive')?'#aaa592':cores[i%cores.length],borderRadius:[0,4,4,0]}})),label:{show:true,position:'right',formatter:p=>formato(Number(p.value),3)}}]}}/>
      <p className="nota">Multiplicar o MSE por um milhão apenas facilita a leitura. 618,545 no gráfico corresponde a 0,000618545. Não é porcentagem de erro ou de acerto.</p>
      <div className="tabela-rolavel"><table><caption>Métricas publicadas · {fase==='teste'?'teste':'validação'}</caption><thead><tr><th>Versão</th><th>MSE ↓</th><th>Variação vs. 1ª</th><th>MAE ×100 ↓</th><th>Acerto balanceado</th></tr></thead><tbody>{linhas.map(l=>{const mse=numero(l.metricas.mse),mae=numero(l.metricas.mae),acerto=numero(l.metricas.acerto_balanceado_direcional);return <tr key={l.chave}><th>{l.nome}</th><td>{mse===null?'Indisponível':formato(mse,9)}</td><td>{mse!==null&&base!==null?`${sinal((mse/base-1)*100,3)}%`:'—'}</td><td>{mae===null?'—':formato(mae*100,4)}</td><td>{acerto===null?'—':formato(acerto*100,2)+'%'}</td></tr>})}</tbody></table></div>
      <p className="nota">MAE×100 está em pontos de log-retorno, aproximadamente pontos percentuais para mudanças pequenas. “—” indica métrica não consolidada neste resumo, nunca zero.</p>
    </section>
    {!!faixas.length&&<section className="painel"><div className="cabecalho-painel"><div><p className="eyebrow">TAMANHO DO EFEITO E INCERTEZA</p><h2>Diferença e intervalo de confiança</h2></div><label className="filtro-pequeno">Bloco temporal<select value={dias} onChange={e=>setDias(e.target.value)}><option value="7">7 dias · sensibilidade</option><option value="14">14 dias · principal</option><option value="28">28 dias · sensibilidade</option></select></label></div><p className="descricao-painel">O ponto é a diferença média; a linha mostra o intervalo. Se atravessa o zero, o procedimento ainda admite melhora e piora.</p><Faixas itens={faixas}/><p className="nota">{amplo?'Reamostragem pareada de seeds e dias, com peso igual entre os quatro blocos.':'Intervalos temporais condicionais aos modelos ajustados; não incorporam toda a seleção histórica.'} {etapa.id==='entradas'?'Ajuste de Bonferroni para três contrastes.':etapa.id==='taxa'?'Ajuste de Bonferroni para quatro contrastes.':'Sem interpretar o intervalo como probabilidade de a hipótese ser verdadeira.'}</p></section>}
    {amplo&&<section className="painel"><div className="cabecalho-painel"><div><p className="eyebrow">ESTABILIDADE TEMPORAL</p><h2>Resultados por semestre</h2></div><span className="etiqueta">Clique em uma barra</span></div><p className="descricao-painel">Mudança relativa do MSE frente a {grupos[0].nome}. Abaixo de zero indica menor erro. Cada barra resume oito seeds.</p><Grafico rotulo="Diferença de erro nos quatro semestres" altura={290} aoClicar={e=>setBloco(`B${e.dataIndex+1}`)} opcoes={{tooltip:{trigger:'axis',valueFormatter:v=>`${sinal(Number(v),3)}%`},legend:{bottom:0},grid:{left:55,right:20,top:20,bottom:65},xAxis:{type:'category',data:['B1 · 2024/1','B2 · 2024/2','B3 · 2025/1','B4 · 2025/2']},yAxis:{type:'value',axisLabel:{formatter:'{value}%'},splitLine:{lineStyle:{color:'#e9eae5'}}},series:grupos.slice(1).map((g,i)=>({name:g.nome,type:'bar',barMaxWidth:36,itemStyle:{color:cores[i+1]},data:['B1','B2','B3','B4'].map(b=>{const m=objeto(objeto(porBloco[b])[fase]);return (Number(objeto(m[g.chave]).mse)/Number(objeto(m[grupos[0].chave]).mse)-1)*100}),markLine:{symbol:'none',label:{show:false},data:[{yAxis:0}],lineStyle:{color:'#60717e'}}}))}}/>
      <div className="bloco-selecionado"><div className="segmentado">{['B1','B2','B3','B4'].map(b=><button key={b} aria-pressed={b===bloco} onClick={()=>setBloco(b)}>{b}</button>)}</div><p><b>{bloco} em detalhe.</b> {etapa.id==='entradas'&&bloco==='B4'?'Aqui se concentra a melhora da entrada crua. Previsões de pequena amplitude ajudam a interpretar o resultado.':'As diferenças entre semestres ajudam a avaliar se a conclusão depende do regime de mercado.'}</p></div>
      <div className="resumo-bloco">{grupos.map(g=>{const m=objeto(objeto(objeto(porBloco[bloco])[fase])[g.chave]);return <div key={g.chave}><small>{g.nome}</small><b>{formato(Number(m.mse)*1e6,3)}</b><span>MSE ×10⁶ · dispersão ±{formato(Number(m.mse_desvio_seeds)*1e6,3)}</span></div>})}</div><p className="nota">A dispersão acima é o desvio-padrão entre seeds, não um intervalo de confiança.</p>
    </section>}
    {amplo&&<section className="painel"><div className="cabecalho-painel"><div><p className="eyebrow">AVALIAÇÃO FINANCEIRA SECUNDÁRIA</p><h2>Resultado financeiro no teste</h2></div></div><p className="descricao-painel">Carteiras dos períodos de teste B1–B4, independentemente da seleção de validação acima. Taxas são cobradas na compra e na venda. Slippage representa uma execução a preço menos favorável que o preço de referência.</p><div className="controles-inline"><label>Política<select value={politica} onChange={e=>setPolitica(e.target.value)}><option value="smart">Smart · mantém posição</option><option value="diaria24">Diária · encerra em 24h</option></select></label><label>Custos por lado<select value={cenario} onChange={e=>setCenario(e.target.value)}><option value="ideal">Sem custos</option><option value="base">{revisado?'0,10% taxa +0,01% slippage':'0,10% taxa +0,05% slippage'}</option><option value="agravado">{revisado?'0,20% taxa +0,02% slippage':'0,20% taxa +0,10% slippage'}</option></select></label></div><Grafico rotulo="Retornos das carteiras separadas por bloco" opcoes={{tooltip:{trigger:'axis',valueFormatter:v=>`${sinal(Number(v),2)}%`},legend:{bottom:0},grid:{left:55,right:20,top:20,bottom:65},xAxis:{type:'category',data:['B1 · 2024/1','B2 · 2024/2','B3 · 2025/1','B4 · 2025/2']},yAxis:{type:'value',axisLabel:{formatter:'{value}%'},splitLine:{lineStyle:{color:'#e9eae5'}}},series:gruposFinanceiros.map((g,i)=>({type:'bar',name:g.nome,barMaxWidth:28,itemStyle:{color:cores[i]},data:['B1','B2','B3','B4'].map(b=>Number(financeiro(b,g.chave).retorno_liquido)*100)}))}}/>
      <div className="tabela-rolavel"><table><caption>Carteiras de {bloco} · {politica==='smart'?'Smart':'Diária 24h'} · custos {cenario}</caption><thead><tr><th>Versão</th><th>Retorno</th><th>Exposição média</th><th>Queda máxima média</th><th>Seeds positivas</th></tr></thead><tbody>{gruposFinanceiros.map(g=>{const m=financeiro(bloco,g.chave);return <tr key={g.chave}><th>{g.nome}</th><td>{sinal(Number(m.retorno_liquido)*100)}%</td><td>{formato(Number(m.exposicao_media)*100)}%</td><td>{formato(Number(m.drawdown_minuto_close)*100)}%</td><td>{g.chave==='comprar_manter'?'Referência única':`${String(m.seeds_lucrativas)} /8`}</td></tr>})}</tbody></table></div><p className="nota">Cada semestre começa com 10.000 USDT em uma carteira independente. Não somar os retornos nem conectá-los como uma única carteira. Caixa rende 0%; não operar não é obter lucro. Médias de carteiras individuais, não ensemble.</p>
    </section>}
  </div>;
}

function Financeiro({etapa,pub,revisado}:{etapa:Etapa;pub:Registro;revisado:boolean}) {
  const [custo,setCusto]=useState('base');
  const [fase,setFase]=useState('teste');
  const publico=etapa.visual==='publico';
  const linhas=publico?['vanilla','smart','comprar_manter'].map((k)=>{
    const m=objeto(objeto(objeto(objeto(pub.series).cmamba_v_test)[k])[({ideal:'ideal',base:'taxa_010_slip_005',agravado:'taxa_020_slip_010'} as Record<string,string>)[custo]]);
    return { nome:({vanilla:'Vanilla',smart:'Smart',comprar_manter:'Comprar e manter'} as Record<string,string>)[k], valor:Number(m.retorno_pct) };
  }):['smart','vanilla','diaria24'].map(k=>{
    const porCusto=objeto(objeto(objeto(pub.medias)[fase])[custo]);
    const m=objeto(objeto(porCusto[k]).mamba16_seis);
    return {nome:({smart:'Smart · mantém posição',vanilla:'Vanilla · mantém posição',diaria24:'Diária · encerra em 24h'} as Record<string,string>)[k],valor:Number(m.retorno_liquido)*100};
  });
  if(!publico){const b=objeto(objeto(objeto(objeto(pub.medias)[fase])[custo]).benchmarks);linhas.push({nome:'Comprar e manter',valor:Number(objeto(b.comprar_manter).retorno_liquido)*100},{nome:'Caixa',valor:0});}
  return <section className="painel"><div className="cabecalho-painel"><div><p className="eyebrow">SIMULAÇÕES PRESERVADAS</p><h2>Retorno por política e custo</h2></div></div><p className="descricao-painel">{publico?'Checkpoint público com volume · amostra pública de 2023–2024.':'Mamba16 · média de seis carteiras individuais. Mesmas previsões; políticas diferentes.'}</p><div className="controles-inline">{!publico&&<label>Período<select value={fase} onChange={e=>setFase(e.target.value)}><option value="teste">2025 · teste retrospectivo</option><option value="validacao">2024 · validação</option></select></label>}<label>Custos por lado<select value={custo} onChange={e=>setCusto(e.target.value)}><option value="ideal">Sem custos</option><option value="base">{revisado?'0,10% taxa +0,01% slippage':'0,10% taxa +0,05% slippage'}</option><option value="agravado">{revisado?'0,20% taxa +0,02% slippage':'0,20% taxa +0,10% slippage'}</option></select></label></div><Grafico rotulo="Retorno por política e cenário de custos" altura={Math.max(260,linhas.length*58)} opcoes={{grid:{left:5,right:65,top:16,bottom:30,containLabel:true},tooltip:{trigger:'axis',valueFormatter:v=>`${sinal(Number(v))}%`},xAxis:{type:'value',axisLabel:{formatter:'{value}%'},splitLine:{lineStyle:{color:'#e9eae5'}}},yAxis:{type:'category',inverse:true,data:linhas.map(l=>l.nome),axisTick:{show:false},axisLine:{show:false}},series:[{type:'bar',barMaxWidth:26,label:{show:true,position:'right',formatter:p=>`${sinal(Number(p.value))}%`},data:linhas.map((l,i)=>({value:Number.isFinite(l.valor)?l.valor:null,itemStyle:{color:i<2?cores[i]:'#aaa592'}}))}]}}/><div className="tabela-rolavel"><table><caption>Retorno simulado</caption><tbody>{linhas.map(l=><tr key={l.nome}><th>{l.nome}</th><td>{Number.isFinite(l.valor)?`${sinal(l.valor)}%`:'Não disponível'}</td></tr>)}</tbody></table></div><div className="insight"><span>↳</span><p>{publico?'Mesmo com lucro, Smart ficou abaixo de comprar e manter no cenário base. O resultado do artigo e o nosso teste usam períodos diferentes; o gráfico não compara a qualidade dos dois modelos.':'Trocar a política pode mudar completamente o saldo sem alterar um único peso da rede. O desempenho da previsão e a regra de negociação precisam ser discutidos separadamente.'}</p></div><p className="nota">Sensibilidade de custos, sem novas simulações nesta interface. Não é uma reprodução de conta Binance, livro de ofertas ou execução real.</p></section>;
}
