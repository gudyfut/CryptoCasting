"use client";

import { useState, type ReactNode } from "react";
import { entregas, moedas } from "@/lib/estudo";

export function Fonte({ id, children }: { id: string; children: ReactNode }) {
  return <a className="link-documento" href={`/api/estudo/documentos/${id}`} target="_blank" rel="noreferrer">{children} <span aria-hidden="true">↗</span></a>;
}

function Quadro({ titulo, colunas, linhas }: { titulo: string; colunas: string[]; linhas: ReactNode[][] }) {
  return <div className="tabela-container" role="region" aria-label={titulo} tabIndex={0}>
    <table><caption>{titulo}</caption><thead><tr>{colunas.map((coluna) => <th scope="col" key={coluna}>{coluna}</th>)}</tr></thead>
      <tbody>{linhas.map((linha, i) => <tr key={i}>{linha.map((celula, j) => j === 0 ? <th scope="row" key={j}>{celula}</th> : <td key={j}>{celula}</td>)}</tr>)}</tbody>
    </table>
  </div>;
}

export function ResumoProjeto() {
  return <>
    <section className="painel revisao-tarefas"><span className="etiqueta ambar">Revisão metodológica em andamento</span><h2>Agora: definir quais previsões investigar</h2><p>Estamos comparando alternativas de alvo, horizonte e momento da previsão. A tarefa diária de 24h e a de próximo candle já integram o protocolo. Horizontes em vários horários, abstenção e outras tarefas estão em estudo.</p><p>Na seção <b>Tipos de previsão em estudo</b>, explore as opções e os exemplos visuais. A matriz atual documenta o protocolo 1.6; ampliar os experimentos depende desta definição. O piloto NVIDIA permanece um teste técnico delimitado.</p><Fonte id="tarefas">Pesquisa e recomendação para discussão com o orientador</Fonte></section>
    <section className="painel">
      <h2>A pergunta central</h2>
      <p className="objetivo">Investigar a capacidade do Mamba de prever a direção de retornos de BTC, ETH, BNB e XRP a partir de preços e volume, comparando seu desempenho com ARIMA(1,0,0) e LSTM.</p>
      <p>A análise verifica como o desempenho varia com a resolução dos candles, a duração da janela de entrada e o horizonte de previsão. O resultado esperado é uma avaliação dessas condições; a superioridade do Mamba é uma hipótese a testar.</p>
      <p className="nota">Mamba e LSTM são modelos que aprendem com sequências de observações. Neste trabalho, ARIMA(1,0,0), também chamado AR(1), é uma referência estatística simples baseada em retornos anteriores. “Baseline” significa modelo de comparação.</p>
      <Fonte id="protocolo">Referência: objetivo e escopo no protocolo experimental</Fonte>
    </section>
    <section className="painel">
      <h2>O que esperamos entregar como resposta</h2>
      <p>Uma comparação documentada que mostre <b>onde o Mamba ganha, empata ou perde</b> para as duas baselines, como isso muda entre moedas e períodos e se mais detalhe ou mais contexto ajudam.</p>
      <p>O produto principal será uma matriz com <b>moedas nas linhas e resoluções dos candles nas colunas</b>, acompanhada dos resultados por período, erros de cada classe, custo computacional e limitações. Não há uma taxa de acerto garantida.</p>
      <p className="nota">Roteiro de leitura: entender o problema → conhecer os dados → explorar tipos de previsão → entender a avaliação → acompanhar os testes → interpretar as evidências → consultar o andamento.</p>
    </section>
    <section className="painel">
      <h2>Delimitação do estudo</h2>
      <Quadro titulo="Definições centrais do protocolo 1.6" colunas={["Item", "Definição", "Interpretação"]} linhas={[
        ["Tarefa", "Classificação binária: alta ou não alta", "Alta corresponde a retorno futuro maior que zero. Queda e empate pertencem à classe não alta."],
        ["Dados", "OHLCV da Binance Spot · janeiro/2021 a dezembro/2025", "Abertura, máxima, mínima, fechamento e volume. Indicadores derivados são avaliados em uma etapa posterior."],
        ["Ativos", "BTCUSDT, ETHUSDT, BNBUSDT e XRPUSDT", "Mesma fonte e moeda de cotação. Cada ativo recebe modelos próprios."],
        ["Entrada", "Candles de 15m, 1h, 4h e 1d; contextos de 7 e 14 dias", "Mamba e LSTM recebem as mesmas sequências em cada comparação."],
        ["Referência controlada · A", "Próximas 24 horas, diariamente às 00:00 UTC", "Todas as resoluções usam as mesmas origens elegíveis e o mesmo desfecho futuro."],
        ["Próximo candle · B", "A cada fechamento; horizonte depende da resolução", "Já implementada; treino neural desta tarefa ainda pendente. A célula diária coincide com A."],
        ["Possíveis ampliações · C–H", "Em estudo, sem execução", "Horizontes em vários horários, abstenção, eventos, barreiras, magnitude e volatilidade. Exigem decisão e contratos próprios."],
        ["Avaliação", "Balanced accuracy (BA) em divisões temporais", "As comparações com AR(1), LSTM, 50% e o teste PT têm interpretações distintas."],
      ]} />
      <p className="nota">O estudo mede previsão direcional. Retorno financeiro de operações, notícias, sentimento e dados macroeconômicos estão fora deste escopo.</p>
    </section>
    <section className="painel">
      <h2>Situação atual e evidências disponíveis</h2>
      <p className="nota">BA é a média das proporções de acerto de alta e não alta. D1–D4 identificam quatro rodadas em períodos diferentes. As próximas seções explicam a divisão e as métricas.</p>
      <Quadro titulo="Estado registrado do projeto · 13/10/2026" colunas={["Etapa", "Situação", "Evidência / pendência"]} linhas={[
        ["Entregas 1–3", <span className="etiqueta verde" key="dados">Documentadas / executadas</span>, <>Protocolo definido; coleta e pré-processamento executados. Dataset com 1.661 origens diárias comuns, antes da purga por fold. <Fonte id="dados">Relatório dos dados</Fonte></>],
        ["AR(1) · BTC", <span className="etiqueta verde" key="ar">Executado em D1–D4</span>, <>BA média de 49,11% nos quatro folds de desenvolvimento. <Fonte id="piloto">Resultados e limites da interpretação</Fonte></>],
        ["Entregas 4–5", <span className="etiqueta ambar" key="redes">Piloto executado · Mamba em revisão</span>, <>BTC/1d/D1: BA Mamba 41,46%, LSTM 50,00% e AR(1) 46,34%. O fluxo foi auditado, mas uma diferença na inicialização do Mamba local exige verificação. A causa do resultado não está isolada. <Fonte id="diagnostico">Diagnóstico e limites do piloto</Fonte></>],
        ["Avaliação final", <span className="etiqueta" key="final">Planejada / bloqueada</span>, "Oito folds de 2024–2025. Exige congelamento das escolhas e declaração de exposições anteriores. Não há resultados finais."],
      ]} />
    </section>
    <section className="painel">
      <h2>Próxima etapa de trabalho</h2>
      <p>Definir com o orientador quais tarefas entram na ampliação do estudo e qualificar o Mamba oficial no piloto NVIDIA preparado. O piloto CPU fica preservado em revisão. Depois, versionar as decisões e medir o custo intradiário antes de iniciar a grade; não executar todas as opções automaticamente.</p>
      <p className="nota">As próximas seções explicam os termos e o procedimento. O andamento reúne as pendências, os registros históricos e os comandos para quem vai executar o estudo.</p>
    </section>
  </>;
}

