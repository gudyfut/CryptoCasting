import plano from "@/lib/plano-experimental.json";

const perguntas: Record<string, { pergunta: string; contraste: string; observar: string }> = {
  E0: {
    pergunta: "Maior detalhe dos preços ajuda a prever o dia seguinte?",
    contraste: "Comparar candles de 15m, 4h e 1d com a referência de 1h, dentro de cada moeda. Também comparar Mamba com as duas baselines.",
    observar: "Detalhe adicional pode trazer informação ou ruído. Medir BA e diferenças por moeda e período; não presumir que 15m será melhor.",
  },
  E1: {
    pergunta: "Observar mais passado ajuda?",
    contraste: "Comparar E1 com E0: somente a duração da entrada passa de 7 para 14 dias. As datas avaliadas continuam iguais.",
    observar: "Mais contexto pode ajudar ou dificultar o aprendizado. Publicar os dois resultados; E2 volta à referência de 7 dias.",
  },
  E2: {
    pergunta: "Resumos de retorno, tendência e volatilidade acrescentam informação útil?",
    contraste: "Comparar E2 com E0: adicionar três indicadores ao OHLCV, passando de cinco para oito valores por candle.",
    observar: "Verificar se a BA média do Mamba melhora com os indicadores. A entrada escolhida passa a ser usada pelas duas redes; publicar ambas as opções.",
  },
  E3: {
    pergunta: "A forma de colocar os valores na mesma escala altera o aprendizado?",
    contraste: "Com as entradas escolhidas em E2, comparar MinMaxScaler com StandardScaler. Manter contexto de 7 dias e redes de largura 32.",
    observar: "Escolher a normalização pela BA média do Mamba e aplicá-la também à LSTM. Os dois métodos aprendem suas estatísticas somente no treino.",
  },
  E4: {
    pergunta: "Uma rede mais larga melhora o resultado e a que custo?",
    contraste: "Com entradas e normalização já escolhidas, comparar largura 64 com 32 dentro de cada arquitetura. As duas camadas permanecem.",
    observar: "Cada rede escolhe sua largura pela própria BA média. Registrar parâmetros e tempo; largura maior não garante mais acerto.",
  },
};

