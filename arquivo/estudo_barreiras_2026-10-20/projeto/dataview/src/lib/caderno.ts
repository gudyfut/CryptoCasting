import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import path from "node:path";

export type Media = { modelo: string; log_loss: number; brier: number; balanced_accuracy: number; horizonte?: number; par?: string; fold?: string };
export type Contraste = { diferenca_media: { log_loss: number }; intervalos: Record<string, { log_loss: [number, number] }> };
export type Resumo = {
  id_ciclo: string; dataset: string; celulas: number; ponderacao: string;
  medias: Media[]; por_horizonte: Media[]; por_moeda: Media[]; por_fold: Media[];
  contrastes_globais: { mamba_menos_lstm: Contraste; mamba_menos_ar1: Contraste };
  contexto: { modelo: string; horizonte: number; diferenca_log_loss: number; pares: number; favorece_168: number }[];
  treinamentos: { modelo: string; ajustes: number; parametros: number; epoca_selecionada_mediana: number; selecionou_primeira_epoca: number }[];
  classes_por_horizonte: { horizonte: number; modelo: string; classe: number; probabilidade_media: number; frequencia_observada: number }[];
  comprar_manter_pontas: { par: string; retorno_liquido: number; drawdown_maximo: null }[];
};
export type Financeiro = { par: string; contexto: number; horizonte: number; modelo: string; variante: string; status: string; retorno_liquido: number | null; drawdown_maximo: number | null; tempo_exposto: number | null; operacoes: number | null; retorno_ic14_inferior: number | null; retorno_ic14_superior: number | null };
export type Barreira = { par: string; horizonte: number; n: number; alta_limite_relativa_mediana: number };
export type Caderno = { resumo: Resumo; financeiro: Financeiro[]; barreiras: Barreira[] };
const identidade = "4e232a796fcda0ea34c3";
const resumoEsperado = "350a6b080ded621a8bf0f53f76a0a97f5168a6e580f361912f5dd88847f1e0c5";
export function conferirHash(conteudo: Buffer, esperado: string) {
  if (createHash("sha256").update(conteudo).digest("hex") !== esperado) throw new Error("A integridade do relatório não confere. Consulte o histórico antes de atualizar o painel.");
}
// Os CSVs exportados neste ciclo contêm campos simples; rejeitar uma extensão
// de formato evita interpretar silenciosamente arquivos de outro contrato.
export function lerCsvSimples(conteudo: string): Record<string, string>[] {
  if (conteudo.includes('"')) throw new Error("Formato CSV não suportado neste relatório.");
  const [cabecalho, ...linhas] = conteudo.trim().split(/\r?\n/);
  const chaves = cabecalho.split(",");
  return linhas.map(linha => {
    const campos = linha.split(",");
    if (campos.length !== chaves.length) throw new Error("Linha incompleta no relatório.");
    return Object.fromEntries(chaves.map((chave, i) => [chave, campos[i]]));
  });
}
export function numeroOuAusencia(valor: string | undefined): number | null {
  if (valor == null || valor.trim() === "") return null;
  const n = Number(valor);
  if (!Number.isFinite(n)) throw new Error("Número inválido no relatório.");
  return n;
}
export async function lerCaderno(): Promise<{ dados: Caderno | null; erro: string | null }> {
  try {
    const raiz = path.resolve(process.cwd(), "../historico/analises/ciclo_001_completo");
    const conteudo = await readFile(path.join(raiz, "resumo.json"));
    conferirHash(conteudo, resumoEsperado);
    const bruto = JSON.parse(conteudo.toString("utf8"));
    if (bruto.id_ciclo !== identidade || bruto.dataset !== "9341610dbb329a858784" || bruto.celulas !== 96) throw new Error("Identidade científica inesperada.");
    const [financeiroCsv, barreirasCsv] = await Promise.all(["financeiro_anual.csv", "barreiras_observadas.csv"].map(async nome => {
      const arquivo = await readFile(path.join(raiz, nome));
      conferirHash(arquivo, bruto.arquivos_saida[nome]);
      return lerCsvSimples(arquivo.toString("utf8"));
    }));
    const financeiro = financeiroCsv.map(r => ({ par: r.par, modelo: r.modelo, variante: r.variante, status: r.status,
      contexto: Number(r.contexto), horizonte: Number(r.horizonte), retorno_liquido: numeroOuAusencia(r.retorno_liquido), drawdown_maximo: numeroOuAusencia(r.drawdown_maximo), tempo_exposto: numeroOuAusencia(r.tempo_exposto), operacoes: numeroOuAusencia(r.operacoes), retorno_ic14_inferior: numeroOuAusencia(r.retorno_ic14_inferior), retorno_ic14_superior: numeroOuAusencia(r.retorno_ic14_superior) }));
    const barreiras = barreirasCsv.map(r => ({ par: r.par, horizonte: Number(r.horizonte), n: Number(r.n), alta_limite_relativa_mediana: Number(r.alta_limite_relativa_mediana) }));
    if (financeiro.length !== 288 || barreiras.length !== 12) throw new Error("Relatório incompleto.");
    const resumo: Resumo = { id_ciclo: bruto.id_ciclo, dataset: bruto.dataset, celulas: bruto.celulas, ponderacao: bruto.ponderacao,
      medias: bruto.medias, por_horizonte: bruto.por_horizonte, por_moeda: bruto.por_moeda, por_fold: bruto.por_fold,
      contrastes_globais: bruto.contrastes_globais, contexto: bruto.contexto, treinamentos: bruto.treinamentos,
      classes_por_horizonte: bruto.classes_por_horizonte, comprar_manter_pontas: bruto.comprar_manter_pontas };
    return { dados: { resumo, financeiro, barreiras }, erro: null };
  } catch (e) { return { dados: null, erro: e instanceof Error ? e.message : "Não foi possível ler o relatório." }; }
}
