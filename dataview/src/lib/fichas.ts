import type { FichaModelo } from './panorama-tipos';

export const gruposFicha = [
  { id: 'entrada', nome: 'Dados e entrada', campos: {
    mercado: 'Mercado', moedas: 'Moedas', fonte: 'Origem dos dados', candle: 'Tamanho do candle', origens: 'Frequência da previsão', contexto: 'Histórico em cada exemplo', canais: 'Canais efetivos', representacao: 'Transformação dos canais', escala: 'Escala das entradas', alvo: 'O que o modelo prevê', escala_alvo: 'Escala do alvo', purga: 'Separação nas fronteiras', aquecimento: 'Passado mínimo comum', qualidade: 'Lacunas e exceções',
  } },
  { id: 'modelo', nome: 'Modelo e técnicas', campos: {
    familias: 'Modelos avaliados', eixo: 'Eixo percorrido pelo Mamba', estrutura: 'Estrutura da rede', estado: 'Memória interna · d_state', convolucao: 'Convolução · d_conv', expansao: 'Expansão interna', dropout: 'Dropout', normalizacao: 'Normalização dentro da rede', leitura: 'Como a saída é formada', auxiliar: 'Informação auxiliar', ganho: 'Ajuste da saída',
  } },
  { id: 'treino', nome: 'Treinamento', campos: {
    execucao: 'Novos pesos ou sinais herdados', otimizador: 'Otimizador', taxa: 'Taxa de aprendizado inicial', decay: 'Penalização · weight decay', isencoes: 'Quais pesos recebem penalização', parametros_adam: 'Betas e epsilon do Adam', scheduler: 'Evolução da taxa', perda: 'Função de perda', lote: 'Lote efetivo / microlote', clipping: 'Limite dos gradientes', epocas: 'Épocas e parada', precisao: 'Precisão numérica e backend',
  } },
  { id: 'avaliacao', nome: 'Seleção e avaliação', campos: {
    calendario: 'Treino, validação e teste', selecao: 'Escolha do checkpoint', promocao: 'Escolha da receita', seeds: 'Inicializações · seeds', controles: 'Controles de reprodução', referencias: 'Comparadores', agregacao: 'Como os resultados são resumidos', incerteza: 'Incerteza', exposicao: 'Exposição aos períodos',
  } },
  { id: 'operacao', nome: 'Simulação de operações', campos: {
    lados: 'Compra, venda e caixa', decisao: 'Decisão e latência', saida: 'Saída da posição', filtro: 'Regra de entrada', capital: 'Capital por carteira', tamanho: 'Tamanho e limites da posição', comissao: 'Comissão por lado', slippage: 'Derrapagem por lado', funding: 'Funding', risco: 'Marcação e risco', instrumento: 'Filtros do instrumento', cenarios: 'Cenários e controles', calibracao: 'Escolha da política',
  } },
] as const;

export type AlteracaoFicha = 'alterado' | 'mantido' | 'novo' | 'retirado';
export function compararFichas(atual: FichaModelo, anterior?: FichaModelo | null) {
  return gruposFicha.map(grupo => ({
    id: grupo.id, nome: grupo.nome,
    campos: Object.entries(grupo.campos).flatMap(([chave, nome]) => {
      const id = `${grupo.id}.${chave}`;
      const valor = atual.campos[id];
      const antes = anterior?.campos[id];
      if (valor === undefined && antes === undefined) return [];
      const alteracao: AlteracaoFicha = valor === undefined ? 'retirado' : antes === undefined ? 'novo' : valor === antes ? 'mantido' : 'alterado';
      return [{ id, nome, valor, antes, alteracao }];
    }),
  }));
}

