import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import ts from "typescript";

// Usa o compilador já instalado no projeto; nenhuma dependência de testes nova.
const fonte = await readFile(new URL("../src/lib/resultados-locais.ts", import.meta.url), "utf8");
const { outputText } = ts.transpileModule(fonte, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 } });
const { interpretarResultado } = await import(`data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`);
const pasta = `pareado_${"a".repeat(20)}`;

function resumo() {
  const metrica = { amostras: 8, suporte_nao_alta: 4, suporte_alta: 4, balanced_accuracy: .75, accuracy: .75, f1_macro: .75, matriz_confusao_linhas_reais_colunas_previstas: [[3, 1], [1, 3]] };
  return { id: "a".repeat(20), contrato: "entregas45-v1", estado: "concluido", tipo_fold: "desenvolvimento", protocolo: "1.6", sha256_codigo: "b".repeat(64),
    celula: { par: "BTCUSDT", granularidade: "1d", contexto_dias: 7, tarefa: "principal", fold: "D1", seed: 42 },
    configuracao: { pares: ["BTCUSDT"], granularidades: ["1d"], contextos_dias: [7], tarefa: "principal", folds: ["D1"], seeds: [42], features: "ohlcv", normalizador: "standard", backend_mamba: "pytorch", dispositivo: "cpu", largura_mamba: 32, largura_lstm: 32 },
    modelos: { mamba: { backend: "pytorch" }, lstm: { backend: "torch.nn.LSTM" } }, contagens: { teste: 8 },
    avaliacoes: { teste: { metricas: { mamba: structuredClone(metrica), lstm: structuredClone(metrica), ar1: structuredClone(metrica) }, diferencas_pp: { mamba_menos_ar1: 0, mamba_menos_lstm: 0, mamba_menos_50: 25 } } } };
}

test("resumo completo mantém BA, backend e dispositivo", () => {
  const resultado = interpretarResultado(resumo(), pasta);
  assert.equal(resultado.ba.mamba, .75);
  assert.equal(resultado.dispositivo, "cpu");
});
test("BA alterada sem matriz correspondente é rejeitada", () => {
  const r = resumo(); r.avaliacoes.teste.metricas.mamba.balanced_accuracy = .99;
  assert.throws(() => interpretarResultado(r, pasta), /Métrica inconsistente/);
});
test("diferença em pontos percentuais inconsistente é rejeitada", () => {
  const r = resumo(); r.avaliacoes.teste.diferencas_pp.mamba_menos_50 = .25;
  assert.throws(() => interpretarResultado(r, pasta), /Métrica inconsistente/);
});
test("fold final ou resultado incompleto não entra no painel de desenvolvimento", () => {
  const r = resumo(); r.celula.fold = "F1";
  assert.throws(() => interpretarResultado(r, pasta));
  const incompleto = resumo(); incompleto.estado = "em_execucao";
  assert.throws(() => interpretarResultado(incompleto, pasta));
});
test("backend executado não pode ser rotulado como outro", () => {
  const r = resumo(); r.modelos.mamba.backend = "oficial";
  assert.throws(() => interpretarResultado(r, pasta), /Backend executado/);
});
test("identidade e população declarada precisam corresponder", () => {
  assert.throws(() => interpretarResultado(resumo(), `pareado_${"c".repeat(20)}`));
  const r = resumo(); r.contagens.teste = 9;
  assert.throws(() => interpretarResultado(r, pasta), /Suportes/);
});
test("falta de classe é indisponibilidade e nunca BA zero", () => {
  const r = resumo();
  for (const m of Object.values(r.avaliacoes.teste.metricas)) Object.assign(m, { suporte_alta: 0, suporte_nao_alta: 8, balanced_accuracy: null, accuracy: 1, f1_macro: .5, matriz_confusao_linhas_reais_colunas_previstas: [[8, 0], [0, 0]] });
  for (const k of Object.keys(r.avaliacoes.teste.diferencas_pp)) r.avaliacoes.teste.diferencas_pp[k] = null;
  assert.equal(interpretarResultado(r, pasta).ba.mamba, null);
});
test("próximo candle diário só reutiliza a célula principal canônica", () => {
  const r = resumo(); r.configuracao.tarefa = "proximo_candle";
  assert.equal(interpretarResultado(r, pasta).tarefa, "principal");
  r.celula.tarefa = "proximo_candle";
  assert.throws(() => interpretarResultado(r, pasta), /canônica/);
});
