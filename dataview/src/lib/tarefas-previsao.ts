// Catálogo editorial: alternativas para discussão, não configurações de treino.
export const tarefasPrevisao = [
  {
    id: "direcao", nome: "Direção", pergunta: "Vai subir ou não?", saida: "Alta / não alta",
    motivo: "Investigar se o modelo antecipa o sentido do movimento.",
    estado: "Alvo atual", metrica: "Balanced accuracy, F1 e acerto de cada classe.",
    mudanca: "Já disponível em 24h e próximo candle. Outros prazos exigem novas amostras. Uma classe neutra seria outra definição de alvo.",
    limite: "Acertar o sentido não informa o tamanho do ganho ou da perda.",
    fontes: [
      { nome: "DeepLOB · 2019", url: "https://arxiv.org/abs/1808.03668", detalhe: "Ações: classificação de movimentos com livro de ofertas. Referência de tarefa; os dados diferem do nosso OHLCV." },
      { nome: "Mallqui & Fernandes · 2019", url: "https://doi.org/10.1016/j.asoc.2018.11.038", detalhe: "Bitcoin: estuda direção e preços diários, distinguindo classificação e regressão." },
    ],
  },
  {
    id: "retorno", nome: "Retorno ou preço", pergunta: "Quanto vai variar?", saida: "Ex.: retorno de +3%",
    motivo: "Medir a magnitude esperada do movimento, além do sentido.",
    estado: "Extensão em estudo", metrica: "MAE / RMSE, com referência ingênua e escala comparável.",
    mudanca: "Requer saída numérica, outra função de perda e avaliação própria. Para comparar moedas, considerar retorno em vez do preço nominal.",
    limite: "Pequeno erro de preço pode ocorrer só por repetir o último preço; isso não comprova bom sinal de trade.",
    fontes: [{ nome: "Mallqui & Fernandes · 2019", url: "https://doi.org/10.1016/j.asoc.2018.11.038", detalhe: "Bitcoin diário: previsão de máximo, mínimo e fechamento, além de direção. Não é previsão de lucro líquido." }],
  },
  {
    id: "intervalo", nome: "Faixa provável", pergunta: "Qual a incerteza da previsão?", saida: "Ex.: quantis de 10% a 90%",
    motivo: "Mostrar uma faixa de cenários e avaliar riscos de cauda.",
    estado: "Extensão em estudo", metrica: "Perda de quantis, cobertura observada e largura da faixa.",
    mudanca: "Requer saídas probabilísticas e verificação de calibração. A faixa pode ser de retorno ou volatilidade: é um formato de resposta combinável com outros alvos.",
    limite: "Uma faixa nominal de 80% precisa conter cerca de 80% dos valores fora do treino; não é garantia para uma previsão isolada.",
    fontes: [
      { nome: "CAViaR · Engle & Manganelli, 2004", url: "https://doi.org/10.1198/073500104000000370", detalhe: "Referência financeira para quantis condicionais de perdas (VaR); não propõe uma faixa simétrica de preço." },
      { nome: "TFT · Lim et al., 2021", url: "https://arxiv.org/html/1912.09363v3", detalhe: "Inclui volatilidade de 31 índices: quantis e horizontes de até cinco dias úteis. A arquitetura citada não será adicionada ao TCC." },
    ],
  },
  {
    id: "volatilidade", nome: "Volatilidade", pergunta: "Quanto o mercado vai oscilar?", saida: "Intensidade das oscilações",
    motivo: "Estimar risco e períodos de maior ou menor instabilidade.",
    estado: "Extensão em estudo", metrica: "MAE / QLIKE, conforme a medida de variância escolhida.",
    mudanca: "Requer definir volatilidade futura e comparadores de risco adequados. O AR(1) direcional atual não basta para esta tarefa.",
    limite: "Um mercado pode oscilar muito e terminar no mesmo preço. Volatilidade não determina alta ou baixa.",
    fontes: [
      { nome: "Wang et al. · 2023", url: "https://doi.org/10.1016/j.irfa.2023.102914", detalhe: "Criptomoedas: volatilidade diária, semanal e mensal. Inclui variáveis externas que não fazem parte do nosso escopo." },
      { nome: "Kilic · FEDS, rev. 2026", url: "https://www.federalreserve.gov/econres/feds/linear-and-nonlinear-econometric-models-against-machine-learning-models.htm", detalhe: "S&P 500 e 40 ações: comparação de previsões de volatilidade em diferentes horizontes. Working paper, não consenso institucional." },
    ],
  },
  {
    id: "barreiras", nome: "Primeiro limite atingido", pergunta: "Qual limite o preço toca primeiro?", saida: "Superior / inferior / prazo",
    motivo: "Considerar o caminho do preço, aproximando o alvo de regras de saída.",
    estado: "Alternativa metodológica", metrica: "Acerto por classe; custos e execução se houver simulação de trades.",
    mudanca: "Requer limites definidos com informação passada e prazo máximo. Se ambos os limites forem tocados no mesmo candle, OHLCV não revela a ordem.",
    limite: "Fechar em alta não significa ter tocado primeiro o limite superior. Tocar um limite também não garante execução naquele preço.",
    fontes: [{ nome: "López de Prado · 2018 / Mlfin.py", url: "https://mlfinpy.readthedocs.io/en/latest/Labelling.html", detalhe: "Triple-barrier: método de rotulagem do livro Advances in Financial Machine Learning, documentado na biblioteca. Não é um ranking empírico de tarefas." }],
  },
] as const;
export type TipoPrevisao = typeof tarefasPrevisao[number]["id"];
