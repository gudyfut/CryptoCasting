export type Registro = Record<string, unknown>;
export type SerieIndice = { id: string; ciclo: string; celula: string; modelo: string; bloco: string; seed: number | null; n: number; n_horario: number; epoca: number | null; mse: number };
export type DadosPanorama = { gerado_utc: string; publicacoes: Record<string, Registro>; series: SerieIndice[]; fontes: Record<string, string>; natureza: string; custos_vigentes?: Registro };
export type SerieReal = { ciclo: string; celula: string; metricas: Record<string, number>; pontos: [number, number, number, number, number][]; aprendizagem: { epoca: number; mse_validacao: number }[]; epoca_selecionada: number | null; fonte: string; fonte_sha256: string };
export type GrupoMetrica = { chave: string; nome: string };
export type FichaModelo = {
  id: string; nome: string; grupo: string; referencia: string | null; nota: string;
  campos: Record<string, string>; fontes: string[];
  integridade: 'conferida' | 'ausente' | 'divergente';
};
export type CatalogoFichas = {
  fichas: Record<string, FichaModelo>; paginas: Record<string, string[]>;
  padroes: Record<string, string>; anteriores: Record<string, string | null>;
};
export type FasePesquisa = {
  id: string; data: string; titulo: string; pergunta: string; mudanca: string;
  conclusao: string; limite: string; resultado: string; detalhes?: string[];
  receita?: string; fontes?: string[];
};
export type ResultadoDiario = {
  id: string; nome: string; moeda: string; situacao: 'conferido' | 'ausente' | 'divergente';
  fonte: string; hash?: string; fonteOperacional?: string; periodos: {
    ano: number; mse: number | null; erroPreco: number | null; diferencaNaive: number | null;
    retorno: number | null; queda: number | null; acerto: number | null;
    seeds: { seed: string; retorno: number; queda: number }[];
    ensemble: { retorno: number; queda: number; operacoes: number } | null;
  }[];
};
export type EvolucaoPesquisa = {
  fechamento: { situacao: 'conferido' | 'indisponivel' | 'divergente'; data?: string; ajustes?: number; controles?: number; carteiras?: number; fonte?: string; comparacao?: string };
  custos?: { situacao: 'vigente' | 'historico' | 'divergente'; slippage: number };
  observadoEm: string; receitas: ResultadoDiario[]; moedas: ResultadoDiario[];
  estado: {
    situacao: string; registroEm: string | null; moeda: string | null; ajuste: string | null;
    concluidos: number | null; previstos: number | null; epoca: number | null; epocas: number | null;
    recente: boolean;
  };
};
export type Etapa = {
  id: string; capitulo: number; data: string; titulo: string; curto: string; categoria: string;
  pergunta: string; hipotese: string; mudanca: string; constantes: string;
  resumo: string; conclusao: string; resultado: string; destaque: string; unidade: string;
  leitura: string; limite: string; contagem: string; periodo: string; fontes: string[];
  publicacao?: string; grupos?: GrupoMetrica[]; primaria?: 'validacao' | 'teste'; exemplos?: string[];
  visual?: 'metodo' | 'blocos' | 'entradas' | 'carteira' | 'publico' | 'barreiras';
};
export const objeto = (v: unknown): Registro => v && typeof v === 'object' && !Array.isArray(v) ? v as Registro : {};
export const numero = (v: unknown): number | null => typeof v === 'number' && Number.isFinite(v) ? v : null;
export function metrica(pub: Registro, chave: string, fase: string): Registro {
  if (Array.isArray(pub.modelos)) return objeto(pub.modelos.find(x => objeto(x).modelo === chave));
  const grupos = objeto(objeto(pub.medias_globais ?? pub.medias)[fase]);
  const grupo = objeto(grupos[chave]);
  const m = objeto(grupo.metricas ?? grupo);
  return { ...m, mse: m.mse ?? m.mse_medio_seeds };
}
export const formato = (n: number, dec = 2) => n.toLocaleString('pt-BR', { minimumFractionDigits: dec, maximumFractionDigits: dec });
export const sinal = (n: number, dec = 2) => `${n > 0 ? '+' : ''}${formato(n, dec)}`;
