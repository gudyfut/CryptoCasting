import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import ts from 'typescript';
async function carregar(nome) {
  const fonte = await readFile(new URL(`../src/lib/${nome}.ts`, import.meta.url), 'utf8');
  const js = ts.transpileModule(fonte, {compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText;
  return import(`data:text/javascript;base64,${Buffer.from(js).toString('base64')}`);
}
const { perdas, limites, operacaoIlustrativa } = await carregar('didatica');
const { conferirHash, numeroOuAusencia, lerCsvSimples, lerCaderno } = await carregar('caderno');
const perto = (a,b) => assert.ok(Math.abs(a-b)<1e-10, `${a} ≠ ${b}`);

test('escores distinguem perfeição, erro confiante e referência uniforme', () => {
  perto(perdas([0,0,1],2).logLoss,0); perto(perdas([0,0,1],2).brier,0);
  perto(perdas([1,0,0],2).brier,2);
  perto(perdas([1/3,1/3,1/3],2).logLoss,Math.log(3));
  perto(perdas([1/3,1/3,1/3],2).brier,2/3);
  assert.ok(perdas([.8,.1,.1],2).logLoss > perdas([.1,.1,.8],2).logLoss);
  assert.throws(()=>perdas([.3,.3,.3],2));
});
test('barreiras escalam em raiz do prazo e são simétricas em log-preço', () => {
  const dia=limites(100,.003,24), semana=limites(100,.003,168);
  perto(semana.distancia/dia.distancia,Math.sqrt(7));
  perto(Math.log(dia.superior/100),-Math.log(dia.inferior/100));
});
test('política rejeita sinal insuficiente e alvo incapaz de pagar custos', () => {
  for(const [alta,p] of [[.02,.55],[.004,.6]]) {
    const r=operacaoIlustrativa(alta,p,'superior');
    assert.equal(r.permitida,false); assert.equal(r.quantidade,0); assert.equal(r.saldo,10000);
  }
});
test('contabilidade preserva caixa, cobra dois lados e limita risco nominal', () => {
  const stop=operacaoIlustrativa(.02,.65,'inferior');
  assert.equal(stop.permitida,true); assert.ok(stop.investido<10000);
  perto(stop.saldo,9900); // orçamento de perda de 1%, sem gap
  const alvo=operacaoIlustrativa(.02,.65,'superior');
  perto(alvo.saldo-10000,alvo.investido*alvo.retornoSuperior);
  assert.ok(alvo.retornoSuperior<.02);
  const prazo=operacaoIlustrativa(.02,.65,'prazo');
  assert.ok(prazo.precoSaida>prazo.inferior && prazo.precoSaida<prazo.superior);
});
test('ausência não vira zero e CSV incompleto não é aceito', () => {
  assert.equal(numeroOuAusencia(''),null); assert.equal(numeroOuAusencia('0.0'),0);
  assert.throws(()=>numeroOuAusencia('NaN'));
  assert.throws(()=>lerCsvSimples('a,b\n1'));
});
test('adulteração de relatório é detectada', () => {
  const original=Buffer.from('relatorio original');
  const hash=createHash('sha256').update(original).digest('hex');
  assert.doesNotThrow(()=>conferirHash(original,hash));
  assert.throws(()=>conferirHash(Buffer.from('relatorio alterado'),hash));
});
test('relatório real fechado carrega integralmente, sem fontes volumosas no cliente', async () => {
  const {dados,erro}=await lerCaderno();
  assert.equal(erro,null); assert.equal(dados.resumo.celulas,96);
  assert.equal(dados.financeiro.length,288); assert.equal(dados.barreiras.length,12);
  assert.equal(dados.resumo.fontes,undefined);
  assert.equal(dados.financeiro.filter(r=>r.variante==='sem_filtro' && r.retorno_liquido===null).length,72);
  assert.equal(dados.financeiro.filter(r=>r.variante==='base' && r.modelo==='ar1' && r.operacoes===0).length,24);
});
