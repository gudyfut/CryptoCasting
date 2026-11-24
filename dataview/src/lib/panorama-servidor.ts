import 'server-only';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import exportacao from '@/data/panorama.json';
import { etapas } from './etapas';
import type { DadosPanorama } from './panorama-tipos';
import { carregarCustos } from './custos-servidor';
export const panorama = exportacao as unknown as DadosPanorama;
export async function carregarPanorama(): Promise<DadosPanorama> {
  const c = await carregarCustos();
  if (c.situacao === 'vigente') return c.panorama as DadosPanorama;
  const copia = structuredClone(panorama);
  copia.custos_vigentes = { situacao: c.situacao, slippage_por_lado: c.slippage };
  if (c.situacao === 'divergente') for (const p of Object.values(copia.publicacoes)) {
    delete p.medias_operacionais_por_bloco; delete p.benchmarks_blocos;
    if ('series' in p) delete p.series;
    if (!('medias_globais' in p) && !('por_ajuste' in p)) delete p.medias;
  }
  return copia;
}
export const raizPanorama = path.resolve(process.cwd(), '..');
export type Disponibilidade = Record<string, 'conferida' | 'ausente' | 'divergente'>;
export async function conferirArquivo(caminho: string, esperado: string) {
  const bytes = await readFile(path.join(raizPanorama, caminho));
  if (createHash('sha256').update(bytes).digest('hex') !== esperado) throw new Error('Divergência de integridade');
  return bytes;
}
export async function disponibilidadeFontes(): Promise<Disponibilidade> {
  const caminhos = new Set(etapas.flatMap(e => [...e.fontes, ...(e.publicacao ? [String(panorama.publicacoes[e.publicacao].fonte)] : [])]));
  const resultados = await Promise.all([...caminhos].map(async caminho => {
    try { await conferirArquivo(caminho, panorama.fontes[caminho]); return [caminho, 'conferida'] as const; }
    catch (erro) { return [caminho, (erro as NodeJS.ErrnoException).code === 'ENOENT' ? 'ausente' : 'divergente'] as const; }
  }));
  return Object.fromEntries(resultados);
}
