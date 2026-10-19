import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { gunzipSync } from 'node:zlib';
import ts from 'typescript';
async function importar(nome) {
  const fonte = await readFile(new URL(`../src/lib/${nome}.ts`, import.meta.url), 'utf8');
  const js = ts.transpileModule(fonte, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 } }).outputText;
  return import(`data:text/javascript;base64,${Buffer.from(js).toString('base64')}`);
}
const { agregarCandles, classePrevista } = await importar('exploracao');
const { perdas } = await importar('didatica');
test('agregação conserva OHLCV e não preenche candles com lacunas', () => {
  const dados = Array.from({length:5}, (_,i) => [i*60,100+i,110+i,90+i,105+i,2]);
  assert.deepEqual(agregarCandles(dados,5), [{time:0,open:100,high:114,low:90,close:109,volume:10}]);
  dados[2]=[120]; assert.deepEqual(agregarCandles(dados,5), [{time:0}]);
  assert.deepEqual(agregarCandles(dados.slice(0,4),5), [{time:0}]);
});
test('tolerância float32 preserva probabilidades, sem renormalização', () => {
  const p=[0.2,0.3,0.49999997];
  assert.equal(perdas(p,2).logLoss,-Math.log(p[2]));
  assert.equal(classePrevista(p),2); assert.throws(()=>perdas([.2,.3,.49],2));
});
test('exportação completa reproduz as métricas dos três modelos e mantém identidades', async () => {
  const bruto = await readFile('.dados/explorador/indice.json');
  const recibo = JSON.parse(await readFile('../historico/qualificacoes/explorador_previsoes_2026-10-19.json','utf8'));
  assert.equal(createHash('sha256').update(bruto).digest('hex'),recibo.indiceSha256);
  const indice=JSON.parse(bruto);
  assert.equal(indice.celulas.length,96);
  assert.equal(new Set(indice.celulas.map(c=>`${c.par}/${c.contexto}/${c.horizonte}/${c.fold}`)).size,96);
  for(const c of indice.celulas) {
    const nome=`previsoes/${c.id}.json.gz`, arquivo=await readFile(`.dados/explorador/${nome}`);
    assert.equal(createHash('sha256').update(arquivo).digest('hex'),indice.arquivos[nome]);
    const pacote=JSON.parse(gunzipSync(arquivo));
    assert.equal(pacote.observacoes.length,c.n);
    assert.equal(new Set(pacote.observacoes.map(o=>o.origem)).size,c.n);
    for(const m of ['mamba','lstm','ar1']) {
      let ll=0,brier=0;
      for(const o of pacote.observacoes) {
        assert(o.entrada===o.origem+60);assert(o.expiracao===o.entrada+c.horizonte*3600);
        assert(o.saida>=o.entrada && o.saida<=o.expiracao);
        const e=perdas(o.probabilidades[m],o.classe);ll+=e.logLoss;brier+=e.brier;
      }
      assert(Math.abs(ll/c.n-pacote.metricas[m].log_loss)<1e-10);
      assert(Math.abs(brier/c.n-pacote.metricas[m].brier)<1e-10);
    }
  }
});
test('lacuna real de março permanece observável como ausência', async () => {
  const linhas=JSON.parse(gunzipSync(await readFile('.dados/explorador/precos/BTCUSDT/2023-03-24.json.gz')));
  assert.equal(linhas.filter(l=>l.length===1).length,81);
  const horas=agregarCandles(linhas,60);
  assert.equal(horas.find(c=>c.time===Date.parse('2023-03-24T13:00:00Z')/1000).open,undefined);
});
