import test from 'node:test';
import assert from 'node:assert/strict';
import ts from 'typescript';
import { readFile } from 'node:fs/promises';
const fonte = await readFile(new URL('../src/lib/registros.ts', import.meta.url), 'utf8');
const js = ts.transpileModule(fonte, {compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText;
const { validarRegistro } = await import(`data:text/javascript;base64,${Buffer.from(js).toString('base64')}`);
const base = {id:'0123456789abcdef0123', ciclo:'ciclo_001',status:'treinando',inicio_utc:'2026-10-18',celula:{par:'BTCUSDT',contexto:24,horizonte:24,fold:'DB1',seed:42}};
test('estado de execução não vira resultado concluído',()=>assert.equal(validarRegistro(base).status,'treinando'));
test('conclusão exige auditoria e três comparadores',()=>assert.throws(()=>validarRegistro({...base,status:'concluida_auditada'})));
test('não aceita horizonte fora do contrato',()=>assert.throws(()=>validarRegistro({...base,celula:{...base.celula,horizonte:2}})));
test('aceita resultado auditado com métricas reais',()=>{
 const m = {metricas:{teste:{log_loss:1.05,brier:.66,balanced_accuracy:.34,n:100}}};
 const r = validarRegistro({...base,status:'concluida_auditada',auditoria:'aprovado',resultados:{mamba:m,lstm:m,ar1:m}});
 assert.equal(r.resultados.mamba.metricas.teste.n,100);
});
