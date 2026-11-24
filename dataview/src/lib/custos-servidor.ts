import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import path from 'node:path';

type Json = Record<string, unknown>;
type Leitor = (arquivo: string) => Promise<Buffer>;
export type RevisaoCustos = {
  situacao: 'vigente' | 'historico' | 'divergente';
  slippage: number; pasta?: string; arquivos?: Record<string, string>;
  panorama?: unknown; diarias?: Json; resumo?: Json;
};
const raiz = path.resolve(process.cwd(), '..');
const objeto = (v: unknown): Json => v && typeof v === 'object' && !Array.isArray(v) ? v as Json : {};
async function lerCustos(leitor: Leitor): Promise<RevisaoCustos> {
  async function ler(nome: string, esperado?: string) {
    const destino = path.resolve(raiz, nome);
    if (!destino.startsWith(raiz + path.sep)) throw new Error('Caminho fora do projeto');
    const b = await leitor(destino);
    if (esperado && createHash('sha256').update(b).digest('hex') !== esperado) throw new Error('Custos: integridade divergente');
    return JSON.parse(b.toString('utf8')) as unknown;
  }
  let ptr: Json;
  try { ptr = objeto(await ler('registros/custos_vigentes/vigente.json')); }
  catch (erro) {
    return { situacao: (erro as NodeJS.ErrnoException).code === 'ENOENT' ? 'historico' : 'divergente', slippage: .0005 };
  }
  try {
    if (typeof ptr.pasta !== 'string' || !/^dados\/reavaliacoes\/custos_[a-f0-9]{20}$/.test(ptr.pasta) || typeof ptr.manifesto_sha256 !== 'string') throw new Error('Ponteiro inválido');
    const m = objeto(await ler(`${ptr.pasta}/publicacao_manifesto.json`, ptr.manifesto_sha256));
    const hashes = objeto(m.arquivos), pais = objeto(m.pais);
    for (const [nome, hash] of Object.entries(pais)) {
      if (typeof hash !== 'string') throw new Error('Hash de origem ausente');
      const destino = path.resolve(raiz, nome);
      if (!destino.startsWith(raiz + path.sep)) throw new Error('Origem fora do projeto');
      const b = await leitor(destino);
      if (createHash('sha256').update(b).digest('hex') !== hash) throw new Error('Origem divergente');
    }
    async function publicado(nome: string) {
      const chave = `publicacao/${nome}.json`, hash = hashes[chave];
      if (typeof hash !== 'string') throw new Error('Publicação incompleta');
      return ler(`${ptr.pasta}/${chave}`, hash);
    }
    const [panorama, diarias, resumo] = await Promise.all([publicado('panorama'), publicado('diarias'), publicado('resumo')]);
    const r = objeto(resumo);
    if (r.situacao !== 'concluido_conferido' || r.slippage_por_lado !== .0001 || r.novos_treinamentos !== 0) throw new Error('Reavaliação inválida');
    return { situacao: 'vigente', slippage: .0001, pasta: ptr.pasta, panorama, diarias: objeto(diarias), resumo: r,
      arquivos: Object.fromEntries(Object.entries(hashes).map(([k,v]) => [`${ptr.pasta}/${k}`, String(v)])) };
  } catch { return { situacao: 'divergente', slippage: .0001 }; }
}

// Compartilha apenas leituras simultâneas. Não mantém um resultado antigo após
// a leitura terminar: a próxima consulta volta a conferir as origens.
let emLeitura: Promise<RevisaoCustos> | undefined;
export function carregarCustos(leitor: Leitor = readFile): Promise<RevisaoCustos> {
  if (leitor !== readFile) return lerCustos(leitor);
  if (!emLeitura) {
    const atual = lerCustos(leitor);
    emLeitura = atual;
    void atual.finally(() => { if (emLeitura === atual) emLeitura = undefined; });
  }
  return emLeitura;
}
