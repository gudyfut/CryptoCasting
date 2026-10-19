import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { gunzipSync } from "node:zlib";
import path from "node:path";
import { agregarCandles, type IndicePublico, type SeriePrevisoes } from "./exploracao";

type Indice = IndicePublico & { arquivos: Record<string, string> };
const raiz = path.resolve(process.cwd(), ".dados/explorador");
export async function lerIndice(): Promise<Indice> {
  const [bruto, recibo] = await Promise.all([readFile(path.join(raiz, "indice.json")), readFile(path.resolve(process.cwd(), "../historico/qualificacoes/explorador_previsoes_2026-10-19.json"), "utf8")]);
  if (createHash("sha256").update(bruto).digest("hex") !== JSON.parse(recibo).indiceSha256) throw new Error("Índice de previsões não corresponde à exportação verificada.");
  const indice = JSON.parse(bruto.toString()) as Indice;
  if (indice.ciclo !== "4e232a796fcda0ea34c3" || indice.dataset !== "9341610dbb329a858784" || indice.celulas.length !== 96) throw new Error("Identidade incompatível.");
  return indice;
}
export async function lerPacote(indice: Indice, nome: string) {
  if (!Object.hasOwn(indice.arquivos, nome)) throw new Error("Arquivo fora do inventário.");
  const bruto = await readFile(path.join(raiz, nome));
  if (createHash("sha256").update(bruto).digest("hex") !== indice.arquivos[nome]) throw new Error("Arquivo de visualização alterado; exportação precisa ser conferida.");
  return JSON.parse(gunzipSync(bruto).toString());
}
export async function lerSerie(id: string): Promise<SeriePrevisoes> {
  const indice = await lerIndice();
  if (!indice.celulas.some(c => c.id === id)) throw new Error("Célula indisponível.");
  return lerPacote(indice, `previsoes/${id}.json.gz`);
}
export async function lerPrecos(par: string, inicio: number, fim: number, resolucao: number) {
  const indice = await lerIndice();
  if (!["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT"].includes(par) || ![1, 5, 15, 60].includes(resolucao) || !Number.isSafeInteger(inicio) || !Number.isSafeInteger(fim) || inicio >= fim || fim - inicio > (resolucao === 60 ? 96 : 18) * 86400 || inicio < indice.inicioPrecos || fim > indice.fimPrecos) throw new Error("Recorte de preços inválido.");
  const dias: number[] = [];
  for (let dia = Math.floor(inicio / 86400) * 86400; dia < fim; dia += 86400) dias.push(dia);
  const blocos = await Promise.all(dias.map(dia => lerPacote(indice, `precos/${par}/${new Date(dia * 1000).toISOString().slice(0, 10)}.json.gz`)));
  const linhas = (blocos.flat() as number[][]).filter(r => r[0] >= inicio && r[0] < fim);
  return { candles: agregarCandles(linhas, resolucao), minutosAusentes: linhas.filter(r => r.length === 1).length, resolucao, inicio, fim };
}