export function MetodologiaProjeto() {
  return <>
    <section className="painel">
      <h2>Como uma comparação será feita</h2>
      <p>Escolhemos uma moeda, uma resolução e uma janela de entrada. Treinamos Mamba e LSTM com os mesmos exemplos do passado e ajustamos o AR(1). Depois comparamos suas respostas com o que realmente aconteceu nas mesmas datas posteriores.</p>
      <div className="glossario-matriz">
        <div><b>Treino: aprender</b><p>Dados usados para ajustar os parâmetros do modelo.</p></div>
        <div><b>Validação: escolher quando parar</b><p>Período posterior ao treino. Escolhe a época, isto é, qual passagem pelo conjunto de treino produziu a melhor BA de validação.</p></div>
        <div><b>Teste de desenvolvimento: comparar opções</b><p>Bloco seguinte. Pode orientar escolhas em D1–D4; por isso, não é a avaliação final.</p></div>
        <div><b>Fold: repetir em outro período</b><p>Uma rodada completa com seus próprios blocos. O histórico de treino cresce conforme avançamos no calendário.</p></div>
      </div>
    </section>
    <section className="painel">
      <h2>Modelos e função de cada comparação</h2>
      <Quadro titulo="Arquitetura investigada e baselines definidas" colunas={["Modelo", "Entrada e configuração", "Função no trabalho"]} linhas={[
        ["Mamba", "Sequências OHLCV; duas camadas; largura 32 ou 64. Probabilidade de alta maior que 50% produz a classe alta.", "Arquitetura investigada. Avaliar a previsão direcional e sua variação nas condições do protocolo."],
        ["LSTM", "Duas camadas unidirecionais; largura 32 ou 64. Mesmas entradas, folds, seeds e regras de treino do Mamba.", "Baseline neural. Comparar duas arquiteturas sequenciais sob condições pareadas."],
        ["ARIMA(1,0,0) / AR(1)", "Log-retornos; intercepto e coeficiente estimados no treino. Retorno previsto maior que zero produz a classe alta.", "Baseline estatística simples. Na tarefa de 24h, usa retornos diários e sua previsão é compartilhada entre as quatro resoluções."],
      ]} />
      <p className="nota">AR(1) mantém sua especificação fixa. As variações de features, janela e largura se aplicam às redes; não são configurações equivalentes do AR(1).</p>
    </section>
    <section className="painel">
      <h2>Divisão temporal e prevenção de vazamento</h2>
      <ol className="lista-metodo">
        <li><b>Construir as amostras por timestamp.</b> Cada exemplo preserva a origem da previsão e o término do alvo. Somente candles encerrados até a origem podem compor a entrada.</li>
        <li><b>Separar treino, validação e avaliação por datas.</b> O treino começa em 2021 e cresce a cada fold. Um fold é uma rodada com seus próprios intervalos temporais.</li>
        <li><b>Purgar as fronteiras.</b> Remover exemplos cujo alvo termine na fronteira ou depois do fim do bloco. Ajustar a normalização somente nos candles únicos do treino.</li>
        <li><b>Treinar novamente em cada fold.</b> Iniciar com pesos novos; a validação escolhe a época. Somente o conjunto de treino pode ser embaralhado.</li>
        <li><b>Avaliar no bloco seguinte.</b> Manter a ordem das previsões e comparar modelos nas mesmas origens. Não alinhar arquivos pela posição das linhas.</li>
      </ol>
      <Quadro titulo="Papel de cada fase" colunas={["Fase", "Período e repetições", "Decisões permitidas"]} linhas={[
        ["Desenvolvimento · D1–D4", "Histórico de 2021–2023; avaliações trimestrais em 2023; seed 42.", "Escolher features, normalização e larguras. Os resultados servem a ajustes e não constituem a avaliação final."],
        ["Final · F1–F8", "Avaliações trimestrais em 2024–2025; seeds 17, 42 e 2026.", "Aplicar as escolhas congeladas e reportar todas as repetições. A execução permanece bloqueada até essa etapa."],
      ]} />
      <p className="nota">As fronteiras exatas estão na matriz expansível do Plano de testes. Contextos de 7 e 14 dias são reportados separadamente. Exposições a resultados antigos devem ser declaradas antes de considerar a reserva final intocada.</p>
    </section>
    <section className="painel">
      <h2>Métricas e interpretação</h2>
      <p><b>Balanced accuracy (BA)</b> dá peso igual ao acerto das duas classes. Exemplo didático: acertar 80% das altas e 40% das não altas resulta em BA de 60%: (80% + 40%) ÷ 2. “Recall” é essa proporção de acertos dentro de uma classe.</p>
      <p className="nota">Se um modelo tiver BA de 55% e a baseline 52%, a diferença é de 3 pontos percentuais (p.p.). Isso descreve o ganho observado; não demonstra sozinho que ele se repetirá em outros períodos.</p>
      <Quadro titulo="Comparações que devem permanecer separadas" colunas={["Medida", "O que responde", "Limite da interpretação"]} linhas={[
        ["BA · métrica principal", "Média do recall de alta e do recall de não alta. Dá o mesmo peso às duas classes.", "Deve acompanhar o suporte por classe e a matriz de confusão. É indefinida se uma classe real estiver ausente."],
        ["Mamba − AR(1)", "Quanto a BA do Mamba difere da baseline estatística, em pontos percentuais.", "Diferença positiva observada não demonstra, sozinha, superioridade estatística."],
        ["Mamba − LSTM", "Quanto a BA difere entre redes com as mesmas entradas e origens.", "É uma comparação de arquiteturas nas condições adotadas, não de todos os modelos possíveis."],
        ["Referência de 50%", "Quanto a BA se afasta da referência sem habilidade direcional, quando ambas as classes estão presentes.", "O random walk sem deriva prevê não alta e atinge essa BA. A referência não é o resultado do AR(1) nem um p-valor."],
        ["Pesaran–Timmermann (PT)", "Verifica associação entre direção prevista e observada; reporta estatística e p-valor por modelo e seed.", "Não verifica correção ou qualidade do treinamento, superioridade sobre as baselines ou lucro. Seleção de origens e alvos sobrepostos exigem revisão da inferência."],
        ["Medidas complementares", "Accuracy, F1 macro, recall e quantidade de exemplos por classe.", "Ajudam a identificar desequilíbrio e erros. Nenhuma dessas medidas comprova rentabilidade de trading."],
      ]} />
      <p className="nota">Para uma leitura favorável do PT de uma rede, o protocolo exige estatística positiva e p &lt; 0,05 nas três seeds finais. O AR(1) é determinístico e tem um único PT por célula. O p-valor não é a chance de o modelo estar certo. Dependência temporal e muitas comparações limitam a conclusão; um PT com estatística negativa não favorece o modelo.</p>
      <Fonte id="protocolo">Consultar fórmulas e critérios no protocolo</Fonte>
    </section>
  </>;
}

