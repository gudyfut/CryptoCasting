import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import * as echarts from 'echarts';
import sharp from 'sharp';

// Pós-processamento dos resultados; não participa de treino ou seleção.
const raiz=path.resolve(process.argv[2] ?? '');
if(!process.argv[2]) throw new Error('Informe o diretório de um ciclo consolidado.');
const resumo=JSON.parse(fs.readFileSync(path.join(raiz,'consolidacao/resumo.json'),'utf8'));
const ciclo=JSON.parse(fs.readFileSync(path.join(raiz,'ciclo.json'),'utf8'));
const registros=[],fontesExecucoes={};
for(const entrada of fs.readdirSync(raiz,{withFileTypes:true})) {
  const arquivo=path.join(raiz,entrada.name,'estado.json');
  if(!entrada.isDirectory() || !fs.existsSync(arquivo)) continue;
  const r=JSON.parse(fs.readFileSync(arquivo,'utf8'));
  if(r.status==='concluida_auditada' && r.id_ciclo===resumo.id_ciclo) {
    registros.push(r);
    fontesExecucoes[r.id]=crypto.createHash('sha256').update(fs.readFileSync(arquivo)).digest('hex');
  }
}
if(registros.length!==resumo.celulas_auditadas) throw new Error('Consolidar novamente: contagem mudou.');
const saida=path.join(raiz,'consolidacao/figuras');fs.mkdirSync(saida,{recursive:true});
const nomes=['mamba','lstm','ar1','frequencia_treino'];
const nomesExibicao={mamba:'Mamba',lstm:'LSTM',ar1:'AR(1)',frequencia_treino:'Frequências do treino'};
const cores=['#087f8c','#b66b13','#6c5595','#858585'];
const pares=ciclo.assinatura.configuracao.pares;
const contextos=ciclo.assinatura.configuracao.contextos;
const horizontes=ciclo.assinatura.configuracao.horizontes;
const totalFolds=ciclo.assinatura.configuracao.folds.length;
const titulo=`${resumo.status==='completo'?'Grade completa':'Resultados parciais'} · ${registros.length}/${resumo.celulas_esperadas} células`;
const foldsPresentes=ciclo.assinatura.configuracao.folds.filter(f=>registros.some(r=>r.celula.fold===f));
const seedsPresentes=[...new Set(registros.map(r=>r.celula.seed))].sort((a,b)=>a-b);
const proveniencia=`Desenvolvimento · períodos presentes: ${foldsPresentes.join(', ')} · seeds: ${seedsPresentes.join(', ')} · ciclo ${resumo.id_ciclo.slice(0,8)}`;
const notaGrade=resumo.status==='completo'?'Grade de desenvolvimento concluída; avaliação final permanece separada.':'Quadro parcial não permite seleção conclusiva.';
const notaCobertura=resumo.status==='completo'?`Médias entre seeds e os ${totalFolds} folds de desenvolvimento.`:'Médias dos folds disponíveis; a cobertura pode variar entre células.';
const media=xs=>xs.length?xs.reduce((a,b)=>a+b,0)/xs.length:null;
function score(r,nome) {return nome==='frequencia_treino'?r.referencia_constante.metricas_teste.log_loss:r.resultados[nome].metricas.teste.log_loss;}
function celula(par,w,h){return registros.filter(r=>r.celula.par===par && r.celula.contexto===w && r.celula.horizonte===h);}
function valor(par,w,h,nome){const rs=celula(par,w,h);const folds=[...new Set(rs.map(r=>r.celula.fold))];return media(folds.map(f=>media(rs.filter(r=>r.celula.fold===f).map(r=>score(r,nome)))));}
async function salvar(nome,opcao,largura,altura){const grafico=echarts.init(null,null,{renderer:'svg',ssr:true,width:largura,height:altura});grafico.setOption({...opcao,animation:false,graphic:[{type:'text',left:30,bottom:7,style:{text:proveniencia,fill:'#607077',font:'11px Arial'}}]});const svg=grafico.renderToSVGString();fs.writeFileSync(path.join(saida,nome),svg);await sharp(Buffer.from(svg)).png().toFile(path.join(saida,nome.replace('.svg','.png')));grafico.dispose();}
const eixos=horizontes.flatMap(h=>contextos.map(w=>[w,h]));
const grids=[],xs=[],ys=[],series=[];
pares.forEach((par,i)=>{
  grids.push({left:100,right:40,top:125+i*235,height:155});
  xs.push({gridIndex:i,type:'category',data:eixos.map(([w,h])=>{const rs=celula(par,w,h);return `H${h} · W${w}\n${new Set(rs.map(r=>r.celula.fold)).size}/${totalFolds} folds`;}),axisLabel:{fontSize:12}});
  ys.push({gridIndex:i,type:'value',name:par+' · log-loss',min:0,nameLocation:'end'});
  nomes.forEach((nome,k)=>series.push({name:nome,type:'bar',xAxisIndex:i,yAxisIndex:i,itemStyle:{color:cores[k]},data:eixos.map(([w,h])=>valor(par,w,h,nome)),barMaxWidth:36}));
});
await salvar('log_loss_por_celula.svg',{backgroundColor:'#fff',title:{text:titulo,subtext:`Menor é melhor. ${notaCobertura} ${notaGrade}`,left:35,top:20},legend:{data:nomes,formatter:n=>nomesExibicao[n],top:77},grid:grids,xAxis:xs,yAxis:ys,series},1400,125+235*pares.length);
for(const comparador of ['lstm','ar1']) {
  const rotulos=pares.flatMap(par=>horizontes.map(h=>[par,h]));const dados=[];
  rotulos.forEach(([par,h],y)=>contextos.forEach((w,x)=>{const a=valor(par,w,h,'mamba'),b=valor(par,w,h,comparador);if(a!==null && b!==null)dados.push([x,y,a-b]);}));
  const amplitude=Math.max(.01,...dados.map(x=>Math.abs(x[2])));
  await salvar(`diferenca_mamba_${comparador}.svg`,{backgroundColor:'#fff',title:{text:`Mamba menos ${nomesExibicao[comparador]} · log-loss`,subtext:`${titulo}\n${notaCobertura}\nNegativo favorece Mamba. Sem número = não executado. Não são testes independentes por célula.`,left:30,top:20},grid:{left:180,right:100,top:120,bottom:120},xAxis:{type:'category',data:contextos.map(w=>`Contexto ${w}h`),splitArea:{show:true}},yAxis:{type:'category',inverse:true,data:rotulos.map(([p,h])=>`${p} · H${h}h`),splitArea:{show:true}},visualMap:{min:-amplitude,max:amplitude,orient:'horizontal',left:'center',bottom:25,inRange:{color:['#167d8d','#ffffff','#c25038']},precision:3},series:[{type:'heatmap',data:dados,label:{show:true,formatter:p=>p.value[2].toFixed(4)},itemStyle:{borderColor:'#fff',borderWidth:2}}]},850,790);
}
const arquivos=fs.readdirSync(saida).filter(x=>x.endsWith('.svg') || x.endsWith('.png'));
fs.writeFileSync(path.join(saida,'manifesto.json'),JSON.stringify({id_ciclo:resumo.id_ciclo,status:resumo.status,celulas:registros.length,criado_utc:new Date().toISOString(),fonte_sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(raiz,'consolidacao/resumo.json'))).digest('hex'),gerador_sha256:crypto.createHash('sha256').update(fs.readFileSync(new URL(import.meta.url))).digest('hex'),fontes_execucoes:fontesExecucoes,arquivos},null,2));
console.log(saida);
