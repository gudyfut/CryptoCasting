// Executar com servidor local ativo: node --test tests/api.integration.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
const base=process.env.URL_PORTAL_TESTE??'http://localhost:3000';
const raiz=path.resolve(process.cwd(),'..');
const indice=JSON.parse(fs.readFileSync(path.join(raiz,'dados/portal/resumo.json'),'utf8'));
test('API de série entrega a identidade auditada e recusa identificadores inválidos',async()=>{
  for(const fase of ['desenvolvimento','avaliacao']){
    const entrada=indice.series.find(s=>s.fase===fase);
    if(!entrada)continue;
    const resposta=await fetch(`${base}/api/estudo/serie?id=${entrada.id}`);
    assert.equal(resposta.status,200);
    const serie=await resposta.json();
    assert.equal(serie.id,entrada.id);
    assert.equal(serie.origens.length,entrada.n);
    assert.deepEqual(serie.modelos,entrada.modelos);
  }
  assert.equal((await fetch(`${base}/api/estudo/serie?id=../configuracoes`)).status,400);
  assert.equal((await fetch(`${base}/api/estudo/serie?id=00000000000000000000`)).status,404);
});
test('API de análise só publica fases com recibo e limita caminhos',async()=>{
  for(const fase of ['desenvolvimento','avaliacao']){
    const recibo=path.join(raiz,`registros/analises/${indice.execucao}/${fase}/auditoria_publicacao.json`);
    const resposta=await fetch(`${base}/api/estudo/analise?fase=${fase}`);
    if(fs.existsSync(recibo)){
      assert.equal(resposta.status,200);
      const analise=await resposta.json();
      assert.equal(analise.execucao,indice.execucao);
      assert.equal(analise.fase,fase);
      const manifesto=JSON.parse(fs.readFileSync(path.join(path.dirname(recibo),'publicacao.json'),'utf8'));
      for(const arquivo of ['resumo.json','metricas_por_ajuste.csv','metricas_medias_seeds.csv','financeiro.csv',analise.financeiro[0].arquivo]){
        const publicada=await fetch(`${base}/api/estudo/analise?fase=${fase}&arquivo=${arquivo}`);
        assert.equal(publicada.status,200);
        const bytes=Buffer.from(await publicada.arrayBuffer());
        assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),manifesto.arquivos[arquivo]);
        if(arquivo.endsWith('.csv'))assert.ok(publicada.headers.get('content-type').startsWith('text/csv'));
      }
    }else{
      assert.equal(resposta.status,404);
    }
  }
  assert.equal((await fetch(`${base}/api/estudo/analise?fase=avaliacao&arquivo=../../configuracoes/retorno24_001.json`)).status,400);
  assert.equal((await fetch(`${base}/api/estudo/analise?fase=antigo`)).status,400);
});