export function DadosProjeto() {
  return <>
    <section className="painel">
      <h2>Do candle à resposta do modelo</h2>
      <p>Um <b>candle</b> resume um intervalo de mercado: preço de abertura, maior preço, menor preço, fechamento e volume negociado. Esses cinco valores formam o <b>OHLCV</b>. A resolução é a duração desse intervalo.</p>
      <div className="glossario-matriz">
        <div><b>Contexto: o passado observado</b><p>Os 7 ou 14 dias de candles que entram em uma previsão. O treino usa muitas dessas janelas, distribuídas pelo histórico.</p></div>
        <div><b>Horizonte: o futuro a prever</b><p>24h na referência A; um candle na tarefa B. Candle de 1h pode servir para prever 1h ou 24h: resolução e horizonte são escolhas diferentes.</p></div>
        <div><b>Origem: quando fazemos a previsão</b><p>00:00 UTC na referência A; cada fechamento na tarefa B. Nas candidatas, poderá haver outros horários ou eventos, sempre usando só o passado disponível.</p></div>
        <div><b>Alvo: a resposta correta</b><p>“Alta” se o fechamento 24 horas depois for maior que o fechamento na origem; “não alta” se for menor ou igual. Não exigimos uma alta mínima de 5%.</p></div>
      </div>
      <p className="nota-destaque"><b>Exemplo didático:</b> um fechamento de 100 na origem e de 101 no alvo corresponde a alta; 99 ou 100 corresponde a não alta. O modelo recebe somente o passado. O fechamento futuro é usado depois para conferir sua resposta.</p>
      <p>Para observar os mesmos 7 dias, usamos 672 candles de 15 minutos ou 7 candles diários. Na tarefa A, ambos geram <b>um exemplo e uma previsão diária</b>; os 672 candles não são 672 exemplos independentes. Na tarefa B, fazemos outro exemplo a cada fechamento elegível, com o horizonte de um candle.</p>
    </section>
    <section className="painel">
      <h2>Fonte, período e unidade temporal</h2>
      <p>Arquivos históricos públicos de candles de 15 minutos da <b>Binance Spot</b>, de 01/01/2021 00:00 UTC até 01/01/2026 00:00 UTC, com limite final exclusivo. Os candles de 1h, 4h e 1d são agregados a partir dessa mesma base, usando somente blocos completos.</p>
      <p>Todos os pares são cotados em USDT. A seleção dos quatro ativos é intencional e não representa uma amostra aleatória do mercado de criptomoedas.</p>
      <Fonte id="coleta">Documentação da coleta e auditoria</Fonte>
    </section>
    <section className="painel">
      <h2>Ativos analisados e justificativa</h2>
      <Quadro titulo="Propriedades distintas dos ativos selecionados" colunas={["Ativo / par", "Uso e contexto de rede", "Relevância para o estudo"]} linhas={moedas.map((m) => [
        <>{m.nome}<small className="linha-meta">{m.sigla}USDT</small></>,
        <>{m.papel}<small className="linha-meta">{m.rede}</small></>,
        m.descricao,
      ])} />
      <p className="nota">As propriedades motivam a seleção, mas não demonstram diferenças de previsibilidade. O vínculo de BNB com a Binance e o uso de uma única corretora são limitações da amostra. Não será atribuída causalidade a eventos das redes.</p>
    </section>
    <section className="painel">
      <h2>Volatilidade observada</h2>
      <p>Desvio-padrão dos log-retornos diários de fechamento nos mesmos <b>1.811 dias válidos</b> dos quatro ativos. A análise é descritiva e usa o período completo de 2021–2025.</p>
      <Quadro titulo="Volatilidade diária no período completo · não anualizada" colunas={["BTC", "ETH", "BNB", "XRP"]} linhas={[moedas.map((m) => `${m.volatilidade.toFixed(2).replace(".", ",")}%`)]} />
      <p>A ordem BTC &lt; ETH &lt; BNB &lt; XRP foi observada no período completo, mas varia entre anos. Maior volatilidade não implica que a direção seja mais fácil ou mais difícil de prever.</p>
      <Fonte id="dados">Fonte: resultados da execução oficial da Entrega 3</Fonte>
    </section>
    <section className="painel">
      <h2>Cobertura e tratamento de lacunas</h2>
      <Quadro titulo="Dataset documentado: daeec76f001afb50a8fe" colunas={["Registro", "Quantidade", "Tratamento / significado"]} linhas={[
        ["Arquivos mensais", "240", "216 completos e 24 com lacunas documentadas; arquivos e checksums originais preservados."],
        ["Candles ausentes", "70 de 15m por par", "Lacunas preservadas. Amostras cujo contexto ou alvo atravesse lacunas são excluídas; não há preenchimento automático de preços."],
        ["Arquivos processados", "67", "Manifestos e hashes permitem auditar os artefatos produzidos."],
        ["Origens diárias comuns", "1.661 antes da purga por fold", "Interseção das datas elegíveis dos quatro pares e quatro resoluções. Não equivale ao número de exemplos de um único fold."],
      ]} />
      <p className="nota">Os números desta seção são registros da execução oficial. A leitura dos resultados locais é feita separadamente na seção Resultados e interpretação.</p>
    </section>
  </>;
}

