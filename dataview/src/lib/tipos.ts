export type IndiceSerie = { id:string; par:string; fold:string; contexto:number; seed:number; modelos:string[]; n:number; fase:string; arquivo:string; sha256:string };
export type Metrica = { modelo:string; par:string; fold:string; contexto?:number; seed?:number; fase:string; n:number; mse:number; rmse:number; mae:number; habilidade_mse:number|null; acerto_balanceado_direcional:number|null; epoca:number|null; segundos:number|null };
export type ResumoPortal = { execucao:string; dataset:string; gerado_utc:string; desenvolvimento_completo:boolean; avaliacao_completa:boolean; metricas:Metrica[]; series:IndiceSerie[] };
export type Origem = { tempo:number; destino:number; preco:number; preco_real:number; retorno_real:number; previsoes:Record<string,number> };
export type Preco = { time:number; open?:number; high?:number; low?:number; close?:number; volume?:number };
export type Serie = { id:string; par:string; fold:string; contexto:number; seed:number; modelos:string[]; origens:Origem[]; precos:Preco[]; convencao_tempo:string };
export const nomes:Record<string,string> = { mamba:"Mamba", lstm:"LSTM", arima:"ARIMA", naive:"Naive" };
export const cores:Record<string,string> = { mamba:"#176fba", lstm:"#a8611a", arima:"#8e55a0", naive:"#617482" };
export const numero = (n:number, casas=2) => n.toLocaleString("pt-BR",{minimumFractionDigits:casas,maximumFractionDigits:casas});
export function retornoPercentual(retornoLog:number):string {
  const percentual=Math.expm1(retornoLog)*100;
  if(percentual===0)return '0,00%';
  const tamanho=Math.abs(percentual);
  if(tamanho>0&&tamanho<0.0001)return `${percentual.toExponential(2).replace('.',',')}%`;
  return `${numero(percentual,tamanho>0&&tamanho<0.01?4:2)}%`;
}
export const dataUTC = (n:number) => new Date(n*1000).toLocaleString("pt-BR",{timeZone:"UTC",dateStyle:"short",timeStyle:"short"});
