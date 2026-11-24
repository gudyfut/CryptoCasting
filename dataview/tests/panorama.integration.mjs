import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import { createHash } from 'node:crypto';
const dados=JSON.parse(await fs.readFile('src/data/panorama.json','utf8'));
const base=process.env.PORTAL_URL??'http://127.0.0.1:3000';
test('API entrega as 205 séries exatas e rejeita IDs desconhecidos',async()=>{
  for(let i=0;i<dados.series.length;i+=10)await Promise.all(dados.series.slice(i,i+10).map(async s=>{const r=await fetch(`${base}/api/panorama/serie?id=${s.id}`);assert.equal(r.status,200);const bytes=Buffer.from(await r.arrayBuffer());assert.equal(createHash('sha256').update(bytes).digest('hex'),s.id);}));
  for(const id of ['../../AGENTS.md','0'.repeat(64),'__proto__'])assert.equal((await fetch(`${base}/api/panorama/serie?id=${encodeURIComponent(id)}`)).status,404);
});
test('Evidências são permitidas por lista explícita; a página antiga redireciona',async()=>{
  const fonte='docs/resultados_entradas_niveis.md';
  const r=await fetch(`${base}/api/panorama/fonte?caminho=${encodeURIComponent(fonte)}`);assert.equal(r.status,200);assert.equal(r.headers.get('x-source-sha256'),dados.fontes[fonte]);
  assert.equal(createHash('sha256').update(Buffer.from(await r.arrayBuffer())).digest('hex'),dados.fontes[fonte]);
  for(const f of ['../../AGENTS.md','AGENTS.md','dados/segredo.json'])assert.equal((await fetch(`${base}/api/panorama/fonte?caminho=${encodeURIComponent(f)}`)).status,404);
  const antigo=await fetch(`${base}/previsoes`,{redirect:'manual'});assert.ok([307,308].includes(antigo.status));assert.equal(antigo.headers.get('location'),'/?etapa=entradas&aba=previsoes');
});
test('Visão geral, fases recentes e fontes preservam resultados e navegação direta',async()=>{
  const inicio=await (await fetch(base)).text();
  assert.match(inicio,/O que testamos/);
  assert.match(inicio,/A mesma receita em ETH, BNB e XRP/);
  assert.match(inicio,/Recuperar a contribuição do Mamba/);
  for(const [id,trecho] of [['padronizacao-diaria','O QUE APRENDEMOS'],['sem-penalizacao','Retiramos somente'],['outras-moedas','Retorno líquido']]){
    const r=await fetch(`${base}/?etapa=${id}`);assert.equal(r.status,200);assert.ok((await r.text()).includes(trecho));
  }
  const resumo=await (await fetch(`${base}/?vista=sintese`)).text();
  assert.match(resumo,/A evolução diária em BTC/);
  const fonte='dados/experimentos/padronizacao_diaria_f3f8772670f244779ad7/publicacao/resumo.json';
  const r=await fetch(`${base}/api/panorama/fonte?caminho=${encodeURIComponent(fonte)}`);
  assert.equal(r.status,200);
  const bytes=Buffer.from(await r.arrayBuffer());
  assert.equal(createHash('sha256').update(bytes).digest('hex'),r.headers.get('x-source-sha256'));
  for(const f of ['dados/experimentos/generalizacao_moedas_1f2b005888361d23c111/ETHUSDT/ajustes/seed_42/checkpoints/epoca_0001.pt','../../registros/catalogo_estudos.json'])assert.equal((await fetch(`${base}/api/panorama/fonte?caminho=${encodeURIComponent(f)}`)).status,404);
});
test('Configuração tem uma categoria por vez, comparação e fontes por hash em todas as fases',async()=>{
  const ids=['inicio','comparacao-modelos','receitas-ohlcv','buscas-ia','historico-movel','receita-diaria','alvo-diario','padronizacao-diaria','sem-penalizacao','outras-moedas','estado32'];
  for(const id of ids){
    const resumo=await (await fetch(`${base}/?etapa=${id}`)).text();
    assert.doesNotMatch(resumo,/class="tabela-parametros"/);
    const r=await fetch(`${base}/?etapa=${id}&aba=configuracao`);assert.equal(r.status,200);
    const html=await r.text();assert.match(html,/Configuração da fase/);assert.match(html,/Só alterações/);assert.match(html,/Referência do teste/);
    assert.match(html,/Categorias da configuração/);assert.match(html,/class="tabela-parametros"/);
    assert.match(html,/<details class="fontes-configuracao"(?![^>]*\bopen\b)[^>]*>/);
  }
  const fonte='configuracoes/padronizacao_diaria_001.json';
  const r=await fetch(`${base}/api/panorama/fonte?caminho=${encodeURIComponent(fonte)}`);assert.equal(r.status,200);
  const bytes=Buffer.from(await r.arrayBuffer());assert.equal(createHash('sha256').update(bytes).digest('hex'),r.headers.get('x-source-sha256'));
  assert.equal(JSON.parse(bytes).treinamento.weight_decay,0.001);
  assert.equal((await fetch(`${base}/api/panorama/fonte?caminho=configuracoes/nao-autorizada.json`)).status,404);
});

test('Resultados finais incluem XRP, auditoria conjunta e distinção entre média e ensemble',async()=>{
  const html=await (await fetch(`${base}/?etapa=outras-moedas&aba=resultados`)).text();
  for(const trecho of ['Concluído e conferido','210','ETH','BNB','XRP','Média das 3 seeds','Ensemble','Seeds com ganho','teste retrospectivo'])assert.ok(html.includes(trecho),trecho);
  assert.doesNotMatch(html,/Conferência final pendente|Em treinamento|Sem publicação/);
  const fontes=await (await fetch(`${base}/?etapa=outras-moedas&aba=fontes`)).text();
  assert.match(fontes,/Fechamento conjunto/);
  for(const f of ['registros/generalizacao_moedas/retomadas/20261110/fechamento_geral.json','registros/generalizacao_moedas/conferencias/2026-11-10T160822.449897_0000/comparacao.json','dados/experimentos/generalizacao_moedas_1f2b005888361d23c111/XRPUSDT/continuacao_001/publicacao/resumo.json']){
    const r=await fetch(`${base}/api/panorama/fonte?caminho=${encodeURIComponent(f)}`);assert.equal(r.status,200,f);
    const bytes=Buffer.from(await r.arrayBuffer());assert.equal(createHash('sha256').update(bytes).digest('hex'),r.headers.get('x-source-sha256'));
  }
});