function Comando({ texto }: { texto: string }) {
  const [estado, setEstado] = useState("Copiar");
  async function copiar() {
    try { await navigator.clipboard.writeText(texto); setEstado("Copiado"); }
    catch { setEstado("Selecione o texto"); }
  }
  return <div className="comando"><code>{texto}</code><button onClick={copiar} aria-label={`Copiar comando: ${texto}`}>{estado}</button></div>;
}

export function EntregasProjeto() {
  return <>
    <section className="painel">
      <h2>Cronograma e situação das entregas</h2>
      <p className="nota-destaque"><b>Decisão atual:</b> rever o conjunto de tarefas antes de ampliar os treinos. Os prazos e a matriz abaixo documentam o planejamento 1.6; as opções C–H ainda não entram no orçamento. <Fonte id="tarefas">Estudo dos tipos de previsão</Fonte></p>
      <p>Datas do cronograma acadêmico de 2026. O estado abaixo diferencia documentação, execução e implementação; uma data prevista não significa que a etapa foi concluída.</p>
      <Quadro titulo="Acompanhamento das 12 entregas" colunas={["Entrega", "Período previsto", "Estado registrado", "Conteúdo, evidência e pendências"]} linhas={entregas.map((e) => [
        <>{String(e.numero).padStart(2, "0")} · {e.titulo}</>, e.prazo,
        <span key={e.numero} className={`etiqueta ${e.estado.includes("revisão") ? "ambar" : e.tipo === "concluida" ? "verde" : e.tipo === "implementada" ? "ambar" : ""}`}>{e.estado}</span>,
        <>{e.detalhe}{"documento" in e && <Fonte id={e.documento}>Documento da entrega</Fonte>}</>,
      ])} />
    </section>
    <section className="painel">
      <h2>Pendências para ampliar os experimentos neurais</h2>
      <ol className="lista-metodo">
        <li>Decidir quais tarefas entram na ampliação do estudo e registrar alvo, origens, horizontes, comparadores e orçamento. <Fonte id="tarefas">Opções e requisitos em discussão</Fonte></li>
        <li>Verificar a recorrência e a inicialização do Mamba local contra a referência oficial. O piloto está em revisão; sua baixa BA ainda não tem causa isolada. <Fonte id="diagnostico">Diagnóstico e verificações pendentes</Fonte></li>
        <li>Documentar qualquer correção e seu teste controlado com nova identidade. Preservar o piloto original. Manter a implementação escolhida consistente na grade e qualificar o ambiente se for usar Mamba oficial/CUDA.</li>
        <li>Medir tempo e memória em janelas intradiárias. Só então avaliar a viabilidade e iniciar E0–E4 no desenvolvimento. O tempo do piloto diário não estima o custo da grade inteira.</li>
        <li>Documentar as escolhas e as exposições anteriores antes de liberar a avaliação final.</li>
      </ol>
      <p className="nota">Orçamento do protocolo 1.6, sem as candidatas C–H: até 640 treinamentos neurais no desenvolvimento e 2.112 na avaliação final (1.056 por rede). São quantidades de ajustes, não execuções já feitas. O piloto diário ainda não fornece uma estimativa suficiente de custo.</p>
      <Fonte id="matriz">Matriz completa e orçamento de treinamentos</Fonte>
    </section>
    <section className="painel">
      <h2>Histórico para a escrita do TCC</h2>
      <p>Cada tentativa recebe uma ficha com dados, amostras, configuração, previsões, métricas e situação de revisão. Resultados ruins, falhas e hipóteses ainda não confirmadas permanecem registrados. Uma revisão posterior acrescenta evidência sem apagar a anterior.</p>
      <p>Já estão arquivados os quatro pilotos AR(1) e o piloto pareado. As datas de execução dos registros AR(1) antigos não foram preservadas; o ano avaliado não deve ser confundido com a data em que o teste foi executado.</p>
      <div className="links-fontes"><Fonte id="historico">Estrutura e regras do histórico</Fonte><Fonte id="timeline">Linha do tempo</Fonte><Fonte id="decisoes">Decisões registradas</Fonte></div>
    </section>
    <details className="painel detalhes-tecnicos">
      <summary>Referência técnica: comandos para futuras execuções</summary>
      <p>O piloto CPU já foi executado e está em revisão. O piloto NVIDIA preparado qualifica o backend oficial na tarefa A; seu guia explica instalação, treino e auditoria. Os comandos abaixo são referências de planejamento e verificação sem treino. Mudanças de código ou protocolo podem produzir uma nova identidade de execução.</p>
      <span className="passo-comando">1. Conferir a configuração do piloto, sem treinar</span>
      <Comando texto="python run_treino.py --configuracao configuracoes/treino_piloto_nvidia.json --planejar" />
      <span className="passo-comando">2. Verificar ambiente e dados do piloto NVIDIA, sem treinar</span>
      <Comando texto="python run_verificacao.py --configuracao configuracoes/treino_piloto_nvidia.json" />
      <span className="passo-comando">3. Após qualificação e definição das tarefas, conferir a grade 1.6 em WSL/CUDA</span>
      <Comando texto="python run_treino.py --configuracao configuracoes/treino_desenvolvimento_wsl.json --planejar" />
      <p className="nota">O piloto em CPU usa a implementação PyTorch de fallback. A grade WSL solicita Mamba oficial explicitamente e exige um ambiente CUDA ainda indisponível nesta máquina. Identificar o backend ao interpretar cada resultado; implementações diferentes não devem ser misturadas silenciosamente.</p>
      <Fonte id="nvidia">Guia do piloto NVIDIA e critérios de aceite</Fonte>
    </details>
  </>;
}
