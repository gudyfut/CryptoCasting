// Validação leve de resumos para a interface. A auditoria dos parquets é Python.
import type { ResultadoLocal } from "./estudo";

function objeto(valor: unknown): Record<string, unknown> {
  if (typeof valor !== "object" || valor === null || Array.isArray(valor)) throw new Error("Objeto inválido");
  return valor as Record<string, unknown>;
}
function texto(valor: unknown): string {
  if (typeof valor !== "string" || !valor) throw new Error("Texto inválido");
  return valor;
}
function numero(valor: unknown): number {
  if (typeof valor !== "number" || !Number.isFinite(valor)) throw new Error("Número inválido");
  return valor;
}
function inteiro(valor: unknown): number {
  const n = numero(valor);
  if (!Number.isInteger(n) || n < 0) throw new Error("Contagem inválida");
  return n;
}
function opcional(valor: unknown): number | null {
  return valor === null ? null : numero(valor);
}
function conferir(valor: number | null, esperado: number | null) {
  if (valor === null ? esperado !== null : esperado === null || Math.abs(valor - esperado) > 1e-10) throw new Error("Métrica inconsistente");
}
function valorPermitido<T extends string | number>(valor: unknown, permitidos: readonly T[]): T {
  if (!permitidos.includes(valor as T)) throw new Error("Valor fora do protocolo");
  return valor as T;
}
function baConferida(valor: unknown, amostras: number): number | null {
  const metricas = objeto(valor);
  const matriz = metricas.matriz_confusao_linhas_reais_colunas_previstas;
  if (!Array.isArray(matriz) || matriz.length !== 2 || matriz.some((r) => !Array.isArray(r) || r.length !== 2)) throw new Error("Matriz inválida");
  const [[vn, fp], [fn, vp]] = matriz.map((r: unknown[]) => r.map(inteiro));
  const baixa = vn + fp, alta = fn + vp;
  if (baixa + alta !== amostras || inteiro(metricas.amostras) !== amostras || inteiro(metricas.suporte_alta) !== alta || inteiro(metricas.suporte_nao_alta) !== baixa) throw new Error("Suportes divergentes");
  const ba = opcional(metricas.balanced_accuracy);
  conferir(ba, alta > 0 && baixa > 0 ? (vp / alta + vn / baixa) / 2 : null);
  conferir(numero(metricas.accuracy), (vn + vp) / amostras);
  const f1 = (corretos: number) => 2 * corretos + fp + fn === 0 ? 0 : 2 * corretos / (2 * corretos + fp + fn);
  conferir(numero(metricas.f1_macro), (f1(vn) + f1(vp)) / 2);
  return ba;
}

export function interpretarResultado(valor: unknown, pasta: string): ResultadoLocal {
  const registro = objeto(valor);
  const id = texto(registro.id);
  if (!/^[a-f0-9]{20}$/.test(id) || !new RegExp(`^pareado_${id}(_[a-f0-9]{8})?$`).test(pasta)) throw new Error("Identidade inválida");
  if (registro.contrato !== "entregas45-v1" || registro.estado !== "concluido" || registro.tipo_fold !== "desenvolvimento" || registro.protocolo !== "1.6") throw new Error("Contrato/estado inválido");
  const celula = objeto(registro.celula), config = objeto(registro.configuracao);
  const par = valorPermitido(celula.par, ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT"]);
  const granularidade = valorPermitido(celula.granularidade, ["15m", "1h", "4h", "1d"]);
  const contexto = valorPermitido(celula.contexto_dias, [7, 14]);
  const tarefa = valorPermitido(celula.tarefa, ["principal", "proximo_candle"]);
  const fold = valorPermitido(celula.fold, ["D1", "D2", "D3", "D4"]);
  const seed = valorPermitido(celula.seed, [42]);
  if (tarefa === "proximo_candle" && (contexto !== 7 || granularidade === "1d")) throw new Error("Tarefa não canônica");
  for (const [chave, esperado] of Object.entries({ pares: par, granularidades: granularidade, contextos_dias: contexto, folds: fold, seeds: seed })) {
    if (!Array.isArray(config[chave]) || !(config[chave] as unknown[]).includes(esperado)) throw new Error("Célula fora da configuração");
  }
  if (config.tarefa !== tarefa && !(config.tarefa === "proximo_candle" && tarefa === "principal" && granularidade === "1d" && contexto === 7)) throw new Error("Tarefa divergente");
  const features = valorPermitido(config.features, ["ohlcv", "ampliadas"]);
  const normalizador = valorPermitido(config.normalizador, ["standard", "minmax"]);
  const backend = valorPermitido(config.backend_mamba, ["pytorch", "oficial"]);
  const dispositivo = valorPermitido(config.dispositivo, ["cpu", "cuda"]);
  if (backend === "oficial" && dispositivo !== "cuda") throw new Error("Backend incompatível");
  const modelos = objeto(registro.modelos);
  if (objeto(modelos.mamba).backend !== backend || objeto(modelos.lstm).backend !== "torch.nn.LSTM") throw new Error("Backend executado divergente");
  const amostras = inteiro(objeto(registro.contagens).teste);
  if (!amostras) throw new Error("Bloco vazio");
  const avaliacao = objeto(objeto(registro.avaliacoes).teste), metricas = objeto(avaliacao.metricas);
  const ba = { mamba: baConferida(metricas.mamba, amostras), lstm: baConferida(metricas.lstm, amostras), ar1: baConferida(metricas.ar1, amostras) };
  const valores = objeto(avaliacao.diferencas_pp);
  const diferencas = { mamba_menos_ar1: opcional(valores.mamba_menos_ar1), mamba_menos_lstm: opcional(valores.mamba_menos_lstm), mamba_menos_50: opcional(valores.mamba_menos_50) };
  conferir(diferencas.mamba_menos_ar1, ba.mamba === null || ba.ar1 === null ? null : 100 * (ba.mamba - ba.ar1));
  conferir(diferencas.mamba_menos_lstm, ba.mamba === null || ba.lstm === null ? null : 100 * (ba.mamba - ba.lstm));
  conferir(diferencas.mamba_menos_50, ba.mamba === null ? null : 100 * (ba.mamba - .5));
  return { pasta, id, par, granularidade, contexto, tarefa, fold, seed, features, normalizador, backend, dispositivo,
    larguraMamba: valorPermitido(config.largura_mamba, [32, 64]), larguraLstm: valorPermitido(config.largura_lstm, [32, 64]),
    codigo: texto(registro.sha256_codigo), amostras, ba, diferencas };
}
