import { readdir, readFile } from "node:fs/promises";
import path from "node:path";

export type Execucao = {
  id: string; ciclo: string; id_ciclo?: string; status: string; inicio_utc: string; fim_utc?: string;
  celula: { par: string; contexto: number; horizonte: number; fold: string; seed: number };
  auditoria?: string; modelo?: string; erro?: string;
  resultados?: Record<string, { metricas: { teste: { log_loss: number; brier: number; balanced_accuracy: number | null; n: number } } }>;
  financeiro?: Record<string, { base: { status: string; retorno_liquido: number | null; drawdown_maximo: number | null; operacoes?: number } }>;
};

export function validarRegistro(valor: unknown): Execucao {
  if (!valor || typeof valor !== "object") throw new Error("Registro não é objeto.");
  const r = valor as Execucao;
  if (typeof r.id !== "string" || typeof r.ciclo !== "string" || !r.celula ||
      !["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT"].includes(r.celula.par) ||
      ![24, 168].includes(r.celula.contexto) || ![1, 24, 168].includes(r.celula.horizonte) ||
      !/^DB[1-4]$/.test(r.celula.fold) || !Number.isInteger(r.celula.seed)) throw new Error("Célula inválida.");
  if (r.status === "concluida_auditada") {
    if (r.auditoria !== "aprovado") throw new Error("Conclusão sem auditoria.");
    for (const modelo of ["mamba", "lstm", "ar1"]) {
      const m = r.resultados?.[modelo]?.metricas?.teste;
      if (!m || !Number.isFinite(m.log_loss) || m.log_loss < 0 || !Number.isInteger(m.n) || m.n <= 0) {
        throw new Error("Métricas ausentes ou inválidas.");
      }
    }
  }
  return r;
}

export async function lerExecucoes() {
  const raiz = path.resolve(process.cwd(), "../historico/execucoes");
  const resultados: Execucao[] = [];
  const avisos: string[] = [];
  let arquivos: string[];
  try { arquivos = await readdir(raiz); }
  catch (erro) {
    if ((erro as NodeJS.ErrnoException).code === "ENOENT") return { resultados, avisos };
    throw erro;
  }
  for (const nome of arquivos.filter((n) => /^[a-f0-9]{20}(_tentativa\d+)?\.json$/.test(n)).sort()) {
    try { resultados.push(validarRegistro(JSON.parse(await readFile(path.join(raiz, nome), "utf8")))); }
    catch { avisos.push(`${nome}: registro incompleto ou incompatível; não contado como resultado.`); }
  }
  return { resultados, avisos };
}
