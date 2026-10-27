import "server-only";
import fs from "node:fs/promises";
import path from "node:path";
import {createHash} from "node:crypto";
import type {Analise} from "./analises";
export const raiz = path.resolve(process.cwd(), "..");
export async function ler<T>(relativo: string): Promise<T | null> {
  try { return JSON.parse(await fs.readFile(path.join(raiz, relativo), "utf8")); }
  catch (erro) { if ((erro as NodeJS.ErrnoException).code === "ENOENT") return null; throw erro; }
}
export async function lerPublicacao(fase:string,arquivo="resumo.json"):Promise<string|null>{
  if(!["desenvolvimento","avaliacao"].includes(fase))return null;
  const ponteiro=await ler<{id:string}>("registros/execucao_atual.json");
  if(!ponteiro || !/^[a-f0-9]{20}$/.test(ponteiro.id))return null;
  const base=`registros/analises/${ponteiro.id}/${fase}`;
  const recibo=await ler<{execucao:string;fase:string;arquivos:Record<string,string>}>(`${base}/publicacao.json`);
  if(!recibo || recibo.execucao!==ponteiro.id || recibo.fase!==fase || !recibo.arquivos[arquivo])return null;
  const auditoria=await ler<{status:string;execucao:string;publicacao_sha256:string}>(`${base}/auditoria_publicacao.json`);
  if(!auditoria || auditoria.status!=="aprovado" || auditoria.execucao!==ponteiro.id)return null;
  const manifesto=await fs.readFile(path.join(raiz,base,"publicacao.json"));
  if(createHash("sha256").update(manifesto).digest("hex")!==auditoria.publicacao_sha256)return null;
  const absoluto=path.resolve(raiz,base,arquivo);
  if(!absoluto.startsWith(path.resolve(raiz,base)+path.sep))throw new Error("Caminho de publicação inválido.");
  const bytes=await fs.readFile(absoluto);
  if(createHash("sha256").update(bytes).digest("hex")!==recibo.arquivos[arquivo])throw new Error("Integridade da análise não confirmada.");
  return bytes.toString("utf8");
}
export async function analisesPublicadas():Promise<Analise[]>{
  const analises:Analise[]=[];
  for(const fase of ["desenvolvimento","avaliacao"]){const texto=await lerPublicacao(fase);if(texto)analises.push(JSON.parse(texto));}
  return analises;
}
export type Configuracao = { pares: string[]; contextos: number[]; seeds: number[]; folds_desenvolvimento: string[]; folds_avaliacao: string[]; horizonte: number; candle_minutos: number; entradas: string[] };
export type Estado = { configuracao: Configuracao; execucao: string | null; dataset: string | null; ajustesPlanejados: number; ajustesAuditados: number; referenciasAuditadas: number; falhas: number; piloto: boolean; desenvolvimento: boolean; avaliacao: boolean; congelado: boolean; ultimaAtualizacao: string | null;arquivoVerificado?:boolean;preparacaoAprovada?:boolean;interfaceAprovada?:boolean };
export async function estadoEstudo(): Promise<Estado> {
  const configuracao = await ler<Configuracao>("configuracoes/retorno24_001.json");
  if (!configuracao) throw new Error("Configuração do estudo indisponível.");
  const ponteiro = await ler<{ id: string; caminho: string; dataset: string }>("registros/execucao_atual.json");
  const estado: Estado = { configuracao, execucao: ponteiro?.id ?? null, dataset: ponteiro?.dataset ?? null, ajustesPlanejados: configuracao.pares.length * configuracao.contextos.length * configuracao.seeds.length * (configuracao.folds_desenvolvimento.length + configuracao.folds_avaliacao.length) * 2, ajustesAuditados: 0, referenciasAuditadas: 0, falhas: 0, piloto: false, desenvolvimento: false, avaliacao: false, congelado: false, ultimaAtualizacao: null };
  if (!ponteiro) return estado;
  const arquivo=await ler<{status:string}>("arquivo/estudo_barreiras_2026-10-20/verificacao.json");
  const testes=await ler<{status:string}>("registros/qualificacao/testes_atual.json");
  const cuda=await ler<{caminho:string}>("registros/qualificacao/cuda_atual.json");
  const qualificacao=cuda?await ler<{status:string}>(cuda.caminho):null;
  const dataset=await ler<{caminho:string}>("registros/dataset_atual.json");
  const preparacao=dataset?await ler<{status:string}>(`${dataset.caminho}/preparacao.json`):null;
  estado.arquivoVerificado=arquivo?.status==='preservado_verificado';
  estado.preparacaoAprovada=testes?.status==='aprovado'&&qualificacao?.status==='aprovado'&&preparacao?.status==='auditada';
  const aceite=await ler<{status:string;execucao:string}>("registros/interface/aceite_final.json");
  estado.interfaceAprovada=aceite?.status==='aprovado'&&aceite.execucao===ponteiro.id;
  const base = ponteiro.caminho;
  estado.piloto = !!await ler(`${base}/piloto_aprovado.json`);
  estado.desenvolvimento = !!await ler(`${base}/desenvolvimento_concluido.json`);
  estado.avaliacao = !!await ler(`${base}/avaliacao_concluido.json`);
  estado.congelado = !!await ler(`${base}/congelamento.json`);
  const celulas = await fs.readdir(path.join(raiz, base, "celulas")).catch(() => []);
  for (const celula of celulas) {
    const tentativas = await fs.readdir(path.join(raiz, base, "celulas", celula));
    for (const tentativa of tentativas) {
      const registro = await ler<{status:string;fim_utc?:string;celula:{modelo:string}}>(`${base}/celulas/${celula}/${tentativa}/tentativa.json`);
      if (!registro) continue;
      if (registro.status === "auditada") {
        if (["lstm", "mamba"].includes(registro.celula.modelo)) estado.ajustesAuditados++; else estado.referenciasAuditadas++;
        if (registro.fim_utc && (!estado.ultimaAtualizacao || registro.fim_utc > estado.ultimaAtualizacao)) estado.ultimaAtualizacao = registro.fim_utc;
      }
      if (["falha", "interrompida"].includes(registro.status)) estado.falhas++;
    }
  }
  return estado;
}
