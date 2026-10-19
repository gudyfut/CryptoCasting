import assert from 'node:assert/strict';
const base = process.env.CC_URL ?? 'http://localhost:3000';
const obter = async caminho => { const resposta = await fetch(base+caminho); assert.equal(resposta.status,200,caminho); return resposta.json(); };
const indice = await obter('/api/estudo/previsoes');
assert.equal(indice.celulas.length,96); assert.equal(indice.arquivos,undefined); assert.equal(indice.fontes,undefined);
for(const [par,contexto,horizonte,fold] of [['BTCUSDT',24,1,'DB1'],['ETHUSDT',168,24,'DB2'],['BNBUSDT',24,168,'DB3'],['XRPUSDT',168,168,'DB4']]) {
  const c=indice.celulas.find(c=>c.par===par&&c.contexto===contexto&&c.horizonte===horizonte&&c.fold===fold);
  const serie=await obter(`/api/estudo/previsoes?id=${c.id}`); assert.equal(serie.observacoes.length,c.n);
  const o=serie.observacoes[0],inicio=Math.floor(o.entrada/3600)*3600,fim=inicio+7200;
  const dados=await obter(`/api/estudo/precos?par=${par}&inicio=${inicio}&fim=${fim}&resolucao=1`);
  const candle=dados.candles.find(x=>x.time===o.entrada);assert.equal(candle.open,o.precoEntrada);
}
for(const caminho of ['/api/estudo/previsoes?id=../../segredo','/api/estudo/precos?par=BTCUSDT&inicio=1704067200&fim=1704153600&resolucao=1','/api/estudo/precos?par=BTCUSDT&inicio=1672531200&fim=1672617600&resolucao=7']) assert.equal((await fetch(base+caminho)).status,400);
for(const caminho of ['/','/previsoes','/api/estudo/documentos/entregas','/api/estudo/documentos/avaliacao']) assert.equal((await fetch(base+caminho)).status,200);
console.log('API: quatro moedas, quatro folds, entrada igual ao preço bruto, bloqueio de 2024, parâmetros inválidos e documentos verificados.');