// Esta é uma leitura curta para a interface. Os valores integrais continuam
// na ficha e na comparação; não encurtar os próprios registros científicos.
export function valorResumido(id: string, valor: string): string {
  if (id === 'entrada.moedas') return valor.replaceAll('USDT', '').replaceAll(' / ', ' · ');
  if (id === 'entrada.candle') return valor.startsWith('1 dia') ? 'Candles diários' : valor === '1 hora' ? 'Candles de 1h' : valor;
  if (id === 'entrada.canais') {
    const n = valor.match(/^\d+/)?.[0];
    const canais = n === '1' ? 'canal' : 'canais';
    const conteudo = valor.includes('timestamp') ? 'data + OHLCV' : valor.includes('retorno logarítmico horário') ? 'retorno do fechamento' : valor.includes('volatilidades') ? 'OHLCV + volatilidade' : valor.includes('log-retornos') ? 'OHLCV + momentum' : valor.includes('médias móveis') ? 'OHLCV + volume relativo' : 'OHLCV';
    return n ? `${n} ${canais} · ${conteudo}` : valor;
  }
  if (id === 'entrada.alvo') {
    if (valor.startsWith('3 classes')) return 'Primeiro toque nas barreiras · prazos de 1h, 24h ou 168h';
    if (valor.startsWith('2 payoffs')) return 'Ganho líquido de compra e venda em 24h';
    if (valor.startsWith('Retorno simples')) return 'Retorno simples do próximo dia';
    if (valor.startsWith('Log-retorno')) return 'Log-retorno em 24h';
    if (valor.startsWith('Preço de fechamento')) return 'Preço de fechamento do próximo dia';
  }
  if (id === 'entrada.representacao') {
    if (valor.startsWith('Preço em nível')) return 'Preços em nível · data · volume / 1e9';
    if (valor.includes('último close conhecido')) return 'Preços relativos à própria janela';
    if (valor.startsWith('ln(O/C anterior)')) return 'Preços relativos ao fechamento anterior';
    if (valor.startsWith('O, H, L, C')) return 'OHLCV em valores originais';
    if (valor.startsWith('ln(O),')) return 'OHLCV em logaritmos';
  }
  if (id === 'entrada.escala') {
    const moeda = valor.match(/^Z-score próprio de ([A-Z]+)/)?.[1];
    if (moeda) return `Padronização de ${moeda} · só no treino`;
    if (valor.startsWith('Sem padronização')) return 'Sem padronização';
    if (valor.includes('própria janela') || valor.includes('padronizado na janela')) return 'Escala por janela';
    if (valor.startsWith('Z-score')) return 'Padronização por canal, só no treino';
    if (valor.startsWith('Base OHLCV')) return 'OHLCV sem escala; extras padronizados no treino';
  }
  if (id === 'modelo.estrutura') {
    if (valor.includes('3 C-Blocks × 4')) return 'CryptoMamba · 12 blocos';
    const camadas = valor.match(/(\d+) blocos(?: Mamba)?/), largura = valor.match(/Projeção \d+→(\d+)/);
    if (camadas && largura) return `Mamba · ${camadas[1]} camadas · largura ${largura[1]}`;
    if (valor.startsWith('LSTM')) return 'LSTM · 2 camadas · largura 32';
  }
  if (id === 'modelo.eixo') return valor.startsWith('Canais:') ? 'Varredura pelos canais' : valor.startsWith('Tempo:') ? 'Varredura no tempo' : valor;
  if (id === 'modelo.normalizacao') return valor.startsWith('Pré-LayerNorm') ? 'Pré-LayerNorm' : valor.startsWith('Pós-LayerNorm') ? 'Pós-LayerNorm' : 'Sem LayerNorm adicional';
  if (id === 'treino.perda') return valor.includes('Huber') ? 'Huber' : valor.startsWith('RMSE') ? 'RMSE' : valor.startsWith('MSE') ? valor.includes('2 alvos') ? 'MSE de dois payoffs' : 'MSE' : valor.startsWith('Cross-entropy') ? 'Cross-entropy · 3 classes' : valor;
  if (id === 'treino.epocas') {
    const n = valor.match(/[\d.]+/)?.[0];
    return n ? `${valor.startsWith('Até') ? 'Até ' : ''}${n} épocas${valor.includes('sem parada antecipada') ? ' · sem parada antecipada' : ' · parada pela validação'}` : valor;
  }
  if (id === 'treino.scheduler') return valor.startsWith('StepLR') ? 'Taxa reduzida em intervalos fixos' : valor.startsWith('ReduceLROnPlateau') ? 'Taxa reduzida quando a validação estagna' : valor;
  if (id === 'avaliacao.calendario') {
    if (valor.includes('Desenvolvimento DB1')) return '4 blocos de desenvolvimento + 4 blocos em 2024–2025';
    if (valor.startsWith('B1:')) return '4 blocos em 2024–2025';
    if (valor.startsWith('Somente desenvolvimento')) return '4 blocos de desenvolvimento em 2023';
    if (valor.includes('S1:') || valor.includes('D3:')) return '3 recortes de desenvolvimento em 2023';
    if (valor.startsWith('Mesmo V/C/S')) return '3 recortes · treino móvel de 12 meses';
    if (valor.startsWith('D1:')) return '2 recortes de desenvolvimento em 2023';
    if (valor.startsWith('Treino 2020')) {
      const inicio = valor.match(/^Treino (2020)-(\d{2})-(\d{2})/);
      return inicio && (inicio[2] !== '01' || inicio[3] !== '01') ? `Treino desde ${inicio[3]}/${inicio[2]}/2020 · validação 2024 · teste 2025` : 'Treino 2020–2023 · validação 2024 · teste 2025';
    }
    if (valor.includes('V 2024')) return 'Treino 2021–2023 · validação 2024 · teste 2025';
  }
  if (id === 'avaliacao.selecao') return valor.includes('RMSE global do retorno') ? 'Menor RMSE de retorno na validação' : valor.includes('RMSE global do preço') ? 'Menor RMSE de preço na validação' : valor.includes('log-loss') ? 'Menor log-loss na validação' : 'Menor erro na validação';
  if (id === 'operacao.lados') return valor.startsWith('Spot:') ? 'Compra ou caixa' : valor.startsWith('Compra, venda') ? 'Compra, venda ou caixa' : valor.startsWith('Futuros:') ? 'Compra ou bilateral em futuros' : 'Spot e futuros, conforme o braço';
  if (id === 'operacao.saida') return valor.startsWith('24h') || valor.startsWith('Encerramento após 24') ? 'Posição encerrada em 24h' : valor.startsWith('Stop =') ? 'Stop e take · prazo máximo de 24h' : valor.includes('Smart') ? 'Políticas retidas e diárias, em braços separados' : valor.startsWith('Primeiro toque') ? 'Primeiro toque ou fim do prazo' : valor;
  return valor;
}