export default function PlanoTestes() {
  return <>
    <section className="painel">
      <h2>Plano executável atual: o que cada teste pretende responder</h2>
      <p className="nota-destaque"><b>Revisão aberta:</b> a seção Tipos de previsão em estudo organiza as alternativas A–H. E0–E4 abaixo pertencem à tarefa diária do protocolo 1.6; não incluem novas agendas, abstenção ou barreiras. Definir as tarefas antes de ampliar esta grade.</p>
      <p>O objetivo é identificar em quais condições o Mamba apresenta previsão direcional útil. As possibilidades abaixo são hipóteses: resultados iguais ou piores também serão documentados.</p>
      <p className="nota-destaque"><b>Antes da grade:</b> qualificar o Mamba oficial no piloto NVIDIA preparado. O piloto CPU BTC/D1 verificou o fluxo de treinamento, mas está em revisão por uma diferença de inicialização. Essa verificação técnica precede os experimentos E0–E4.</p>
      <div className="roteiro-testes">
        {plano.etapas.map((etapa) => <article key={etapa.id} className="teste-planejado">
          <h3><span>{etapa.id}</span> {etapa.nome}</h3>
          <p className="pergunta-teste">{perguntas[etapa.id].pergunta}</p>
          <dl>
            <div><dt>O que muda e com o que comparar</dt><dd>{perguntas[etapa.id].contraste}</dd></div>
            <div><dt>O que averiguar</dt><dd>{perguntas[etapa.id].observar}</dd></div>
          </dl>
        </article>)}
      </div>
      <p className="nota"><b>“BA média” nesta escolha:</b> cada moeda, resolução e fold de desenvolvimento tem o mesmo peso. Só decidir com a cobertura completa. Empates mantêm a opção inicial. As escolhas são globais; não se escolhe uma configuração diferente para esconder resultados ruins de uma moeda.</p>
    </section>
    <section className="painel">
      <h2>O que permanece igual entre as comparações</h2>
      <ul className="lista-explicativa">
        <li><b>Dados e alvo:</b> quatro moedas, mesmas origens elegíveis, previsão de alta ou não alta nas próximas 24 horas, às 00:00 UTC.</li>
        <li><b>Períodos:</b> quatro rodadas de desenvolvimento D1–D4, sem usar os resultados finais para decidir configurações.</li>
        <li><b>Treinamento neural:</b> mesmas regras de otimização, seleção pela validação e seed 42. A seed identifica a inicialização aleatória; não representa outro histórico de mercado.</li>
        <li><b>Comparação pareada:</b> Mamba e LSTM recebem os mesmos exemplos em cada condição. Cada modelo aprende seus próprios pesos; o número de parâmetros pode ser diferente.</li>
        <li><b>AR(1):</b> mantém a especificação fixa e usa retornos diários. Não recebe os indicadores, janelas ou larguras das redes.</li>
      </ul>
      <p className="nota">Alterar a moeda compara ativos; alterar o fold compara períodos. Nenhuma dessas diferenças isola o efeito causal de volatilidade ou de eventos de mercado. Usar uma implementação Mamba consistente na grade; o piloto local não entra automaticamente na média dos novos experimentos.</p>
    </section>
    <section className="painel">
      <h2>O que significam as mudanças de entrada e modelo</h2>
      <div className="glossario-matriz">
        <div><b>Features: valores de entrada</b><p>E2 acrescenta ao OHLCV o retorno das últimas 24h, a distância do fechamento à média móvel de 7 dias e a volatilidade dos últimos 7 retornos diários. São calculados com dados já disponíveis, sem acrescentar notícias ou fontes externas.</p></div>
        <div><b>Largura: dimensão interna da rede</b><p>32 ou 64 representa o tamanho da representação interna do Mamba ou do estado da LSTM. Não é o número de candles nem o tamanho do lote de treino. A quantidade de parâmetros depende da arquitetura.</p></div>
        <div><b>StandardScaler</b><p>Subtrai a média de treino de cada variável e divide pelo seu desvio-padrão. Assim, preços e volume passam a usar escalas comparáveis.</p></div>
        <div><b>MinMaxScaler</b><p>Usa o mínimo e o máximo de treino para colocar esses valores entre 0 e 1. Valores futuros podem sair desse intervalo; não serão cortados nem usados para reajustar a escala.</p></div>
      </div>
    </section>
    <section className="painel">
      <h2>Próximo candle e avaliação final no planejamento atual</h2>
      <ol className="lista-metodo">
        <li><b>Analisar o próximo candle, também em desenvolvimento.</b> Não é preciso esperar a avaliação final para estudar esta tarefa. Com contexto de 7 dias, prever 15 minutos, 1 hora ou 4 horas à frente, a cada candle. A linha de 1 dia reutiliza a tarefa principal. Aqui mudam horizonte, frequência e quantidade de exemplos: não é uma comparação isolada do detalhe da entrada.</li>
        <li><b>Congelar as escolhas.</b> Registrar entradas, normalização, largura de cada rede, código, dados e exposições anteriores aos resultados. Os contextos de 7 e 14 dias continuam sendo apresentados separadamente.</li>
        <li><b>Avaliar 2024–2025.</b> Aplicar as regras congeladas nos oito trimestres F1–F8, com três seeds. Refazer o treino em cada rodada; observar se os ganhos se repetem entre períodos e inicializações.</li>
      </ol>
      <p className="nota">A grade é sequencial, com candidatos definidos previamente. Não testa todas as combinações possíveis e não demonstra que a configuração escolhida é a melhor de toda a família Mamba.</p>
    </section>
  </>;
}
