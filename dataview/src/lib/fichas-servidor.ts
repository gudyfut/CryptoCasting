import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import path from 'node:path';
import type { CatalogoFichas, FichaModelo } from './panorama-tipos';
import { carregarCustos } from './custos-servidor.ts';

type Json = Record<string, unknown>;
type Campos = Record<string, string>;
const o = (v: unknown): Json => v && typeof v === 'object' && !Array.isArray(v) ? v as Json : {};
const lista = (v: unknown): unknown[] => Array.isArray(v) ? v : [];
const texto = (v: unknown): string => v === null ? 'Sem limite adicional' : typeof v === 'boolean' ? v ? 'Sim' : 'Não' : Array.isArray(v) ? v.map(texto).join(' / ') : typeof v === 'object' ? JSON.stringify(v) : String(v ?? 'Não informado na fonte');
const numero = (v: unknown) => typeof v === 'number' ? v.toLocaleString('pt-BR', { maximumFractionDigits: 10 }) : texto(v);
const porcento = (v: unknown) => typeof v === 'number' ? `${numero(v * 100)}%` : texto(v);

// Lista fechada dos arquivos lidos nesta apresentação. Os hashes são fixados
// na implementação; uma divergência retira a ficha, nunca altera o esperado.
const fontes: Record<string, { caminho: string; sha256: string }> = {
  "barreiras": {"caminho": "arquivo/estudo_barreiras_2026-10-20/projeto/configuracoes/ciclo_001.json", "sha256": "c5339994f34c161edc45b62c51f93fff9465963483da95c010092488b5b41a5d"},
  "protocolo-barreiras": {"caminho": "arquivo/estudo_barreiras_2026-10-20/projeto/docs/protocolo_experimental.md", "sha256": "8911f17e05c8da1396081006939340686df537fcc9d0aef19a21b94f6bdcfc19"},
  "retorno24": {"caminho": "configuracoes/retorno24_001.json", "sha256": "12fcac9e6319dfc7f800f878016da8738331a7fa01795ad9150d7af801887a91"},
  "protocolo-retorno": {"caminho": "docs/protocolo_experimental.md", "sha256": "f500efb75aef1ce2cd404e2f07f7a0148c65d1d8ad50e8e28a9851d3e1921c0c"},
  "penalizacao": {"caminho": "configuracoes/penalizacao_mamba_001.json", "sha256": "08b478a2da8bb28f5fe07f5fe1a8ea4b439fac80b3ef01dff1b0d99460d47d90"},
  "prenorm": {"caminho": "configuracoes/normalizacao_mamba_001.json", "sha256": "2007953b95eb6cf6f7dd19e57ab785115765a2c704c736c5392220e54bb37b32"},
  "r0": {"caminho": "configuracoes/treinamento_ohlcv24_001.json", "sha256": "25b4d7cb28efc723dc2390490c744366816390142354e060a6ae8421259c4724"},
  "entradas-r0": {"caminho": "configuracoes/entradas_ohlcv24_001.json", "sha256": "92c2ed229a56bfb223de2f0bb8369d491cbf4fc73bcbe79e408ea4f4de3c27d0"},
  "protocolo-ohlcv": {"caminho": "dados/experimentos/ohlcv_modular_ab5baf3eab3a2e66d8b2/protocolo.md", "sha256": "dbd1d9d1638fda1652a0fb46f770632921eb55c8f369e5d6668f19847a3877fa"},
  "estado8": {"caminho": "configuracoes/mamba_estado8_001.json", "sha256": "0afa359b15f298c0ff315c8d8e45e1c64f0a0dbcbf610a434ab677a187649227"},
  "estado32": {"caminho": "configuracoes/mamba_estado32_001.json", "sha256": "4683348fa4b7db23205cb0fe080274d147aed7750cef2c7e82692c25cde3e571"},
  "estado64": {"caminho": "configuracoes/mamba_estado64_001.json", "sha256": "1975f83c267a7054c753f2e4e34c378bd12504486ab8ffdf3e24b9c7bfa07c8c"},
  "complemento": {"caminho": "configuracoes/mamba_estado16_complemento_001.json", "sha256": "6c5370aaed8cba7b34a18f72f347837e9743726ccf749739fc07932f235abbea"},
  "taxa": {"caminho": "configuracoes/mamba_taxa0001_estado16_001.json", "sha256": "c8c6218c3ed2e30b6013d10c82f82e5d62604650cd95eb607bdd0330200e55a2"},
  "crypto": {"caminho": "configuracoes/cryptomamba_adaptado_001.json", "sha256": "3291902d7f206a3aa8e71258d2aec79de4ea43c2d978d06817ff404c642c9639"},
  "carteira": {"caminho": "configuracoes/backtest_carteira_001.json", "sha256": "90c49786892452830ed4cdf3a8589bbd9a2f8e0283325ad7c708b7a025c530b1"},
  "adamw": {"caminho": "configuracoes/cryptomamba_adamw_001.json", "sha256": "fc0eaacfe9ccd7a2994277f82079b5a9ed64af2b4dc2c6c55034c6fa824832e4"},
  "dinamica": {"caminho": "configuracoes/mamba16_taxa_dinamica_001.json", "sha256": "33cc850086a506233fd3e2ecb54bb274d9c6caaa2a31f7abbad0d88e0cd6ca5e"},
  "huber": {"caminho": "configuracoes/mamba16_perda_huber_001.json", "sha256": "9025f321143149a2f33c37699400be66ab92b6196aaf42cbd3c815016a64aaf3"},
  "blocos": {"caminho": "configuracoes/huber_blocos_001.json", "sha256": "d1de35d0899e08052653a4db4f26e4fa3729047c0a52931b5226a6c9e8b5d841"},
  "entradas": {"caminho": "configuracoes/entradas_niveis_001.json", "sha256": "0e2bcb422e3cfea8e8deaa8c9eb7f17eaea825e20d59bee2cfc531d50896e8b4"},
  "crua-huber": {"caminho": "configuracoes/crua_huber_001.json", "sha256": "557dfd4d065f36b7b7afe3102ba6568a965734214ad64e0e77146d1d1b374051"},
  "astra1-config": {"caminho": "configuracoes/busca_astra_001.json", "sha256": "03dbc1df353330e20ccfbb25038fd3caeef065a8525642f7c704505ae773861e"},
  "astra1-candidatas": {"caminho": "dados/experimentos/busca_astra_b34bad73d6cef1d10a97/candidatas.json", "sha256": "9acc851a72892b730ca78aee270a8085b20081e4c6d03e94e90cd900d7cbe943"},
  "astra1-ajustes": {"caminho": "dados/experimentos/busca_astra_b34bad73d6cef1d10a97/ajustes.json", "sha256": "717b90966ddc9746ba9cb33e16e6c2c306ea0d87f39a221af08870481db6c9e9"},
  "protocolo-astra1": {"caminho": "docs/protocolo_busca_astra.md", "sha256": "3b657576a124437a61c2ecb34f76c760ac72f3dd86416bef542c8aac888e80f6"},
  "comparacao-astra": {"caminho": "configuracoes/comparacao_astra_crua_001.json", "sha256": "46ce372522f4717624fde0e939dec4adc5a0fac428bfdfb804dd9403b95688f8"},
  "f01": {"caminho": "configuracoes/futuros_001.json", "sha256": "67bc314051238c04a87608c9e12c77682e2110a2cc7d0377656ae79448d6f7a6"},
  "f02": {"caminho": "configuracoes/smart_mercados_001.json", "sha256": "e4d82b2fb602090fef0c23ce2baffafac16b3f2006c4873d965be9e90ec6736d"},
  "f03": {"caminho": "configuracoes/revisao_operacional_001.json", "sha256": "7b3230c026490cc83bcdb3f5ebc08ccc97b77a26b6095166767a4d3b10a073c7"},
  "astra2-config": {"caminho": "configuracoes/busca_astra_002.json", "sha256": "06afdf05ed9752df57f2151d79e54e06a18618fbe6d88da641c1231b1effdcf0"},
  "astra2-ajustes": {"caminho": "dados/experimentos/busca_astra_002_932da51c61935c911ec5/ajustes.json", "sha256": "5d3a6b3870c3a84009b9e23ea64a586b7d7eea1fcc4974fe3649d7606f99ed64"},
  "astra2-propostas": {"caminho": "dados/experimentos/busca_astra_002_932da51c61935c911ec5/propostas.json", "sha256": "ad7184b8b961fa93c659dc7987475337c946140d825ae8db23780a82bfd14b64"},
  "protocolo-astra2": {"caminho": "docs/protocolo_busca_astra_002.md", "sha256": "183199162a902ff303b0fee0b92b5b8a639b08845e02abc3211ecfc264db2ab5"},
  "operacional-congelamento": {"caminho": "dados/experimentos/operacional_futuros_f0dd11f393b5e26edaf8/congelamento.json", "sha256": "aa27a70c539e39953dc391e2685a778b606f6506cbc302c1fca2031e34946554"},
  "operacional-receitas": {"caminho": "dados/experimentos/operacional_futuros_f0dd11f393b5e26edaf8/receitas.json", "sha256": "e8f405e4dd1472ff74850753449e4c407598d2c965fc2ccaad05495ca1b3a95c"},
  "protocolo-operacional": {"caminho": "docs/desenho_operacional_futuros.md", "sha256": "05b4e9ccfeadf7a620e80a26fbb5bcd6dd433608b4b7e044d007a372a85145b9"},
  "historico": {"caminho": "configuracoes/historico_treino_001.json", "sha256": "fddfe3b8698ea7011355670746597c74863491d6f6655d06d1ee9c162be83e5a"},
  "protocolo-historico": {"caminho": "docs/protocolo_historico_treino.md", "sha256": "43333ebaea018a816a8f6f7e5b80df01b87bf54e0adeaf52c6168a70d7639f86"},
  "diario": {"caminho": "configuracoes/cryptomamba_reproducivel_001.json", "sha256": "8727bfabf16021074f121e7283343c524f7d8667875e0d9076bb70e4620cb064"},
  "diario-primeiro": {"caminho": "configuracoes/cryptomamba_diario_001.json", "sha256": "c8adcba2bc9b8c141c94c775c099a61e413fcdf81915d9c8428ed1549f378557"},
  "alvo": {"caminho": "configuracoes/alvo_retorno_diario_001.json", "sha256": "41dec3f40fcb5e7cfe8274b13b89fe42abda55eafc547ff223bfb99237b2610e"},
  "padronizado": {"caminho": "configuracoes/padronizacao_diaria_001.json", "sha256": "60d37a1b823976261f9e7d5b8a15fbfe632ccb0be20ae7c74ae8379ad0091981"},
  "sem-penalizacao": {"caminho": "configuracoes/sem_penalizacao_diaria_001.json", "sha256": "b1523a60e37d7fe04c9b0d389d915926214d22d096e0f9bd31e01174672e8ca3"},
  "protocolo-diario": {"caminho": "docs/protocolo_cryptomamba_diario.md", "sha256": "30cfaa1beee93c270e3a4e87f4443d92a6a771cc21c3e30522bfd7de5fbc6b2a"},
  "protocolo-reproducivel": {"caminho": "docs/protocolo_cryptomamba_reproducivel.md", "sha256": "032a974de5fdcf899b8806be5e3308d45c23d5bb86055538fb621e02f1ae0e1f"},
  "protocolo-alvo": {"caminho": "docs/protocolo_alvo_retorno_diario.md", "sha256": "e11138b1cb272fab34ae94b50f39b5edb88838f498da4755983f347f707bdab6"},
  "protocolo-padronizado": {"caminho": "docs/protocolo_padronizacao_diaria.md", "sha256": "ae84426c88201c65b623272d1100bf387d17deebde27b776b8c60b51ce8c4c3a"},
  "protocolo-sem": {"caminho": "docs/protocolo_sem_penalizacao_diaria.md", "sha256": "7c9560f1474b9aa505ff9363da54db5092bdc489e705aaae317e176bb556238c"},
  "moedas": {"caminho": "dados/experimentos/generalizacao_moedas_1f2b005888361d23c111/congelamento.json", "sha256": "f385eadbdb4742ff298bacf42f2d57057c488530712eefdc3e4c15d454941074"},
  "protocolo-moedas": {"caminho": "docs/protocolo_generalizacao_moedas.md", "sha256": "26c64a6313722c915ce5c72cbabd2db181b32f1178645a83df67819f895749fd"},
};
export function fontesFichas(): Record<string, string> {
  return Object.fromEntries(Object.values(fontes).map(f => [f.caminho, f.sha256]));
}