export function resumoFicha(ficha: FichaModelo) {
  const c = ficha.campos;
  const item = (id: string, prefixo = '') => ({ id, texto: `${prefixo}${valorResumido(id, c[id] ?? 'Não disponível')}` });
  const preparacao = ficha.id === 'desenho';
  const semTreino = c['treino.execucao']?.startsWith('Zero treino novo');
  const testeBloqueado = ficha.id === 'diario-primeiro';
  const semCarteira = c['operacao.cenarios']?.startsWith('Nenhuma') || /^astra1-C\d+$/.test(ficha.id);
  const canais = c['entrada.canais']?.match(/^\d+/)?.[0];
  return [
    { id: 'entrada', nome: 'Entrada', itens: [item('entrada.moedas'), item('entrada.candle'), item('entrada.contexto', 'Contexto: '), ...(canais ? [{ id: 'entrada.canais', texto: `${canais} ${canais === '1' ? 'canal' : 'canais'}` }] : []), item('entrada.escala')], apoio: item('entrada.alvo', 'Prevê: ') },
    { id: 'modelo', nome: 'Rede', itens: [item('modelo.estrutura'), ...(c['modelo.estado']?.startsWith('Não se aplica') ? [] : [item('modelo.estado', 'Estado: ')]), item('modelo.normalizacao')], apoio: item('modelo.eixo') },
    { id: 'treino', nome: 'Treino', itens: preparacao || semTreino ? [{ id: 'treino.execucao', texto: preparacao ? 'Preparação e qualificação' : 'Sem novo treinamento' }] : [item('treino.otimizador'), item('treino.taxa', 'Taxa: '), item('treino.decay', 'Penalização: '), item('treino.perda')], apoio: preparacao || semTreino ? { id: 'treino.execucao', texto: preparacao ? 'Parâmetros planejados para a referência' : 'Reutiliza os pesos e as previsões preservados' } : item('treino.epocas') },
    { id: 'avaliacao', nome: 'Avaliação', itens: [testeBloqueado ? { id: 'avaliacao.calendario', texto: 'Validação 2024 · teste 2025 bloqueado' } : item('avaliacao.calendario')], apoio: item('avaliacao.selecao') },
    { id: 'operacao', nome: 'Operação', itens: semCarteira || preparacao ? [{ id: 'operacao.cenarios', texto: 'Não executada nesta etapa' }] : [item('operacao.lados'), item('operacao.saida')], apoio: semCarteira || preparacao ? { id: 'operacao.cenarios', texto: testeBloqueado ? 'Controle de reprodução reprovado' : 'Etapa de preparação ou avaliação preditiva' } : { id: 'operacao.comissao', texto: `Comissão: ${c['operacao.comissao'] ?? 'não disponível'} por lado` } },
  ];
}

export const prioridadesDiferencas = [
  'entrada.moedas', 'entrada.candle', 'entrada.alvo', 'entrada.contexto', 'entrada.canais', 'entrada.representacao', 'entrada.escala',
  'modelo.estrutura', 'modelo.estado', 'modelo.eixo', 'modelo.normalizacao', 'modelo.dropout', 'modelo.leitura', 'modelo.ganho',
  'treino.otimizador', 'treino.taxa', 'treino.decay', 'treino.perda', 'treino.epocas', 'treino.scheduler',
  'avaliacao.calendario', 'avaliacao.selecao', 'avaliacao.seeds',
  'operacao.lados', 'operacao.saida', 'operacao.filtro', 'operacao.comissao', 'operacao.slippage', 'operacao.calibracao', 'operacao.instrumento',
];
