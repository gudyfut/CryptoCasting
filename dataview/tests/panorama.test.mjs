import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { capitulos, etapas, fases } from '../src/lib/etapas.ts';
import { carregarCustos } from '../src/lib/custos-servidor.ts';
import { carregarEvolucao, fontesEvolucao } from '../src/lib/evolucao-servidor.ts';
import { carregarFichas, fontesFichas } from '../src/lib/fichas-servidor.ts';
import { compararFichas, gruposFicha, resumoFicha } from '../src/lib/fichas.ts';
import { metrica } from '../src/lib/panorama-tipos.ts';
const raiz=path.resolve('..');
const dados=JSON.parse(await fs.readFile('src/data/panorama.json','utf8'));
const perto=(a,b)=>assert.ok(Math.abs(a-b)<1e-12,`${a} != ${b}`);
const media=a=>a.reduce((x,y)=>x+y,0)/a.length;
test('Todas as etapas têm fontes e suas métricas resolvem na publicação correta',()=>{
  assert.equal(etapas.length,14);assert.equal(new Set(etapas.map(e=>e.id)).size,14);
  assert.equal(etapas[0].id,'desenho');
  assert.ok(etapas.every(e=>e.capitulo>=0&&e.capitulo<capitulos.length));
  assert.ok(etapas.every(e=>!['barreiras','retornos','penalizacao','prenorm','custos'].includes(e.id)));
  for(const e of etapas){
    for(const f of e.fontes)assert.ok(dados.fontes[f],`${e.id}: fonte ausente ${f}`);
    if(!e.grupos)continue;
    const p=dados.publicacoes[e.publicacao];
    for(const fase of Array.isArray(p.modelos)?['teste']:['validacao','teste'])for(const g of e.grupos){const m=metrica(p,g.chave,fase);assert.ok(Number.isFinite(m.mse)&&m.mse>0,`${e.id}/${g.chave}/${fase}`);}
  }
});
test('205 séries reais: hashes, alvo, preços, ordenação e curva de seleção',async()=>{
  assert.equal(dados.series.length,205);assert.equal(new Set(dados.series.map(s=>s.id)).size,205);
  for(const s of dados.series){
    assert.doesNotMatch(s.celula,/controle|repeticao/);
    const b=await fs.readFile(path.join(raiz,'dados/portal_panorama/series',`${s.id}.json`));
    assert.equal(createHash('sha256').update(b).digest('hex'),s.id);
    const j=JSON.parse(b);assert.equal(j.pontos.length,s.n);assert.equal(j.celula,s.celula);
    perto(j.metricas.mse,s.mse);assert.equal(j.metricas.n,s.n_horario);
    for(let i=0;i<j.pontos.length;i++){const p=j.pontos[i];assert.equal(p.length,5);assert.ok(p.every(Number.isFinite));assert.equal(p[0]%86400,0);assert.ok(p[1]>0&&p[2]>0);perto(Math.log(p[2]/p[1]),p[3]);if(i)assert.ok(p[0]>j.pontos[i-1][0]);}
    if(j.aprendizagem.length){const melhor=j.aprendizagem.reduce((a,b)=>a.mse_validacao<=b.mse_validacao?a:b);assert.equal(melhor.epoca,j.epoca_selecionada,`${s.celula}: época`);}
  }
});
test('A herda exatamente os 32 MSE, B/C têm oito seeds; médias preservam pesos iguais',async()=>{
  const p=dados.publicacoes.entradas;const seeds=[7,17,42,123,2026,31415,161803,271828];
  for(const variante of ['atual','crua','niveis_padronizados']){
    const medias=[];
    for(const bloco of ['B1','B2','B3','B4']){
      const ss=dados.series.filter(s=>s.bloco===bloco&&(variante==='atual'?s.ciclo==='blocos'&&s.modelo==='mse':s.ciclo==='entradas'&&s.modelo===variante));
      assert.deepEqual(ss.map(s=>s.seed).sort((a,b)=>a-b),seeds);
      const mse=media(ss.map(s=>s.mse));perto(mse,p.medias_por_bloco[bloco].teste[variante].mse);medias.push(mse);
      for(const s of ss){
        const a=dados.series.find(x=>x.ciclo==='blocos'&&x.modelo==='mse'&&x.seed===s.seed&&x.bloco===s.bloco);
        const j=JSON.parse(await fs.readFile(path.join(raiz,'dados/portal_panorama/series',`${s.id}.json`)));
        const r=JSON.parse(await fs.readFile(path.join(raiz,'dados/portal_panorama/series',`${a.id}.json`)));
        assert.deepEqual(j.pontos.map(p=>p.slice(0,4)),r.pontos.map(p=>p.slice(0,4)));
      }
    }
    perto(media(medias),p.medias_globais.teste[variante].mse);
  }
});
test('Os três contrastes e as sensibilidades mantêm conclusões e custos completos',()=>{
  const p=dados.publicacoes.entradas;
  for(const dias of ['7','14','28']){
    for(const chave of ['crua_menos_atual','niveis_padronizados_menos_atual']){const l=p.contrastes.teste[chave].intervalos[dias].ic_bonferroni_98_333;assert.ok(l[0]<0&&l[1]>0);}
    assert.ok(p.contrastes.teste.crua_menos_niveis_padronizados.intervalos[dias].ic_bonferroni_98_333[1]<0);
  }
  for(const ciclo of ['entradas','blocos'])for(const bloco of ['B1','B2','B3','B4'])for(const c of ['ideal','base','agravado']){
    const j=dados.publicacoes[ciclo].benchmarks_blocos[`${bloco}/benchmark/benchmark/comprar_manter/${c}`];assert.ok(Number.isFinite(j.retorno_liquido));assert.equal(j.capital_inicial,10000);
  }
  for(const bloco of ['B1','B2','B3','B4'])perto(p.medias_operacionais_por_bloco[bloco]['crua/diaria24/base'].retorno_liquido,0);
});
test('Arquivos estruturados exibidos permanecem idênticos às fontes exportadas',async()=>{
  for(const pub of Object.values(dados.publicacoes)){
    const b=await fs.readFile(path.join(raiz,pub.fonte));assert.equal(createHash('sha256').update(b).digest('hex'),dados.fontes[pub.fonte]);
  }
});
test('A cronologia cobre o início e a rodada atual sem perder os detalhes históricos',()=>{
  assert.equal(fases.length,10);
  assert.equal(new Set([...fases,...etapas].map(f=>f.id)).size,fases.length+etapas.length);
  assert.equal(fases[0].id,'inicio');
  assert.equal(fases.at(-1).id,'outras-moedas');
  for(const fase of fases){
    assert.ok(fase.pergunta&&fase.mudanca&&fase.conclusao&&fase.limite);
    for(const id of fase.detalhes??[])assert.ok(etapas.some(e=>e.id===id));
  }
  assert.deepEqual(new Set(fases.flatMap(f=>f.detalhes??[])),new Set(etapas.map(e=>e.id)));
});
test('Resultados recentes conferem hashes, médias das carteiras e ensemble separado',async()=>{
  const evolucao=await carregarEvolucao();
  assert.equal(evolucao.fechamento.situacao,'conferido');
  assert.equal(evolucao.fechamento.ajustes,9);
  assert.equal(evolucao.fechamento.controles,3);
  assert.equal(evolucao.fechamento.carteiras,210);
  const custos=await carregarCustos();
  const fontes=await fontesEvolucao();
  for(const fase of fases)for(const fonte of fase.fontes??[]){
    assert.ok(fontes[fonte],fonte);
    assert.equal(createHash('sha256').update(await fs.readFile(path.join(raiz,fonte))).digest('hex'),fontes[fonte]);
  }
  assert.equal(evolucao.receitas.length,4);
  assert.deepEqual(evolucao.moedas.map(m=>m.moeda),['ETH','BNB','XRP']);
  for(const r of [...evolucao.receitas,...evolucao.moedas]){
    assert.equal(r.situacao,'conferido',r.id);
    assert.equal(fontes[r.fonte],r.hash);
    const bytes=await fs.readFile(path.join(raiz,r.fonte));
    assert.equal(createHash('sha256').update(bytes).digest('hex'),r.hash);
    const resumo=custos.situacao==='vigente'?custos.diarias[r.fonte.replace('/publicacao/resumo.json','')].resumo:JSON.parse(bytes);
    for(const p of r.periodos){
      const f=resumo.resumos[p.ano===2024?'validacao':'teste'];
      perto(p.retorno,media(p.seeds.map(s=>s.retorno)));
      perto(p.queda,media(p.seeds.map(s=>s.queda)));
      perto(p.erroPreco,f.previsao_media_seeds.rmse_usdt);
      perto(p.retorno,f.operacao_media_seeds_base.retorno_liquido);
      assert.equal(p.seeds.length,3);
      assert.ok(p.ensemble&&Number.isFinite(p.ensemble.retorno));
    }
  }
  const p=evolucao.receitas.find(r=>r.id==='padronizado').periodos.find(p=>p.ano===2025);
  assert.ok(p.retorno<0&&p.ensemble.retorno>0);
  assert.equal(p.ensemble.operacoes,24);
  assert.ok(!Object.hasOwn(fontes,'../../AGENTS.md'));
});
test('Todas as fases e testes têm fichas completas e fontes íntegras',async()=>{
  const c=await carregarFichas();
  const chaves=new Set(gruposFicha.flatMap(g=>Object.keys(g.campos).map(k=>`${g.id}.${k}`)));
  for(const pagina of [...fases,...etapas]){
    assert.ok(c.paginas[pagina.id]?.length,pagina.id);
    assert.ok(c.paginas[pagina.id].includes(c.padroes[pagina.id]),pagina.id);
    for(const id of c.paginas[pagina.id])assert.ok(c.fichas[id],id);
    if(c.anteriores[pagina.id])assert.ok(c.fichas[c.anteriores[pagina.id]],pagina.id);
  }
  for(const f of Object.values(c.fichas)){
    assert.equal(f.integridade,'conferida',f.id);
    assert.ok(Object.keys(f.campos).length>=50,f.id);
    assert.ok(f.fontes.length>0,f.id);
    if(f.referencia)assert.ok(c.fichas[f.referencia],f.id);
    for(const [k,v] of Object.entries(f.campos)){assert.ok(chaves.has(k),`${f.id}/${k}`);assert.equal(typeof v,'string');assert.ok(v.length>0,`${f.id}/${k}`);assert.doesNotMatch(v,/Não informado na fonte|undefined|NaN/,`${f.id}/${k}`);}
  }
  for(const [fonte,hash] of Object.entries(fontesFichas()))assert.equal(createHash('sha256').update(await fs.readFile(path.join(raiz,fonte))).digest('hex'),hash,fonte);
});
test('Cores refletem os fatores diários e distinguem a cronologia da referência herdada',async()=>{
  const c=await carregarFichas();
  const diferencas=(id,base)=>compararFichas(c.fichas[id],c.fichas[base]).flatMap(g=>g.campos).filter(x=>x.alteracao!=='mantido').map(x=>x.id).sort();
  assert.deepEqual(diferencas('alvo','diario'),['avaliacao.selecao','entrada.alvo']);
  assert.deepEqual(diferencas('padronizado','alvo'),['entrada.escala']);
  assert.deepEqual(diferencas('sem-penalizacao','padronizado'),['treino.decay']);
  assert.equal(c.anteriores['outras-moedas'],'sem-penalizacao');
  for(const moeda of ['ETH','BNB','XRP']){
    assert.equal(c.fichas[`moeda-${moeda}`].referencia,'padronizado');
    assert.ok(diferencas(`moeda-${moeda}`,'sem-penalizacao').includes('treino.decay'));
    assert.ok(!diferencas(`moeda-${moeda}`,'padronizado').includes('treino.decay'));
  }
  assert.equal(c.fichas.diario.campos['modelo.estado'],'64');
  assert.match(c.fichas.diario.campos['modelo.eixo'],/Canais: 6 tokens/);
  assert.match(c.fichas.r0.campos['modelo.eixo'],/Tempo/);
  assert.equal(c.fichas.estado32.referencia,'r0');
  assert.equal(c.anteriores.estado32,'estado8');
  assert.equal(c.fichas['astra1-C01'].campos['avaliacao.seeds'],'42');
  assert.equal(c.fichas['astra2-N08'].campos['avaliacao.seeds'],'42 / 17');
  assert.equal(c.fichas['astra2-N07'].campos['avaliacao.seeds'],'42 / 17 / 2026');
  assert.equal(c.fichas['carteira-crypto'].campos['modelo.estado'],'64');
  assert.match(c.fichas['carteira-lstm'].campos['modelo.estrutura'],/LSTM/);
});
test('Fichas ocultam parâmetros de uma fonte alterada ou ausente sem tocar nos artefatos',async()=>{
  const alterada=await carregarFichas(async arquivo=>{
    const bytes=await fs.readFile(arquivo);
    return arquivo.endsWith('padronizacao_diaria_001.json')?Buffer.concat([bytes,Buffer.from(' ')]):bytes;
  });
  assert.equal(alterada.fichas.padronizado.integridade,'divergente');
  assert.deepEqual(alterada.fichas.padronizado.campos,{});
  assert.equal(alterada.fichas.alvo.integridade,'conferida');
  const ausente=await carregarFichas(async arquivo=>{
    if(arquivo.endsWith('candidatas.json'))throw Object.assign(new Error('Ausente simulado'),{code:'ENOENT'});
    return fs.readFile(arquivo);
  });
  assert.equal(ausente.fichas['astra1-final'].integridade,'ausente');
  assert.deepEqual(ausente.fichas['astra1-final'].campos,{});
  assert.equal(ausente.fichas.diario.integridade,'conferida');
});
test('Resumo mantém alvo, eixo e regularização sem confundir as receitas',async()=>{
  const c=await carregarFichas();
  const resumo=id=>resumoFicha(c.fichas[id]);
  const entrada=id=>resumo(id).find(r=>r.id==='entrada');
  assert.equal(resumo('padronizado').length,5);
  assert.match(entrada('diario').apoio.texto,/Preço de fechamento/);
  assert.match(entrada('alvo').apoio.texto,/Retorno simples/);
  assert.match(resumo('padronizado').find(r=>r.id==='modelo').apoio.texto,/canais/);
  assert.match(resumo('r0').find(r=>r.id==='modelo').apoio.texto,/tempo/);
  assert.ok(resumo('sem-penalizacao').find(r=>r.id==='treino').itens.some(i=>i.id==='treino.decay'&&i.texto==='Penalização: 0'));
  assert.ok(!resumo('carteira-lstm').find(r=>r.id==='modelo').itens.some(i=>i.id==='modelo.estado'));
  assert.match(resumo('f01-astra').find(r=>r.id==='treino').itens[0].texto,/Sem novo treinamento/);
  assert.match(resumo('diario-primeiro').find(r=>r.id==='avaliacao').itens[0].texto,/teste 2025 bloqueado/);
  assert.match(resumo('astra2-N08').find(r=>r.id==='operacao').itens[0].texto,/Não executada/);
});