const seeds3 = '17 / 42 / 2026';
const seeds6 = `${seeds3} / 7 / 123 / 31415`;
const seeds8 = `${seeds6} / 271828 / 161803`;
const blocos = 'B1: T jan/2021–set/2023, V out–dez/2023, S jan–jun/2024; B2: T até mar/2024, V abr–jun/2024, S jul–dez/2024; B3: T até set/2024, V out–dez/2024, S jan–jun/2025; B4: T até mar/2025, V abr–jun/2025, S jul–dez/2025. Fins exclusivos em UTC.';
const recortes = 'D1: T jan/2021–set/2022, V out–dez/2022, C jan–mar/2023, S abr–jun/2023; D2: T até dez/2022, V jan–mar/2023, C abr–jun/2023, S jul–set/2023; D3: T até mar/2023, V abr–jun/2023, C jul–set/2023, S out–dez/2023.';
const entradasRelativas: Campos = {
  'entrada.mercado': 'Binance Spot', 'entrada.moedas': 'BTCUSDT',
  'entrada.fonte': 'Arquivos oficiais Binance de 1 minuto; agregação apenas de horas completas, sem interpolação.',
  'entrada.candle': '1 hora', 'entrada.origens': 'A cada hora; operação observada separadamente às 00h UTC',
  'entrada.contexto': '168 horas', 'entrada.canais': '5: abertura, máxima, mínima, fechamento e volume-base',
  'entrada.representacao': 'ln(O/C anterior), ln(H/C anterior), ln(L/C anterior), ln(C/C anterior), ln(1+V)',
  'entrada.escala': 'Z-score por canal, ajustado somente nas horas únicas do treino; escala zero vira 1.',
  'entrada.alvo': 'Log-retorno terminal em 24 horas: ln(C futuro/C atual)',
  'entrada.escala_alvo': 'Média e desvio dos alvos de treino; métricas após inverter a escala.',
  'entrada.purga': 'Alvos com destino na fronteira ou depois são removidos; passado anterior pode compor a janela.',
  'entrada.aquecimento': 'Contexto completo e causal; sem acrescentar futuro às entradas.',
  'entrada.qualidade': 'Candles incompletos e lacunas preservados; sem inventar preços.',
  'modelo.familias': 'Mamba-1 oficial; referências LSTM, Naive e ARIMA herdadas quando identificadas.',
  'modelo.eixo': 'Tempo: cada token é uma hora', 'modelo.estrutura': 'Projeção 5→32; 2 blocos Mamba; cabeça linear escalar',
  'modelo.estado': '16', 'modelo.convolucao': '4', 'modelo.expansao': '2', 'modelo.dropout': '0,1',
  'modelo.normalizacao': 'Pré-LayerNorm com conexão residual: x + Mamba(LN(x))',
  'modelo.leitura': 'Último instante da janela', 'modelo.auxiliar': 'Nenhuma variável fora dos canais', 'modelo.ganho': '1 · sem contração da saída',
  'treino.execucao': 'Pesos novos, independentes por ajuste; referências herdadas não são novos treinos.',
  'treino.otimizador': 'AdamW', 'treino.taxa': '0,0002', 'treino.decay': '0,001',
  'treino.isencoes': 'Parâmetros marcados _no_weight_decay (A_log e D) isentos; demais recebem penalização.',
  'treino.parametros_adam': 'Betas 0,9 / 0,999; epsilon 1e−8', 'treino.scheduler': 'Taxa constante',
  'treino.perda': 'MSE no alvo padronizado', 'treino.lote': '64 / 32 · acumulação de gradientes',
  'treino.clipping': 'Norma máxima 1', 'treino.epocas': 'Até 100; parar após 10 épocas sem melhora de validação.',
  'treino.precisao': 'FP32 em CUDA; Mamba-1 oficial, sem fallback; recarga exata por ajuste.',
  'avaliacao.calendario': 'T jan/2021–dez/2023; V 2024; teste 2025 · divisão fixa',
  'avaliacao.selecao': 'Menor MSE de validação em log-retorno real; primeiro checkpoint em empate.',
  'avaliacao.promocao': 'Critério predefinido de cada contraste; não escolher por lucro de teste.',
  'avaliacao.seeds': seeds3, 'avaliacao.controles': 'Qualificação CUDA, recarga exata; controles reais conforme cada rodada.',
  'avaliacao.referencias': 'Naive: retorno zero. ARIMA(p,1,q), p/q 0–2, sem deriva; parâmetros só no treino, estado filtrado causal. LSTM: 2 camadas, largura 32, dropout 0,1.',
  'avaliacao.agregacao': 'Média de métricas dos modelos individuais; não ensemble.',
  'avaliacao.incerteza': 'Bootstrap temporal: 2.000 réplicas, blocos 14 dias; sensibilidades 7 e 28 dias.',
  'avaliacao.exposicao': '2024 e 2025 já consultados; comparação retrospectiva.',
  'operacao.lados': 'Spot: comprado ou caixa; sem venda descoberta',
  'operacao.decisao': '00h UTC; entrada no minuto seguinte', 'operacao.saida': 'Encerramento após 24 horas, com nova entrada independente no dia seguinte.',
  'operacao.filtro': 'Retorno previsto acima do limiar fixo de custos de ida e volta; sem ajuste pelo teste.',
  'operacao.capital': '10.000 USDT por carteira', 'operacao.tamanho': 'Até 100% do patrimônio, sem alavancagem',
  'operacao.comissao': 'Base 0,10%; estresse 0,20%', 'operacao.slippage': 'Base 0,05%; estresse 0,10%',
  'operacao.funding': 'Não se aplica a Spot', 'operacao.risco': 'Marcação por minuto; convenções de simulação não certificam execução real.',
  'operacao.cenarios': 'Custos base e agravados; caixa e compra sistemática como referências.',
  'operacao.calibracao': 'Política fixa; não calibrada pelo lucro de teste.',
};

