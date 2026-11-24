import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import type { EvolucaoPesquisa, ResultadoDiario } from './panorama-tipos';
import { carregarCustos, type RevisaoCustos } from './custos-servidor.ts';

const raiz = path.resolve(process.cwd(), '..');
const pastaMoedas = 'dados/experimentos/generalizacao_moedas_1f2b005888361d23c111';
const fontesNarrativas: Record<string, string> = {
  'arquivo/estudo_barreiras_2026-10-20/README.md': '6841059c1fb4755c6b530c1039d757310c653d361f42249382046dcf82a06fcb',
  'arquivo/estudos_preliminares_2026-10-28/documentacao/resultados_avaliacao.md': 'cdac9fec6d228d97bd99fb07d5fe7b52f81344e9bcb1dfd7a8a280992994225c',
  'docs/resultados_crua_huber.md': 'a4562f1ed991695294f8e3cc9812a3f11c37063b52ae7a6b5ec35d200286b19d',
  'arquivo/orientacoes_2026-11-11/docs/exploracao_ia.md': '25d462b0b91db985f42a58b19264ecf1ad31e24825d5b822b186d6fbcdc9d587',
  'dados/experimentos/historico_treino_5ae264d75324c1093b39/publicacao/resumo.json': 'a4280c7a690b8187ca6e7d4356cd69092ae1c95a479c6b70742d17175a86cf6a',
  'registros/padronizacao_diaria/diagnosticos/2026-11-08T200124.658529Z/conclusao.json': 'dbea0593efcb6310a04aec436460e6bf1b3b43d64d32f4971ed1f147a71f4c2a',
  'registros/generalizacao_moedas/retomadas/20261110/fechamento_geral.json': 'd50fca64f77556a2c86994afc18be142bb6c07a53c8202a59a19f6c82373fc9e',
  'registros/generalizacao_moedas/conferencias/2026-11-10T160822.449897_0000/comparacao.json': '6a529235aafb7f24c35bfca2e9a235121e22494f7b8ebc982ae56ed34d3128e1',
};
// Identidades encerradas: conferir os bytes contra o fechamento, nunca recalcular
// o hash esperado para aceitar uma publicação alterada.
const publicacoes = [
  { id: 'preco', nome: 'Prever preço', moeda: 'BTC', pasta: 'dados/experimentos/cryptomamba_reproducivel_ac8183e1ecfb91102b48', fechamento: 'ff91bf4dd5c71b4c973422d37175ac948711eee8c27daf43b370056e28400628' },
  { id: 'retorno', nome: 'Prever retorno', moeda: 'BTC', pasta: 'dados/experimentos/retomada_alvo_diario_de09c2193737c2581261', fechamento: '6e553f875baa3f93a9d35f7960d6349f8165a3f474bdf939c9422e3f77db88aa' },
  { id: 'padronizado', nome: 'Entradas padronizadas', moeda: 'BTC', pasta: 'dados/experimentos/padronizacao_diaria_f3f8772670f244779ad7', fechamento: 'e09f750a95b79b3bfd87353389eb930994afe5f3e14deb27fe9b617dff9f9657' },
  { id: 'sem-penalizacao', nome: 'Sem penalização', moeda: 'BTC', pasta: 'dados/experimentos/sem_penalizacao_diaria_8a0aeee4d78503b7f50d', fechamento: '33862528119418dd815a97eb2a2aa5a3ca8786c3a5695fc1db410ebe3c8fe65e' },
  { id: 'eth', nome: 'Ethereum', moeda: 'ETH', pasta: `${pastaMoedas}/ETHUSDT`, fechamento: '5d7d44b5de9a247b18ca5eb085b4e398bf8f1cf3ebe338d4c95ecad72a7353e9' },
  { id: 'bnb', nome: 'BNB', moeda: 'BNB', pasta: `${pastaMoedas}/BNBUSDT`, fechamento: '71d40a45a0e8eeef5cdb08e845c525fe34b39262935c23f3f99b41517706a415' },
  // XRP concluiu na continuação identificada pelo recibo de encerramento.
  { id: 'xrp', nome: 'XRP', moeda: 'XRP', pasta: `${pastaMoedas}/XRPUSDT/continuacao_001`, fechamento: null },
];
type Json = Record<string, unknown>;
const objeto = (x: unknown): Json => x && typeof x === 'object' && !Array.isArray(x) ? x as Json : {};
const numero = (x: unknown): number | null => typeof x === 'number' && Number.isFinite(x) ? x : null;
async function ler(caminho: string, hash?: string | null) {
  const bytes = await readFile(path.join(raiz, caminho));
  if (hash && createHash('sha256').update(bytes).digest('hex') !== hash) throw new Error('Integridade divergente');
  return JSON.parse(bytes.toString('utf8')) as unknown;
}
async function manifesto(p: typeof publicacoes[number]) {
  let esperado = p.fechamento;
  if (p.id === 'xrp') {
    const recibo = objeto(await ler('registros/generalizacao_moedas/retomadas/20261110/fechamento.json'));
    if (recibo.conclusao_xrp !== `${p.pasta}/fechamento.json` || typeof recibo.sha256 !== 'string') throw new Error('Recibo XRP inválido');
    esperado = recibo.sha256;
  }
  const f = objeto(await ler(`${p.pasta}/fechamento.json`, esperado));
  if (f.situacao !== 'concluido_conferido') throw new Error('Publicação não encerrada');
  return objeto(f.arquivos);
}
async function resultado(p: typeof publicacoes[number], custos: RevisaoCustos): Promise<ResultadoDiario> {
  const fonte = `${p.pasta}/publicacao/resumo.json`;
  const base: ResultadoDiario = { id: p.id, nome: p.nome, moeda: p.moeda, fonte, situacao: 'ausente', periodos: [] };
  try {
    if (custos.situacao === 'divergente') throw new Error('Reavaliação de custos divergente');
    const hashes = await manifesto(p);
    const hash = hashes['publicacao/resumo.json'];
    const hashCarteiras = hashes['publicacao/carteiras.json'];
    if (typeof hash !== 'string' || typeof hashCarteiras !== 'string') throw new Error('Manifesto incompleto');
    const [resumoOriginal, carteirasOriginais] = await Promise.all([
      ler(fonte, hash), ler(`${p.pasta}/publicacao/carteiras.json`, hashCarteiras),
    ]);
    const revisao = objeto(custos.diarias?.[p.pasta]);
    if (custos.situacao === 'vigente' && (!revisao.resumo || !revisao.carteiras)) throw new Error('Reavaliação diária ausente');
    const resumo = custos.situacao === 'vigente' ? revisao.resumo : resumoOriginal;
    const carteiras = custos.situacao === 'vigente' ? revisao.carteiras : carteirasOriginais;
    const fases = objeto(objeto(resumo).resumos);
    if (!Array.isArray(carteiras)) throw new Error('Carteiras inválidas');
    const periodos = (['validacao', 'teste'] as const).map((fase, i) => {
      const f = objeto(fases[fase]);
      const previsao = objeto(f.previsao_media_seeds);
      const operacao = objeto(f.operacao_media_seeds_base);
      if (numero(previsao.n) !== (i === 0 ? 351 : 350) || numero(operacao.retorno_liquido) === null) throw new Error('Resumo inválido');
      const registros = carteiras.map(objeto).filter(c => c.fase === fase && c.cenario === 'base');
      const seeds = registros.filter(c => ['42', '17', '2026'].includes(String(c.unidade))).map(c => {
        const m = objeto(c.metricas);
        if (numero(m.retorno_liquido) === null || numero(m.drawdown_maximo) === null) throw new Error('Carteira inválida');
        return { seed: String(c.unidade), retorno: m.retorno_liquido as number, queda: m.drawdown_maximo as number };
      });
      if (seeds.length !== 3 || new Set(seeds.map(s => s.seed)).size !== 3) throw new Error('Seeds incompletas');
      const e = objeto(registros.find(c => c.unidade === 'ensemble')?.metricas);
      const habilidade = numero(previsao.habilidade_mse_retorno_naive);
      return {
        ano: 2024 + i, mse: numero(previsao.mse_retorno), erroPreco: numero(previsao.rmse_usdt),
        diferencaNaive: habilidade === null ? null : -habilidade,
        retorno: numero(operacao.retorno_liquido), queda: numero(operacao.drawdown_maximo), acerto: numero(previsao.acerto_sinal), seeds,
        ensemble: numero(e.retorno_liquido) === null || numero(e.drawdown_maximo) === null || numero(e.operacoes) === null ? null : { retorno: e.retorno_liquido as number, queda: e.drawdown_maximo as number, operacoes: e.operacoes as number },
      };
    });
    return { ...base, situacao: 'conferido', hash, periodos, fonteOperacional: custos.situacao === 'vigente' ? `${custos.pasta}/publicacao/diarias.json` : undefined };
  } catch (erro) {
    return { ...base, situacao: (erro as NodeJS.ErrnoException).code === 'ENOENT' ? 'ausente' : 'divergente' };
  }
}

