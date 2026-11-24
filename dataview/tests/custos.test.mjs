import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { carregarCustos } from '../src/lib/custos-servidor.ts';

const hash=b=>createHash('sha256').update(b).digest('hex');
function fontes(){
  const pasta='dados/reavaliacoes/custos_'+'a'.repeat(20),mapa=new Map();
  const incluir=(p,v)=>{const b=Buffer.from(typeof v==='string'?v:JSON.stringify(v));mapa.set(path.resolve('..',p),b);return hash(b);};
  const pai='registros/exemplo.csv',h=incluir(pai,'data,valor\n2025-01-01,10\n');
  const arquivos={};
  for(const [nome,v] of Object.entries({resumo:{situacao:'concluido_conferido',slippage_por_lado:.0001,novos_treinamentos:0},panorama:{publicacoes:{}},diarias:{}}))arquivos[`publicacao/${nome}.json`]=incluir(`${pasta}/publicacao/${nome}.json`,v);
  const m=incluir(`${pasta}/publicacao_manifesto.json`,{arquivos,pais:{[pai]:h}});
  incluir('registros/custos_vigentes/vigente.json',{pasta,manifesto_sha256:m});
  return {mapa,pasta,leitor:async p=>{if(!mapa.has(p))throw Object.assign(new Error('Ausente'),{code:'ENOENT'});return mapa.get(p);}};
}
test('Custos vigentes exigem publicação completa e conferem bytes de pais inclusive CSV',async()=>{
  const f=fontes(),r=await carregarCustos(f.leitor);
  assert.equal(r.situacao,'vigente');assert.equal(r.slippage,.0001);assert.deepEqual(r.diarias,{});
});
test('Origem ou publicação alterada bloqueia custos vigentes; não troca hashes esperados',async()=>{
  for(const nome of ['registros/exemplo.csv','publicacao/diarias.json']){
    const f=fontes(),p=path.resolve('..',nome.startsWith('publicacao/')?`${f.pasta}/${nome}`:nome);
    f.mapa.set(p,Buffer.concat([f.mapa.get(p),Buffer.from(' ')]));
    assert.equal((await carregarCustos(f.leitor)).situacao,'divergente');
  }
});
test('Sem publicação, identifica histórico; ponteiro inválido não recebe aparência de vigente',async()=>{
  assert.equal((await carregarCustos(async()=>{throw Object.assign(new Error('Ausente'),{code:'ENOENT'});})).situacao,'historico');
  assert.equal((await carregarCustos(async()=>Buffer.from('{"pasta":"../../fora"}'))).situacao,'divergente');
});