function treinoConfigurado(c: Json): Campos {
  const t = o(c.treino), ot = o(c.otimizador);
  return {
    'treino.otimizador': typeof ot.nome === 'string' ? ot.nome : 'AdamW',
    'treino.taxa': numero(t.taxa_aprendizado), 'treino.decay': numero(t.weight_decay),
    'treino.lote': `${numero(t.batch)} / ${numero(t.microbatch)} · acumulação de gradientes`,
    'treino.clipping': `Norma máxima ${numero(t.clipping)}`,
    'treino.epocas': `Até ${numero(t.epocas)}; parar após ${numero(t.paciencia)} épocas sem melhora de validação.`,
  };
}
function modeloConfigurado(c: Json): Campos {
  const m = o(c.mamba);
  return { 'modelo.estado': numero(m.estado), 'modelo.convolucao': numero(m.convolucao), 'modelo.expansao': numero(m.expansao), 'modelo.dropout': numero(m.dropout), 'modelo.estrutura': `Projeção 5→${numero(m.largura)}; ${numero(m.camadas)} blocos Mamba; cabeça linear escalar` };
}

export async function carregarFichas(leitor: (arquivo: string) => Promise<Uint8Array> = arquivo => readFile(arquivo)): Promise<CatalogoFichas> {
  const raiz = path.resolve(process.cwd(), '..');
  const dados: Record<string, unknown> = {}, estados: Record<string, FichaModelo['integridade']> = {};
  await Promise.all(Object.entries(fontes).map(async ([id, f]) => {
    try {
      const bytes = await leitor(path.join(raiz, f.caminho));
      if (createHash('sha256').update(bytes).digest('hex') !== f.sha256) throw new Error('Fonte divergente');
      dados[id] = f.caminho.endsWith('.json') ? JSON.parse(Buffer.from(bytes).toString('utf8')) : Buffer.from(bytes).toString('utf8');
      estados[id] = 'conferida';
    } catch (erro) { estados[id] = (erro as NodeJS.ErrnoException).code === 'ENOENT' ? 'ausente' : 'divergente'; }
  }));
  const c = (id: string) => o(dados[id]);
  const fichas: Record<string, FichaModelo> = {};
  function nova(id: string, nome: string, grupo: string, referencia: string | null, campos: Campos, origem: string[], nota = '') {
    const integridade = origem.some(f => estados[f] === 'divergente') ? 'divergente' : origem.some(f => estados[f] !== 'conferida') ? 'ausente' : 'conferida';
    fichas[id] = { id, nome, grupo, referencia, nota, campos: integridade === 'conferida' ? campos : {}, fontes: [...new Set(origem.map(f => fontes[f]?.caminho).filter(Boolean))], integridade };
    return fichas[id];
  }
  function derivar(id: string, nome: string, grupo: string, pai: string, mudancas: Campos, origem: string[], nota = '') {
    const p = fichas[pai];
    const herdadas = Object.entries(fontes).filter(([, f]) => p?.fontes.includes(f.caminho)).map(([id]) => id);
    const ficha = nova(id, nome, grupo, pai, { ...p?.campos, ...mudancas }, [...herdadas, ...origem], nota);
    if (!p || p.integridade !== 'conferida') { ficha.integridade = p?.integridade ?? 'ausente'; ficha.campos = {}; }
    return ficha;
  }

  nova('barreiras', 'Grade inicial · Mamba, LSTM e AR(1)', 'Primeiro estudo', null, {
    ...entradasRelativas, ...treinoConfigurado(c('barreiras')),
    'entrada.moedas': 'BTCUSDT / ETHUSDT / BNBUSDT / XRPUSDT', 'entrada.contexto': '24 ou 168 horas',
    'entrada.origens': 'A cada hora', 'entrada.alvo': '3 classes: barreira inferior primeiro, prazo esgotado, barreira superior primeiro; prazos 1 / 24 / 168 horas.',
    'entrada.escala_alvo': 'Classes, sem padronização do rótulo', 'entrada.purga': 'Prazo máximo de 168 horas, mais latência; mesma purga para os 3 horizontes.',
    'entrada.aquecimento': '168 retornos para volatilidade, mesmo no contexto de 24h; desvio amostral (ddof 1), distância d = sigma × raiz(H), multiplicadores 1/1.',
    'modelo.familias': 'Mamba-1, LSTM e AR(1) probabilístico · 4.096 trajetórias por origem',
    'modelo.estrutura': 'Projeção 5→32; 2 blocos; último estado + auxiliar → cabeça 33→3',
    'modelo.normalizacao': 'Pós-LayerNorm: LN(x + Mamba(x)); LayerNorm final',
    'modelo.leitura': 'Softmax de 3 logits', 'modelo.auxiliar': 'ln(distância da barreira), padronizado só no treino',
    'treino.isencoes': 'AdamW com penalização uniforme na implementação histórica', 'treino.perda': 'Cross-entropy sem pesos de classe ou oversampling',
    'avaliacao.calendario': 'Somente desenvolvimento DB1–DB4 de 2023; treino expansivo desde jan/2021, validações trimestrais anteriores. Avaliação final não executada nesse ciclo.',
    'avaliacao.seeds': '42', 'avaliacao.selecao': 'Menor log-loss de validação; primeira época em empate',
    'avaliacao.referencias': 'LSTM nas mesmas entradas; AR(1) com resíduos gaussianos e 4.096 trajetórias; frequências de treino suavizadas.',
    'avaliacao.agregacao': '192 ajustes neurais, 16 AR(1), 96 células; não confundir grade executada com plano de avaliação futura.',
    'avaliacao.exposicao': '2023: desenvolvimento exploratório',
    'operacao.saida': 'Primeiro toque ou prazo; ambiguidade no mesmo minuto: barreira inferior primeiro.',
    'operacao.filtro': 'p(superior) ≥ 0,60 e ganho nominal líquido positivo pelo filtro conservador.',
    'operacao.tamanho': 'Risco nominal no stop de até 1% do patrimônio; investimento limitado ao caixa.',
  }, ['barreiras', 'protocolo-barreiras'], 'Estudo de classificação. Não comparar sua log-loss diretamente com MSE de retorno.');

  nova('retorno-original', 'Retorno24 · comparação das quatro famílias', 'Comparação ampla', 'barreiras', {
    ...entradasRelativas, ...treinoConfigurado(c('retorno24')),
    'entrada.moedas': 'BTCUSDT / ETHUSDT / BNBUSDT / XRPUSDT', 'entrada.contexto': '24 / 72 / 168 / 336 horas',
    'entrada.canais': '1: retorno logarítmico horário do fechamento', 'entrada.representacao': 'ln(C atual/C anterior)',
    'entrada.escala': 'Z-score por moeda/bloco nos retornos únicos usados por W336; mesma escala entre contextos.',
    'entrada.aquecimento': '336 retornos válidos; população comum entre contextos e moedas.',
    'modelo.estrutura': 'Projeção 1→32; 2 blocos Mamba; cabeça linear escalar',
    'modelo.normalizacao': 'Pós-LayerNorm: LN(x + Mamba(x))',
    'treino.isencoes': 'AdamW com penalização uniforme na implementação histórica',
    'avaliacao.calendario': `Desenvolvimento DB1–DB4 em trimestres de 2023. Avaliação expansiva: ${blocos}`,
    'avaliacao.controles': 'Qualificação das duas redes e quatro contextos; recarga exata dos ajustes.',
    'avaliacao.agregacao': 'Média entre seeds em cada célula; depois peso igual entre moedas, contextos e blocos. Desenvolvimento e avaliação separados.',
    'avaliacao.exposicao': 'Referência predefinida antes da avaliação; 2024–2025 ficaram conhecidos após sua abertura.',
  }, ['retorno24', 'protocolo-retorno']);
  derivar('penalizacao', 'Mamba · isentar A_log e D da penalização', 'Comparação ampla', 'retorno-original', {
    'treino.isencoes': entradasRelativas['treino.isencoes'],
    'treino.execucao': '384 novos Mamba + 2 controles; LSTM, Naive e ARIMA herdados.',
    'avaliacao.controles': '2 controles reais: BTC/DB1/42, contextos 24 e 336; mesma época e limites de reprodução publicados.',
    'avaliacao.exposicao': entradasRelativas['avaliacao.exposicao'],
  }, ['penalizacao']);
  derivar('prenorm', 'Mamba · pré-LayerNorm', 'Comparação ampla', 'penalizacao', {
    'modelo.normalizacao': entradasRelativas['modelo.normalizacao'],
    'treino.execucao': '384 novos Mamba + 2 controles; outras famílias herdadas.',
  }, ['prenorm']);

  nova('r0', 'R0 · OHLCV relativo', 'Receitas OHLCV', 'prenorm', {
    ...entradasRelativas, ...treinoConfigurado(c('r0')), ...modeloConfigurado(c('r0')),
    'avaliacao.controles': 'Mamba e LSTM: seed 42 repetida; 6 ajustes principais + 2 controles; Naive e seleção ARIMA.',
  }, ['r0', 'entradas-r0', 'protocolo-ohlcv']);
  derivar('desenho', 'Preparação do desenho OHLCV', 'Receitas OHLCV', 'prenorm', {
    'treino.execucao': 'Marco de preparação e qualificação; nenhum treinamento de mercado nesta etapa.',
    'avaliacao.controles': 'Ensaios de contrato e CUDA antes do treino; não são resultados de mercado.',
  }, ['r0'], 'Configuração planejada para R0, apresentada como desenho, não como modelo já treinado.');
  // O desenho tem os mesmos parâmetros planejados de R0, sem atribuir-lhe pesos.
  fichas.desenho.campos = fichas.desenho.integridade === 'conferida' ? { ...fichas.r0.campos, 'treino.execucao': 'Marco de preparação e qualificação; nenhum treinamento de mercado nesta etapa.', 'avaliacao.controles': 'Ensaios de contrato e CUDA antes do treino; não são resultados de mercado.' } : {};
  for (const n of [8, 32, 64]) derivar(`estado${n}`, `Mamba · estado ${n}`, 'Receitas OHLCV', 'r0', {
    ...modeloConfigurado(c(`estado${n}`)),
    'avaliacao.seeds': seeds6, 'avaliacao.controles': 'Reprodução sintética e recarga exata; sem controle real extra nessa extensão.',
    'avaliacao.agregacao': '3 seeds comuns no primeiro contraste; 6 seeds descritivas da candidata. Pareamento completo só após o complemento do estado 16.',
  }, [`estado${n}`]);
  derivar('complemento', 'Estado 16 · complemento para seis seeds', 'Receitas OHLCV', 'r0', {
    'avaliacao.seeds': seeds6, 'treino.execucao': '3 novos ajustes do estado 16; demais estados e 3 seeds originais herdados.',
    'avaliacao.agregacao': 'Estados 8 / 16 / 32 / 64 com 6 seeds; mesmas origens.',
  }, ['complemento']);
  for (const n of [8, 16, 32, 64]) derivar(`taxa${n}`, `Estado ${n} · taxa 0,0001`, 'Taxa menor', n === 16 ? 'complemento' : `estado${n}`, {
    'treino.taxa': '0,0001', 'avaliacao.seeds': seeds6,
    'avaliacao.agregacao': '6 pares por estado; 24 novos ajustes no conjunto; quatro contrastes com IC98,75%.',
  }, ['taxa']);
  derivar('crypto', 'CryptoMamba adaptado · Adam', 'Receitas OHLCV', 'complemento', {
    ...treinoConfigurado(c('crypto')),
    'modelo.familias': 'CryptoMamba adaptado; referências anteriores herdadas',
    'modelo.eixo': 'Canais: 5 tokens; contexto temporal 168 é projetado para 14 dimensões.',
    'modelo.estrutura': 'Projeção temporal 168→14; larguras 14→16→32→1; 3 C-Blocks × 4 CMBlocks; merge 5→1 · 139.317 parâmetros',
    'modelo.estado': '64', 'modelo.dropout': '0', 'modelo.normalizacao': 'Pré-LayerNorm eps 1e−5, residual em cada CMBlock',
    'modelo.leitura': 'Merge dos canais e saída escalar',
    'treino.isencoes': 'Adam: decay L2 global, inclusive parâmetros marcados; marcadores não são tratados automaticamente.',
    'treino.scheduler': 'StepLR: metade da taxa a cada 10 épocas',
    'treino.perda': 'RMSE por lote no alvo padronizado; raiz com epsilon 1e−8',
    'avaliacao.seeds': seeds6, 'avaliacao.controles': 'Reprodução sintética e recarga exata; 6 ajustes, sem repetição real adicional.',
  }, ['crypto'], 'Receita composta: várias alterações simultâneas, não uma ablação de um único fator.');
  derivar('carteira', 'Políticas Spot · sinais Mamba16', 'Política Spot', 'complemento', {
    'modelo.familias': 'Mamba16, 6 seeds, pesos herdados; outras famílias em fichas separadas.',
    'treino.execucao': 'Zero treino novo; reutilização de previsões e checkpoints preservados.',
    'operacao.saida': 'Smart e Vanilla retêm e ajustam a posição; diária24 encerra a cada dia.',
    'operacao.filtro': 'Smart: escala heurística de 2%, que não é stop. Vanilla: limiar 1%.',
    'operacao.instrumento': 'Spot: passo 0,00001 BTC; mínimo 5 USDT.',
    'operacao.cenarios': '369 simulações; ideal, base e agravado; controles de previsão constante e comprar/manter.',
    'avaliacao.agregacao': 'Carteiras independentes por modelo/seed e período; não somar retornos.',
  }, ['carteira'], 'Os modelos têm receitas diferentes. Selecione as fichas de cada arquitetura na fase OHLCV para ver seus pesos de origem.');
  derivar('carteira-crypto', 'Políticas Spot · sinais CryptoMamba', 'Política Spot', 'crypto', {
    ...Object.fromEntries(Object.entries(fichas.carteira.campos).filter(([k]) => k.startsWith('operacao.'))),
    'treino.execucao': fichas.carteira.campos['treino.execucao'],
    'avaliacao.agregacao': fichas.carteira.campos['avaliacao.agregacao'],
  }, ['carteira'], 'Mesmas políticas da ficha Mamba16, aplicadas aos sinais do CryptoMamba adaptado; nenhum retreino.');
  derivar('carteira-lstm', 'Políticas Spot · sinais LSTM', 'Política Spot', 'r0', {
    ...Object.fromEntries(Object.entries(fichas.carteira.campos).filter(([k]) => k.startsWith('operacao.'))),
    'modelo.familias': 'LSTM, 3 seeds, pesos herdados', 'modelo.eixo': 'Tempo: recorrência LSTM unidirecional, estado reiniciado por janela.',
    'modelo.estrutura': 'LSTM com entrada 5, largura 32, 2 camadas; cabeça linear escalar.',
    'modelo.estado': 'Não se aplica d_state do Mamba; hidden size 32.', 'modelo.convolucao': 'Não se aplica à LSTM', 'modelo.expansao': 'Não se aplica à LSTM',
    'modelo.normalizacao': 'Sem LayerNorm ou conexão residual adicional; dropout 0,1 entre camadas.',
    'treino.isencoes': 'Todos os parâmetros da LSTM recebem penalização 0,001; nenhuma isenção Mamba se aplica.',
    'treino.execucao': fichas.carteira.campos['treino.execucao'],
    'avaliacao.agregacao': fichas.carteira.campos['avaliacao.agregacao'],
  }, ['carteira'], 'A LSTM mantém sua arquitetura e suas três seeds originais; não receber os parâmetros internos do Mamba.');
  derivar('adamw', 'CryptoMamba adaptado · AdamW', 'Receitas OHLCV', 'crypto', {
    'treino.otimizador': 'AdamW', 'treino.isencoes': entradasRelativas['treino.isencoes'],
    'operacao.saida': fichas.carteira.campos['operacao.saida'],
    'operacao.filtro': fichas.carteira.campos['operacao.filtro'],
  }, ['adamw']);
  derivar('dinamica', 'Mamba16 · taxa reduzida por estagnação', 'Receitas OHLCV', 'complemento', {
    'treino.scheduler': 'ReduceLROnPlateau: fator 0,5; paciência 2; modo min; threshold absoluto 0; sem cooldown; mínimo 0,000025; epsilon 1e−8.',
    'operacao.saida': fichas.carteira.campos['operacao.saida'],
    'operacao.filtro': fichas.carteira.campos['operacao.filtro'],
  }, ['dinamica']);
  derivar('huber', 'Mamba16 · Huber', 'Receitas OHLCV', 'complemento', {
    'treino.perda': '2 × Huber(delta 1) no alvo padronizado; seleção continua pelo MSE real.',
    'operacao.saida': fichas.carteira.campos['operacao.saida'],
    'operacao.filtro': fichas.carteira.campos['operacao.filtro'],
  }, ['huber']);
  for (const perda of ['mse', 'huber']) derivar(`blocos-${perda}`, `Quatro blocos · ${perda === 'mse' ? 'MSE' : 'Huber'}`, 'Avaliação em blocos', perda === 'mse' ? 'complemento' : 'huber', {
    'avaliacao.calendario': blocos, 'avaliacao.seeds': seeds8,
    'avaliacao.controles': 'B1/42: 2 controles reais, um por perda; 64 ajustes principais no conjunto.',
    'avaliacao.agregacao': 'Peso igual entre 4 blocos; média de 8 seeds por bloco. Ensemble separado.',
    'avaliacao.incerteza': 'Bootstrap pareado de seeds e tempo, 2.000 réplicas; 14 dias principal, 7/28 sensibilidades.',
    'operacao.saida': 'Smart retida e diária24, separadas por bloco',
  }, ['blocos']);
  for (const variante of ['crua', 'padronizada']) derivar(`entradas-${variante}`, `Entradas ${variante === 'crua' ? 'cruas' : 'em níveis padronizados'} · MSE`, 'Representação de entrada', 'blocos-mse', {
    'entrada.representacao': 'O, H, L, C em USDT; volume em BTC, sem logaritmos',
    'entrada.escala': variante === 'crua' ? 'Sem padronização das entradas' : 'Z-score por canal, ajustado somente nas horas únicas do treino; escala zero vira 1.',
    'avaliacao.controles': '2 controles reais; 64 ajustes novos e 32 referências relativas/MSE herdadas.',
    'avaliacao.incerteza': '3 contrastes; IC98,333% corrigido; bootstrap de seeds/tempo 14 dias, sensibilidades 7/28.',
  }, ['entradas']);
  derivar('crua-huber', 'OHLCV cru + Huber · complemento fatorial', 'Representação de entrada', 'entradas-crua', {
    'treino.perda': fichas.huber.campos['treino.perda'],
    'avaliacao.controles': '1 controle real; 32 ajustes novos, 96 herdados; fatorial relativa/crua × MSE/Huber.',
    'avaliacao.incerteza': '4 contrastes; IC98,75% corrigido; bootstrap de seeds/tempo 14 dias, sensibilidades 7/28.',
  }, ['crua-huber']);

  function receitaAstra(r: Json, segunda = false): Campos {
    const rep = String(r.representacao);
    const extras: string[] = [];
    if (r.indicadores) extras.push('log-retornos 24/168h', 'volatilidades 24/168h (ddof 0)', 'ln(1+V) − média 168h');
    if (r.momentum) extras.push('log-retornos 24/168h');
    if (r.volatilidade) extras.push('volatilidades 24/168h (ddof 0)');
    if (r.volume_relativo) extras.push('ln(1+V) − média 168h');
    const quantidade = 5 + (r.indicadores ? 5 : 0) + (r.momentum ? 2 : 0) + (r.volatilidade ? 2 : 0) + (r.volume_relativo ? 1 : 0);
    return {
      'entrada.contexto': `${numero(r.contexto)} horas`,
      'entrada.canais': `${quantidade}: OHLCV${extras.length ? ' + ' + extras.join('; ') : '; sem indicadores adicionais'}`,
      'entrada.representacao': rep === 'janela_relativa' ? 'ln(O/H/L/C sobre o último close conhecido da própria janela); ln(1+V) com escala dentro da janela.' : rep === 'crua' ? 'O, H, L, C em USDT; volume em BTC, sem logaritmos' : rep === 'log_niveis' ? 'ln(O), ln(H), ln(L), ln(C), ln(1+V)' : entradasRelativas['entrada.representacao'],
      'entrada.escala': rep === 'crua' ? 'Sem padronização das entradas' : rep === 'janela_relativa' ? 'OHLC relativo à própria janela; volume padronizado na janela. Canais extras usam estatísticas de T.' : entradasRelativas['entrada.escala'],
      'entrada.aquecimento': '336 horas comuns, inclusive para contextos menores; janelas com lacunas não são interpoladas.',
      'modelo.estrutura': `Projeção ${quantidade}→${numero(r.largura)}; ${numero(r.camadas)} blocos Mamba; cabeça linear escalar`,
      'modelo.estado': numero(r.estado), 'modelo.dropout': numero(r.dropout),
      'modelo.leitura': r.pooling === 'media' ? 'Média temporal dos estados da janela' : 'Último instante da janela',
      'modelo.ganho': Number(r.ganho_saida) === 1 ? '1 · sem contração da saída' : `${numero(r.ganho_saida)} · contração em retorno real aplicada em cópia após selecionar o checkpoint`,
      'treino.otimizador': texto(r.otimizador), 'treino.taxa': numero(r.taxa), 'treino.decay': numero(r.decay),
      'treino.perda': r.perda === 'huber' ? fichas.huber.campos['treino.perda'] : entradasRelativas['treino.perda'],
      'avaliacao.promocao': segunda ? 'Score médio MSE/Naive em 3 recortes; reforço de seeds antes de promoção. Nenhuma receita elegível: avaliação final e carteiras condicionais não executadas.' : 'Score médio MSE/Naive em D1/D2; reforço de 3 candidatas. C05 foi congelada para avaliação final com 8 seeds e 4 blocos.',
      'operacao.saida': 'Smart retida e diária24, separadas por bloco',
    };
  }
  function ajustesExecutados(jobs: Json[]): Campos {
    const concluidos = jobs.filter(j => j.status === 'concluido');
    const principais = concluidos.filter(j => !j.controle);
    const seeds = [...new Set(principais.map(j => texto(j.seed)))];
    const blocosFeitos = [...new Set(principais.map(j => texto(j.bloco)))];
    return {
      'treino.execucao': `${principais.length} ajustes principais concluídos e ${concluidos.length - principais.length} controle(s) nesta receita/etapa; pesos independentes.`,
      'avaliacao.seeds': seeds.join(' / ') || 'Nenhuma inicialização concluída nesta fonte',
      'avaliacao.agregacao': `Somente ajustes concluídos nos recortes ${blocosFeitos.join(' / ')}; médias pareadas por receita, sem ensemble automático.`,
    };
  }
  const astra1Ids = ['astra1-ref'];
  nova('astra1-ref', 'Astra001 · referência relativa/MSE', 'Busca Astra001', 'blocos-mse', {
    ...fichas['blocos-mse'].campos,
    ...receitaAstra({ representacao: 'relativa', contexto: 168, largura: 32, camadas: 2, estado: 16, dropout: 0.1, pooling: 'ultimo', taxa: 0.0002, decay: 0.001, otimizador: 'AdamW', perda: 'mse', ganho_saida: 1 }),
    'avaliacao.calendario': 'D1: T 2021–2022, V jan–jun/2023; D2: T 2021–jun/2023, V jul–dez/2023. Só a referência e a C05 seguiram aos 4 blocos finais de 2024–2025.',
    'avaliacao.seeds': 'Triagem 42; reforço 17/2026; final 8 seeds: ' + seeds8,
    'avaliacao.controles': 'Referência D1/42 e finalista B1/42 repetidas; mesma época e tolerâncias de reprodução; recarga exata.',
    'avaliacao.incerteza': 'Final: bootstrap seeds/tempo 14 dias; 2 contrastes, IC97,5% corrigido; sensibilidades 7/28.',
  }, ['astra1-config', 'astra1-candidatas', 'astra1-ajustes', 'protocolo-astra1']);
  for (const candidata of lista(dados['astra1-candidatas']).map(o)) {
    const idOriginal = String(candidata.id), id = `astra1-${idOriginal.split('_')[0]}`;
    const receita = o(o(candidata.proposta).receita);
    const ajustes = lista(dados['astra1-ajustes']).map(o).filter(j => String(j.bloco).startsWith('D') && String(j.receita_arquivo).endsWith(`${idOriginal.split('_')[1]}.json`));
    derivar(id, `Astra001 · ${idOriginal.split('_')[0]}${idOriginal.startsWith('C05_') ? ' · desenvolvimento da finalista' : ''}`, 'Busca Astra001', 'astra1-ref', {
      ...receitaAstra(receita), ...ajustesExecutados(ajustes),
      'avaliacao.calendario': 'D1: T 2021–2022, V jan–jun/2023; D2: T 2021–jun/2023, V jul–dez/2023. Esta ficha mostra o desenvolvimento; avaliação final de C05 em ficha separada.',
    }, ['astra1-candidatas', 'astra1-ajustes'], 'A referência indicada é a âncora da busca, não uma alegação de ablação de um fator. Só as inicializações realmente concluídas desta receita são listadas.');
    astra1Ids.push(id);
  }
  derivar('astra1-final', 'Astra001 · C05 na avaliação final', 'Busca Astra001', 'astra1-C05', {
    ...ajustesExecutados(lista(dados['astra1-ajustes']).map(o).filter(j => String(j.bloco).startsWith('B') && String(j.receita_arquivo).endsWith('bb6004b56a2ab40f1ca2.json'))),
    'avaliacao.calendario': blocos, 'avaliacao.seeds': seeds8,
    'avaliacao.agregacao': '4 blocos × 8 seeds por versão, peso igual entre blocos; 32 candidata e 32 referência, além dos controles.',
  }, ['astra1-config']);
  derivar('comparacao-crua', 'Comparação comum · OHLCV cru/Huber', 'Astra × crua no mesmo executor', 'crua-huber', {
    'entrada.aquecimento': fichas['astra1-ref'].campos['entrada.aquecimento'],
    'avaliacao.controles': '2 controles; 32 ajustes principais novos de crua/Huber; Astra final herdada após conferir população e executor.',
    'avaliacao.calendario': blocos, 'avaliacao.seeds': seeds8,
  }, ['comparacao-astra']);
  const politicasIds: string[] = [];
  for (const versao of ['astra', 'crua']) {
    let pai = versao === 'astra' ? 'astra1-final' : 'comparacao-crua';
    for (const etapa of ['f01', 'f02', 'f03']) {
      const cfg = c(etapa), custos = o(cfg.custos);
      const id = `${etapa}-${versao}`;
      derivar(id, `${etapa.toUpperCase()} · sinais ${versao === 'astra' ? 'Astra C05' : 'crua/Huber'}`, 'Políticas Spot e futuros', pai, {
        'treino.execucao': 'Zero treino novo; mesmos sinais Spot transferidos para as simulações.',
        'entrada.mercado': 'Entradas e pesos de Spot; execução comparada em Spot/perpétuos USD-M, conforme o braço.',
        'operacao.lados': etapa === 'f01' ? 'Futuros: comprado ou bilateral; caixa permitido.' : 'Spot comprado; futuros comprado, bilateral e caixa; controles de funding separados em F02.',
        'operacao.saida': etapa === 'f01' ? 'Fecha e reabre posições diariamente; sinal24 e filtrada24.' : etapa === 'f02' ? 'Smart comum retém e ajusta posições; variante com filtro.' : 'Smart revisada; saída integral no sinal contrário; saída + filtro, em braços separados.',
        'operacao.filtro': etapa === 'f03' ? `Entrada filtrada: limiar log ${numero(cfg.limiar_entrada)}; versões não filtradas separadas.` : etapa === 'f02' ? 'Smart: escala 2%, sem ser stop; variante com filtro de custos fixo.' : 'Sinal direto ou filtro de custos fixo; sem seleção por lucro.',
        'operacao.tamanho': 'Nocional máximo 95% do patrimônio, reserva 5%; teto 50.000 USDT em F01; sem busca de alavancagem.',
        'operacao.comissao': etapa === 'f01' ? `Base ${porcento(o(custos.base).taxa)}; agravado ${porcento(o(custos.agravado).taxa)}` : etapa === 'f02' ? 'Iguais: Spot/futuros 0,05%; por mercado: Spot 0,10%, futuros 0,05%; ideal separado.' : 'Spot 0,10%; futuros 0,05%; corrigida a base de cobrança e reversões.',
        'operacao.slippage': etapa === 'f03' ? 'Base 0,05%; estresse 0,15%' : 'Base 0,05%; F01 agravado 0,10%; ideal zero.',
        'operacao.funding': 'Histórico nos eventos; não entra na decisão. F02 inclui braço futuro sem funding para atribuição.',
        'operacao.risco': 'Mark price por minuto e buffer prudencial de 2%; não replica liquidação oficial da Binance.',
        'operacao.instrumento': etapa === 'f03' ? 'Spot: passo 0,00001 BTC / mínimo 10 USDT; futuro: 0,001 BTC / 100 USDT. ReduceOnly, reversão e arredondamento revisados.' : 'Filtros conservadores publicados; futuro com passo 0,001 BTC e mínimo 100 USDT.',
        'operacao.cenarios': `${texto(cfg.simulacoes_total)} carteiras no ciclo; braços e cenários fixados antes da comparação.`,
      }, [etapa], 'Mudança operacional sobre sinais preservados; não atribuir seu efeito à atualização de pesos.');
      politicasIds.push(id); pai = id;
    }
  }
  const astra2Ids: string[] = [];
  const propostas2 = lista(dados['astra2-propostas']).map(o);
  const jobs2 = lista(dados['astra2-ajustes']).map(o);
  const receitas2 = new Map<string, Json>();
  for (const job of jobs2) if (job.status === 'concluido' && typeof job.receita_id === 'string') receitas2.set(job.receita_id, o(job.receita));
  for (const [idOriginal, r] of receitas2) {
    const paiDeclarado = o(propostas2.find(p => p.id === idOriginal)?.proposta).pai;
    const pai = typeof paiDeclarado === 'string' && fichas[`astra2-${paiDeclarado}`] ? `astra2-${paiDeclarado}` : idOriginal === 'R0_crua_huber' ? 'comparacao-crua' : 'astra1-final';
    const id = `astra2-${idOriginal}`;
    derivar(id, `Astra002 · ${idOriginal}`, 'Busca Astra002', pai, {
      ...receitaAstra(r, true),
      ...ajustesExecutados(jobs2.filter(j => j.receita_id === idOriginal)),
      'avaliacao.calendario': 'S1: T 2021–2022, V jan–mar/2023, S abr–jun/2023; S2: T até mar/2023, V abr–jun, S jul–set; S3: T até jun/2023, V jul–set, S out–dez. Final 2024–2025 não executado.',
      'avaliacao.controles': '1 controle de desenvolvimento; 100 ajustes reais no total, incluindo controle.',
      'avaliacao.referencias': 'Âncoras C05 e crua/Huber; Naive zero, média/mediana de T e direção majoritária de T.',
      'operacao.cenarios': 'Nenhuma nova carteira executada: a etapa operacional era condicional à elegibilidade.',
    }, ['astra2-config', 'astra2-ajustes', 'astra2-propostas', 'protocolo-astra2']);
    astra2Ids.push(id);
  }
  const operacionais: string[] = [];
  const receitasOp = c('operacional-receitas');
  for (const [idOriginal, valor] of Object.entries(receitasOp)) {
    const r = o(valor), payoff = r.familia_alvo === 'payoff';
    const canais = 5 + (r.momentum ? 3 : 0) + (r.volatilidade ? 2 : 0) + (r.volume_relativo ? 2 : 0);
    const pai = idOriginal === 'R0' ? 'comparacao-crua' : idOriginal === 'P0' ? 'operacional-R0' : ['C02', 'C03', 'C04', 'C06'].includes(idOriginal) ? 'operacional-C01' : 'operacional-P0';
    const representacao = r.representacao === 'crua' ? 'O, H, L, C em USDT; volume em BTC, sem logaritmos' : r.representacao === 'log_niveis' ? 'ln(O), ln(H), ln(L), ln(C), ln(1+V)' : entradasRelativas['entrada.representacao'];
    const id = `operacional-${idOriginal}`;
    derivar(id, `Futuros · ${idOriginal}${idOriginal === 'C06' ? ' · base do estudo de histórico' : ''}`, 'Busca operacional em futuros', pai, {
      'entrada.mercado': 'BTCUSDT perpétuo linear USD-M; pesos treinados no próprio mercado futuro',
      'entrada.fonte': 'Candles de futuros 1h; negociação e marcação 1min; funding histórico. Dados 2021–2023 para esta exploração.',
      'entrada.canais': `${canais}: OHLCV${r.momentum ? ' + log-retornos 24/72/168h' : ''}${r.volatilidade ? ' + volatilidades 24/168h (ddof 1)' : ''}${r.volume_relativo ? ' + ln(1+V) menos médias móveis 24/168h' : ''}`,
      'entrada.contexto': `${numero(r.contexto_horas)} horas`, 'entrada.representacao': representacao,
      'entrada.escala': r.representacao === 'crua' ? 'Base OHLCV sem escala; canais extras, se presentes, padronizados só em T.' : entradasRelativas['entrada.escala'],
      'entrada.alvo': payoff ? '2 payoffs líquidos unitários: compra e venda, com stop/take/prazo. Não são probabilidades.' : entradasRelativas['entrada.alvo'],
      'entrada.escala_alvo': payoff ? 'Z-score próprio por lado, somente nos alvos de T.' : entradasRelativas['entrada.escala_alvo'],
      'entrada.purga': '1.442 minutos, cobrindo realização de 24h e latência de entrada/saída.',
      'entrada.aquecimento': '336 horas comuns, inclusive para contextos menores; janelas com lacunas não são interpoladas.',
      'modelo.familias': 'Mamba-1 oficial CUDA',
      'modelo.estrutura': `Projeção ${canais}→32; 2 blocos Mamba; cabeça linear de ${payoff ? 2 : 1} saída(s)`,
      'modelo.estado': numero(r.d_state), 'modelo.ganho': '1 · sem contração da saída',
      'treino.execucao': '9 ajustes por receita: 3 recortes × 3 seeds, mais 2 controles no ciclo; 74 ajustes no total.',
      'treino.taxa': numero(r.taxa), 'treino.perda': payoff ? 'MSE médio dos 2 alvos padronizados' : fichas.huber.campos['treino.perda'],
      'avaliacao.calendario': recortes,
      'avaliacao.selecao': payoff ? 'Menor MSE real médio dos 2 payoffs em V; recarga exata antes de C/S.' : entradasRelativas['avaliacao.selecao'],
      'avaliacao.promocao': 'Calmar mediano positivo, crescimento médio positivo com custos base e slippage 2×, pelo menos 2 de 3 recortes positivos e 20 operações por carteira S. Nenhuma finalista.',
      'avaliacao.seeds': '42 / 17 / 2026', 'avaliacao.controles': 'R0 e P0, D1/42: controle real antes das demais execuções.',
      'avaliacao.referencias': 'R0 terminal, P0 payoff, caixa, sempre comprado, sempre vendido e tendência causal EMA24/168.',
      'avaliacao.agregacao': 'Receita × recorte × seed; carteiras independentes. Reforço/final não acionados por inelegibilidade.',
      'operacao.lados': 'Compra, venda ou caixa; uma posição por vez',
      'operacao.decisao': 'Cadências 1h ou 4h, escolhidas em C; latência de 1 minuto',
      'operacao.saida': 'Stop = max(sigma168h × raiz(24), 0,5%); take = 1,5 × stop; prazo máximo 24h; stop primeiro se ambíguo; gaps adversos.',
      'operacao.filtro': payoff ? 'Melhor payoff previsto acima da margem adicional calibrada em C; sem reaprender política em S.' : 'Sinal terminal acima de custos, funding causal estimado e margem adicional; nada de funding futuro no sinal.',
      'operacao.tamanho': 'Risco nominal no stop 0,5% ou 1%; nocional até 95% do patrimônio e 50.000 USDT; sem busca de alavancagem.',
      'operacao.comissao': '0,05%', 'operacao.slippage': 'Base 0,05%; estresses 0,10% e 0,15%',
      'operacao.funding': 'Histórico nos eventos; aproximação adversa identificada quando falta mark exato.',
      'operacao.risco': 'Marcação a mercado; fechamento prudencial se patrimônio/nocional ≤ 2%, reprovando promoção; não é liquidação oficial.',
      'operacao.instrumento': 'Passo 0,001 BTC; tick 0,10 USDT; mínimo 100 USDT; filtros de pesquisa, não tabela histórica certificada.',
      'operacao.cenarios': '1.260 carteiras publicadas no ciclo; base e estresses; comparação econômica após a seleção da época.',
      'operacao.calibracao': '12 políticas em C: margem 0/0,10/0,20% × risco 0,5/1% × cadência 1/4h. Se nenhuma passar, S fica em caixa.',
    }, ['operacional-congelamento', 'operacional-receitas', 'protocolo-operacional'], 'T aprende pesos; V escolhe época; C calibra política; S compara receitas adaptativamente. Não é confirmação independente.');
    operacionais.push(id);
  }
  for (const braco of ['acumulado', 'movel12']) derivar(`historico-${braco}`, `C06 · histórico ${braco === 'acumulado' ? 'acumulado' : 'móvel de 12 meses'}`, 'Histórico de treino', braco === 'acumulado' ? 'operacional-C06' : 'historico-acumulado', {
    'avaliacao.calendario': braco === 'acumulado' ? recortes : 'Mesmo V/C/S de D1–D3; T começa em out/2021, jan/2022 e abr/2022, respectivamente, cobrindo 12 meses até V. Contexto anterior continua permitido.',
    'treino.execucao': '18 ajustes novos: 2 históricos × 3 recortes × 3 seeds; 2 controles adicionais. Sem herança de pesos.',
    'avaliacao.controles': 'D1/42 repetido em cada histórico; ambos aprovados antes de liberar os demais ajustes.',
    'avaliacao.promocao': 'Ablação do início de T; sem busca Astra, janela de 6 meses ou promoção automática.',
    'operacao.decisao': 'Camada principal fixa: a cada 4 horas; latência de 1 minuto',
    'operacao.tamanho': 'Risco nominal 0,5% no stop; demais limites do motor ancestral mantidos.',
    'operacao.filtro': 'Limiar adicional zero na política fixa',
    'operacao.cenarios': '456 carteiras; base, custos 2×/3× e restrições de lado; camada calibrada secundária preservada.',
    'operacao.calibracao': 'Principal: política fixa. Secundária: as 12 políticas do ancestral, escolhidas somente em C.',
  }, ['historico', 'protocolo-historico'], 'Somente o início de T muda entre os históricos; escalas e atualizações por época mudam como consequência. O calendário mantém 6 meses entre o fim de T e o início de S.');

  function camposDiarios(cfg: Json, moeda: string): Campos {
    const t = o(cfg.treinamento), m = o(cfg.arquitetura), op = o(cfg.operacoes), p = o(cfg.periodos);
    const retorno = cfg.alvo === 'retorno_simples_fechamento_seguinte_decimal';
    return {
      'entrada.mercado': 'Perpétuo linear USD-M Binance', 'entrada.moedas': moeda,
      'entrada.fonte': 'Candles diários oficiais Binance Vision com checksum; minutos de negociação/mark e funding separados para a simulação.',
      'entrada.candle': '1 dia UTC completo', 'entrada.origens': 'Diária; não há treinamento com origens horárias nesta receita.',
      'entrada.contexto': `${numero(cfg.contexto_dias)} dias`, 'entrada.canais': '6: timestamp Unix UTC em segundos, Open, High, Low, Close, Volume-base / 1.000.000.000',
      'entrada.representacao': 'Preço em nível (USDT), data como canal efetivo; volume dividido por 1e9 antes de eventual padronização.',
      'entrada.escala': cfg.normalizar ? 'Z-score por canal nos candles únicos das janelas de treino; ddof 0; momentos float64/math.fsum; saída FP32; escala zero vira 1; sem clipping.' : 'Sem padronização das entradas',
      'entrada.alvo': retorno ? 'Retorno simples do fechamento do dia seguinte: C seguinte/C atual − 1, em decimal.' : 'Preço de fechamento do próximo dia em USDT',
      'entrada.escala_alvo': 'Sem padronização do alvo',
      'entrada.purga': 'Janelas de 14 dias construídas dentro de cada partição, sem alvo atravessar a fronteira; última janela possível excluída como no Dataset público.',
      'entrada.aquecimento': 'Primeira origem após 14 candles em cada partição; 351 origens em V e 350 no teste.',
      'entrada.qualidade': 'Sem interpolação; arquivos diários mantidos nas divergências documentadas de volume. Minutos não substituem seletivamente a entrada diária.',
      'modelo.familias': 'CryptoMamba diário adaptado com Mamba-1 oficial',
      'modelo.eixo': 'Canais: 6 tokens; 14 dias são a dimensão inicial de cada token. Não é um scan de 14 tokens temporais.',
      'modelo.estrutura': `3 C-Blocks × ${numero(m.densidade)} CMBlocks; larguras ${lista(m.larguras).map(numero).join('→')}; merge 6→1; sem adapter temporal extra`,
      'modelo.estado': numero(m.estado), 'modelo.convolucao': numero(m.convolucao), 'modelo.expansao': numero(m.expansao), 'modelo.dropout': '0',
      'modelo.normalizacao': `Pré-LayerNorm eps ${numero(m.eps_layernorm)} + conexão residual`, 'modelo.leitura': 'Merge dos 6 canais e saída escalar',
      'modelo.auxiliar': 'Nenhuma variável fora dos canais', 'modelo.ganho': '1 · sem contração da saída',
      'treino.execucao': '3 ajustes principais de pesos independentes + 1 controle; 1.000 épocas por ajuste.',
      'treino.otimizador': texto(t.otimizador), 'treino.taxa': numero(t.taxa), 'treino.decay': numero(t.weight_decay),
      'treino.isencoes': 'Adam: decay L2 global, inclusive parâmetros marcados; marcadores não são tratados automaticamente.',
      'treino.parametros_adam': 'Betas 0,9 / 0,999; epsilon 1e−8',
      'treino.scheduler': `StepLR: fator ${numero(t.scheduler_gamma)} a cada ${numero(t.scheduler_passo)} épocas, ao fim da época`,
      'treino.perda': 'RMSE por lote: sqrt(média dos erros² + 1e−8), na unidade nativa do alvo.',
      'treino.lote': `${numero(t.lote)}; último lote parcial; sem acumulação adicional`, 'treino.clipping': 'Sem clipping de gradientes',
      'treino.epocas': `${numero(t.epocas)} completas, sem parada antecipada; escolher mínimo global em V.`,
      'treino.precisao': 'FP32 em CUDA; scan oficial de referência, sem fused ou fallback; reprodução e recarga exatas.',
      'avaliacao.calendario': `Treino ${texto(lista(p.treino)[0])} até ${texto(lista(p.treino)[1])} exclusivo; validação 2024; teste 2025 · divisão fixa.`,
      'avaliacao.selecao': retorno ? 'Menor RMSE global do retorno em V; primeira época em empate.' : 'Menor RMSE global do preço em V; primeira época em empate.',
      'avaliacao.promocao': 'Nenhuma promoção automática por lucro; referência de menor erro é uma escolha retrospectiva identificada.',
      'avaliacao.seeds': lista(cfg.seeds).map(texto).join(' / '),
      'avaliacao.controles': '42 principal → controle42 → 17 → 2026; mesma época e previsão exata antes de teste/demais seeds.',
      'avaliacao.referencias': 'Naive = último fechamento/retorno zero; sempre comprado e sempre vendido; sem LSTM/ARIMA novos.',
      'avaliacao.agregacao': 'Média aritmética das 3 seeds, controle excluído. Ensemble calcula média das previsões antes do filtro e é avaliado separadamente.',
      'avaliacao.incerteza': 'Bootstrap pareado de seeds/dias: 2.000 réplicas; 14 dias principal e 7/28 de sensibilidade.',
      'avaliacao.exposicao': entradasRelativas['avaliacao.exposicao'],
      'operacao.lados': 'Compra, venda ou caixa; uma posição por vez',
      'operacao.decisao': `Após candle completo; latência ${numero(op.latencia_minutos)} minuto(s), entrada 00:01 UTC`,
      'operacao.saida': '24h após entrada; fecha e pode reabrir pagando custos; sem stop/take.',
      'operacao.filtro': `Compra se retorno previsto > ${porcento(op.filtro_retorno_absoluto)}; venda se < −${porcento(op.filtro_retorno_absoluto)}; caso contrário, caixa. Filtro fixo pelo custo base.`,
      'operacao.capital': `${numero(op.capital_inicial)} USDT por carteira`,
      'operacao.tamanho': `Nocional máximo ${porcento(op.fracao_nocional)} do patrimônio, sem transferência entre carteiras.`,
      'operacao.comissao': porcento(op.comissao_por_lado),
      'operacao.slippage': `Base ${porcento(op.slippage_por_lado)}; estresses ${porcento(Number(op.slippage_por_lado) * 2)} e ${porcento(Number(op.slippage_por_lado) * 3)}`,
      'operacao.funding': 'Histórico nos timestamps reais; [entrada, saída); não entra na decisão.',
      'operacao.risco': `Mark1min, envelope conservador de máximas/mínimas; buffer ${porcento(op.buffer_prudencial)} do nocional; não certifica ticks ou liquidação Binance.`,
      'operacao.instrumento': `Passo ${numero(op.passo_quantidade)}; tick ${numero(op.tick_preco)} USDT; mínimo ${numero(op.nocional_minimo)} USDT${op.quantidade_minima !== undefined ? `; quantidade ${numero(op.quantidade_minima)} a ${numero(op.quantidade_maxima)}` : ''}. Filtros de pesquisa/snapshot, não histórico certificado.`,
      'operacao.cenarios': '70 carteiras: 2 períodos × (3 seeds + ensemble + Naive + sempre comprado + sempre vendido) × 5 cenários; restrições de lado e slippage 2×/3×.',
      'operacao.calibracao': 'Política fixa; sem calibrar filtro em V ou teste.',
    };
  }
  nova('diario', 'Diário · preço · execução reproduzível', 'Receita diária BTC', 'historico-movel12', camposDiarios(c('diario'), 'BTCUSDT'), ['diario', 'protocolo-diario', 'protocolo-reproducivel'], 'Novo desenho composto; não atribuir a diferença somente ao candle diário. A tentativa fused anterior falhou no controle e não produziu teste de 2025.');
  nova('diario-primeiro', 'Diário · primeira tentativa, controle reprovado', 'Receita diária BTC', 'historico-movel12', {
    ...camposDiarios(c('diario-primeiro'), 'BTCUSDT'),
    'treino.execucao': 'Somente 1 principal (seed42) e sua repetição concluídos; as demais seeds e o teste foram bloqueados.',
    'avaliacao.seeds': '42 · principal e controle',
    'treino.precisao': 'FP32 CUDA, caminho fused original; controle real reprovado por reprodução numérica.',
    'avaliacao.controles': 'Seed42 e sua repetição; controle reprovado. Sem média de 3 seeds, teste 2025 ou carteiras.',
    'operacao.cenarios': 'Nenhuma carteira executada nessa tentativa.',
  }, ['diario-primeiro', 'protocolo-diario'], 'Tentativa técnica preservada, sem resultado operacional. Não conta como nova hipótese científica.');
  for (const [id, nome, fonte, pai] of [
    ['alvo', 'Diário · alvo retorno simples', 'alvo', 'diario'],
    ['padronizado', 'Diário · retorno com entradas padronizadas', 'padronizado', 'alvo'],
    ['sem-penalizacao', 'Diário · penalização zero', 'sem-penalizacao', 'padronizado'],
  ]) nova(id, nome, 'Receita diária BTC', pai, camposDiarios(c(fonte), 'BTCUSDT'), [fonte, 'protocolo-diario', fonte === 'alvo' ? 'protocolo-alvo' : fonte === 'padronizado' ? 'protocolo-padronizado' : 'protocolo-sem'], id === 'sem-penalizacao' ? 'Observação dos ramos em marcos predefinidos não interfere na seleção nem altera os pesos.' : 'Comparação de um fator contra a referência indicada; restantes condições mantidas.');
  const moedasCongeladas = o(c('moedas').moedas);
  for (const moeda of ['ETH', 'BNB', 'XRP']) {
    const cfg = o(o(moedasCongeladas[`${moeda}USDT`]).configuracao);
    nova(`moeda-${moeda}`, `${moeda} · receita padronizada independente`, 'Generalização por moeda', 'padronizado', {
      ...camposDiarios(cfg, `${moeda}USDT`),
      'entrada.escala': `Z-score próprio de ${moeda}, ajustado só em seus candles únicos de treino; método idêntico ao BTC padronizado.`,
      'entrada.qualidade': moeda === 'XRP' ? '5 dias de 2022 complementados por API oficial; 2 minutos de mark ausentes em 12/08/2024 mantidos; envelope oficial 5min só para risco. Volume diário preservado nas divergências de jan/2025.' : 'Dias inaugurais incompletos excluídos. Divergências de volume de 14/29 jan/2025 mantêm o arquivo diário oficial; sem substituição seletiva.',
      'treino.execucao': '3 ajustes independentes + controle42 nesta moeda; 12 ajustes na rodada, sem transferência de pesos e sem retreino BTC.',
      'avaliacao.controles': 'Controle42 exato por moeda, antes das demais seeds e do teste. XRP: reinício separado após interrupção, com trajetória anterior preservada.',
      'avaliacao.agregacao': 'Média de seeds e ensemble separados por moeda. Não somar carteiras ou ordenar erros absolutos em USDT entre moedas.',
    }, ['moedas', 'protocolo-moedas'], 'Referência científica: BTC padronizado com decay 0,001. A fase imediatamente anterior sem penalização não foi a receita herdada.');
  }

  const paginas: CatalogoFichas['paginas'] = {
    inicio: ['barreiras'], 'comparacao-modelos': ['retorno-original', 'penalizacao', 'prenorm'],
    'receitas-ohlcv': ['r0', 'estado8', 'estado32', 'estado64', 'complemento', 'taxa8', 'taxa16', 'taxa32', 'taxa64', 'crypto', 'carteira', 'carteira-lstm', 'carteira-crypto', 'adamw', 'dinamica', 'huber', 'blocos-mse', 'blocos-huber', 'entradas-crua', 'entradas-padronizada', 'crua-huber'],
    'buscas-ia': [...astra1Ids, 'astra1-final', 'comparacao-crua', ...politicasIds, ...astra2Ids, ...operacionais],
    'historico-movel': ['historico-acumulado', 'historico-movel12'], 'receita-diaria': ['diario-primeiro', 'diario'],
    'alvo-diario': ['alvo'], 'padronizacao-diaria': ['padronizado'], 'sem-penalizacao': ['sem-penalizacao'], 'outras-moedas': ['moeda-ETH', 'moeda-BNB', 'moeda-XRP'],
    desenho: ['desenho'], r0: ['r0'], estado8: ['estado8'], estado32: ['estado32'], estado64: ['estado64'], complemento: ['complemento'],
    taxa: ['taxa8', 'taxa16', 'taxa32', 'taxa64'], crypto: ['crypto'], carteira: ['carteira', 'carteira-lstm', 'carteira-crypto'], adamw: ['adamw'], dinamica: ['dinamica'], huber: ['huber'], blocos: ['blocos-mse', 'blocos-huber'], entradas: ['blocos-mse', 'entradas-crua', 'entradas-padronizada'],
  };
  const padroes: CatalogoFichas['padroes'] = Object.fromEntries(Object.entries(paginas).map(([id, f]) => [id, f.at(-1)!]));
  padroes.taxa = 'taxa16';
  padroes.carteira = 'carteira';
  padroes['outras-moedas'] = 'moeda-ETH';
  const fases = ['inicio', 'comparacao-modelos', 'receitas-ohlcv', 'buscas-ia', 'historico-movel', 'receita-diaria', 'alvo-diario', 'padronizacao-diaria', 'sem-penalizacao', 'outras-moedas'];
  const testes = ['desenho', 'r0', 'estado8', 'estado32', 'estado64', 'complemento', 'taxa', 'crypto', 'carteira', 'adamw', 'dinamica', 'huber', 'blocos', 'entradas'];
  const anteriores: CatalogoFichas['anteriores'] = {};
  for (const sequencia of [fases, testes]) for (const [i, id] of sequencia.entries()) anteriores[id] = i > 0 ? padroes[sequencia[i - 1]] ?? null : null;
  const custos = await carregarCustos();
  if (custos.situacao === 'vigente') for (const ficha of Object.values(fichas)) {
    const anterior = ficha.campos['operacao.slippage'];
    if (anterior) ficha.campos['operacao.slippage'] = anterior.replaceAll('0,05%', '0,01%').replaceAll('0,10%', '0,02%').replaceAll('0,15%', '0,03%') + ' · execução vigente provisória; filtros históricos mantidos.';
  }
  if (custos.situacao === 'divergente') for (const ficha of Object.values(fichas)) {
    if (ficha.campos['operacao.slippage']) ficha.campos['operacao.slippage'] = 'Reavaliação de custos com integridade pendente.';
  }
  return { fichas, paginas, padroes, anteriores };
}