export async function fontesEvolucao(): Promise<Record<string, string>> {
  const entradas = await Promise.all(publicacoes.map(async p => {
    try {
      const hashes = await manifesto(p);
      return ['publicacao/resumo.json', 'publicacao/carteiras.json'].flatMap(f => typeof hashes[f] === 'string' ? [[`${p.pasta}/${f}`, hashes[f] as string] as const] : []);
    } catch { return []; }
  }));
  return { ...fontesNarrativas, ...Object.fromEntries(entradas.flat()) };
}

export async function carregarEvolucao(): Promise<EvolucaoPesquisa> {
  const custos = await carregarCustos();
  const resultados = await Promise.all(publicacoes.map(p => resultado(p, custos)));
  const observadoEm = new Date().toISOString();
  const estado: EvolucaoPesquisa['estado'] = { situacao: 'indisponivel', registroEm: null, moeda: null, ajuste: null, concluidos: null, previstos: null, epoca: null, epocas: null, recente: false };
  try {
    // Estado é evidência operacional mutável, separado das publicações congeladas.
    const e = objeto(await ler('registros/generalizacao_moedas/estado.json'));
    estado.situacao = typeof e.situacao === 'string' ? e.situacao : 'indisponivel';
    estado.registroEm = typeof e.utc === 'string' ? e.utc : null;
    estado.moeda = typeof e.simbolo === 'string' && /^(ETH|BNB|XRP)USDT$/.test(e.simbolo) ? e.simbolo : null;
    estado.ajuste = typeof e.job_atual === 'string' && /^(seed_\d+|controle_42)$/.test(e.job_atual) ? e.job_atual : null;
    estado.concluidos = numero(e.ajustes_concluidos); estado.previstos = numero(e.ajustes_previstos);
    if (estado.moeda && estado.ajuste) {
      const continuacao = e.continuacao === `${pastaMoedas}/XRPUSDT/continuacao_001`;
      const pasta = `${pastaMoedas}/${estado.moeda}${continuacao ? '/continuacao_001' : ''}`;
      try {
        const progresso = objeto(await ler(`${pasta}/ajustes/${estado.ajuste}/progresso.json`));
        estado.epoca = numero(progresso.epoca); estado.epocas = numero(progresso.total);
        if (typeof progresso.utc === 'string' && Date.parse(progresso.utc) > Date.parse(estado.registroEm ?? '')) estado.registroEm = progresso.utc;
      } catch { /* Sem progresso legível: não inventar época. */ }
    }
    const idade = Date.parse(observadoEm) - Date.parse(estado.registroEm ?? '');
    estado.recente = Number.isFinite(idade) && idade >= -60_000 && idade < 10 * 60_000;
  } catch { /* A ausência de artefatos não impede consultar a cronologia. */ }
  const fechamento = await carregarFechamento();
  return { observadoEm, fechamento, receitas: resultados.filter(r => r.moeda === 'BTC'), moedas: resultados.filter(r => r.moeda !== 'BTC'), estado, custos: { situacao: custos.situacao, slippage: custos.slippage } };
}

