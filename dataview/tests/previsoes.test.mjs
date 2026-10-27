import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import zlib from 'node:zlib';

const raiz=path.resolve(process.cwd(),'../dados/portal');
const resumo=JSON.parse(fs.readFileSync(path.join(raiz,'resumo.json'),'utf8'));

test('todas as séries exportadas têm identidade, datas e métricas coerentes',()=>{
  assert.ok(resumo.series.length>0,'nenhuma série exportada');
  for(const entrada of resumo.series){
    const bytes=fs.readFileSync(path.join(raiz,entrada.arquivo));
    assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),entrada.sha256);
    const serie=JSON.parse(zlib.gunzipSync(bytes).toString('utf8'));
    assert.equal(serie.id,entrada.id);
    assert.equal(serie.origens.length,entrada.n);
    const precos=new Map(serie.precos.map(p=>[p.time,p]));
    let anterior=-Infinity;
    for(const o of serie.origens){
      assert.ok(o.tempo>anterior);anterior=o.tempo;
      assert.equal(o.destino-o.tempo,86400);
      assert.equal(precos.get(o.tempo).close,o.preco);
      assert.equal(precos.get(o.destino).close,o.preco_real);
      assert.ok(Math.abs(Math.log(o.preco_real/o.preco)-o.retorno_real)<1e-14);
      for(const p of Object.values(o.previsoes)) assert.ok(Number.isFinite(p));
    }
    for(const modelo of serie.modelos){
      const metrica=resumo.metricas.find(m=>m.modelo===modelo&&m.par===serie.par&&m.fold===serie.fold&&(['naive','arima'].includes(modelo)||(m.contexto===serie.contexto&&m.seed===serie.seed)));
      assert.ok(metrica);
      const mse=serie.origens.reduce((s,o)=>s+(o.previsoes[modelo]-o.retorno_real)**2,0)/serie.origens.length;
      assert.ok(Math.abs(mse-metrica.mse)<1e-12);
      if(modelo==='naive') assert.ok(serie.origens.every(o=>o.previsoes.naive===0));
    }
  }
});

test('nenhum modelo ausente foi preenchido com uma previsão artificial',()=>{
  for(const entrada of resumo.series){
    const serie=JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(raiz,entrada.arquivo))).toString('utf8'));
    for(const o of serie.origens) assert.deepEqual(Object.keys(o.previsoes).sort(),[...serie.modelos].sort());
  }
});
