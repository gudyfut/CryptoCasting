/** Calculadoras ilustrativas; não alteram nem executam o experimento. */
export const numero = (n: number, casas = 3) => n.toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas });
export const percentual = (n: number, casas = 2) => `${numero(100 * n, casas)}%`;
export const probabilidadeLegivel = (p: number) => p > 0 && p < .00001 ? "<0,001%" : percentual(p, p > 0 && p < .001 ? 3 : 1);
export const prazo = (h: number) => h === 168 ? "7 dias" : h === 24 ? "24 horas" : "1 hora";
export const nomes: Record<string, string> = { mamba: "Mamba", lstm: "LSTM", ar1: "AR(1)", frequencia_treino: "Frequências do treino" };
export function perdas(probabilidades: number[], classe: number) {
  // Tolerância do contrato científico para probabilidades softmax salvas em float32.
  // Não renormalizar: a avaliação individual deve reproduzir os escores originais.
  if (probabilidades.length !== 3 || probabilidades.some(p => !Number.isFinite(p) || p < 0 || p > 1) || Math.abs(probabilidades.reduce((a, b) => a + b, 0) - 1) > 1e-6 || ![0, 1, 2].includes(classe)) throw new Error("Probabilidades inválidas");
  return { logLoss: -Math.log(Math.max(probabilidades[classe], 1e-7)), brier: probabilidades.reduce((s, p, i) => s + (p - Number(i === classe)) ** 2, 0) };
}
export function limites(entrada: number, sigma: number, horas: number) {
  const distancia = sigma * Math.sqrt(horas);
  return { superior: entrada * Math.exp(distancia), inferior: entrada * Math.exp(-distancia), distancia };
}
export function operacaoIlustrativa(alta: number, probabilidade: number, saida: "superior" | "inferior" | "prazo") {
  const capital = 10000, entrada = 100, taxa = .001, deslizamento = .0005;
  const superior = entrada * (1 + alta), inferior = entrada / (1 + alta);
  const retorno = (preco: number) => preco * (1 - deslizamento) * (1 - taxa) / (entrada * (1 + deslizamento) * (1 + taxa)) - 1;
  const retornoSuperior = retorno(superior), retornoInferior = retorno(inferior);
  const viabilidade = probabilidade * retornoSuperior + (1 - probabilidade) * retornoInferior;
  const permitida = probabilidade >= .6 && viabilidade > 0;
  const fracao = permitida ? Math.min(1, .01 / -retornoInferior) : 0;
  const investido = capital * fracao;
  const quantidade = investido / (entrada * (1 + deslizamento) * (1 + taxa));
  const precoSaida = saida === "superior" ? superior : saida === "inferior" ? inferior : entrada * Math.exp(Math.log(1 + alta) * .2);
  const recebimento = quantidade * precoSaida * (1 - deslizamento) * (1 - taxa);
  return { capital, superior, inferior, retornoSuperior, retornoInferior, viabilidade, permitida, fracao, investido, quantidade, precoSaida, recebimento, saldo: capital - investido + recebimento };
}