async function carregarFechamento(): Promise<EvolucaoPesquisa['fechamento']> {
  const fonte = 'registros/generalizacao_moedas/retomadas/20261110/fechamento_geral.json';
  try {
    const ponteiro = objeto(await ler('registros/generalizacao_moedas/fechamento.json'));
    if (ponteiro.arquivo !== fonte || ponteiro.sha256 !== fontesNarrativas[fonte]) throw new Error('Fechamento não reconhecido');
    const f = objeto(await ler(fonte, fontesNarrativas[fonte]));
    const conferencia = objeto(f.conferencia);
    const comparacao = String(conferencia.arquivo);
    if (f.situacao !== 'concluido_conferido_continuacao' || conferencia.sha256 !== fontesNarrativas[comparacao] || !fontesNarrativas[comparacao]) throw new Error('Conferência não reconhecida');
    await ler(comparacao, fontesNarrativas[comparacao]);
    await Promise.all(publicacoes.filter(p => ['padronizado', 'eth', 'bnb', 'xrp'].includes(p.id)).map(manifesto));
    if (f.ajustes_principais_novos !== 9 || f.controles_novos !== 3 || f.carteiras_novas !== 210 || f.btc_herdado_sem_retreino !== true) throw new Error('Escopo divergente');
    return { situacao: 'conferido', data: String(f.utc), ajustes: 9, controles: 3, carteiras: 210, fonte, comparacao };
  } catch (erro) {
    return { situacao: (erro as NodeJS.ErrnoException).code === 'ENOENT' ? 'indisponivel' : 'divergente' };
  }
}
