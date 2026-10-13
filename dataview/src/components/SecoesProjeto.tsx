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
    <section className="painel">
      <h2>Objetivo da pesquisa</h2>
      <p className="objetivo">Investigar a capacidade do Mamba de prever a direção de retornos de BTC, ETH, BNB e XRP a partir de preços e volume, comparando seu desempenho com ARIMA(1,0,0) e LSTM.</p>
      <p>A análise verifica como o desempenho varia com a resolução dos candles, a duração da janela de entrada e o horizonte de previsão. O resultado esperado é uma avaliação dessas condições; a superioridade do Mamba é uma hipótese a testar.</p>
      <Fonte id="protocolo">Referência: objetivo e escopo no protocolo experimental</Fonte>
    </section>
    <section className="painel">
      <h2>Delimitação do estudo</h2>
      <Quadro titulo="Definições centrais do protocolo 1.6" colunas={["Item", "Definição", "Interpretação"]} linhas={[
        ["Tarefa", "Classificação binária: alta ou não alta", "Alta corresponde a retorno futuro maior que zero. Queda e empate pertencem à classe não alta."],
        ["Dados", "OHLCV da Binance Spot · janeiro/2021 a dezembro/2025", "Abertura, máxima, mínima, fechamento e volume. Indicadores derivados são avaliados em uma etapa posterior."],
        ["Ativos", "BTCUSDT, ETHUSDT, BNBUSDT e XRPUSDT", "Mesma fonte e moeda de cotação. Cada ativo recebe modelos próprios."],
        ["Entrada", "Candles de 15m, 1h, 4h e 1d; contextos de 7 e 14 dias", "Mamba e LSTM recebem as mesmas sequências em cada comparação."],
        ["Previsão principal", "Próximas 24 horas, diariamente às 00:00 UTC", "Todas as resoluções usam as mesmas origens elegíveis e o mesmo desfecho futuro."],
        ["Avaliação", "Balanced accuracy (BA) em divisões temporais", "As comparações com AR(1), LSTM, 50% e o teste PT têm interpretações distintas."],
      ]} />
      <p className="nota">O estudo mede previsão direcional. Retorno financeiro de operações, notícias, sentimento e dados macroeconômicos estão fora deste escopo.</p>
    </section>
    <section className="painel">
      <h2>Situação atual e evidências disponíveis</h2>
      <Quadro titulo="Estado registrado do projeto · 13/10/2026" colunas={["Etapa", "Situação", "Evidência / pendência"]} linhas={[
        ["Entregas 1–3", <span className="etiqueta verde" key="dados">Documentadas / executadas</span>, <>Protocolo definido; coleta e pré-processamento executados. Dataset com 1.661 origens diárias comuns, antes da purga por fold. <Fonte id="dados">Relatório dos dados</Fonte></>],
        ["AR(1) · BTC", <span className="etiqueta verde" key="ar">Executado em D1–D4</span>, <>BA média de 49,11% nos quatro folds de desenvolvimento. <Fonte id="piloto">Resultados e limites da interpretação</Fonte></>],
        ["Entregas 4–5", <span className="etiqueta verde" key="redes">Piloto CPU executado e auditado</span>, <>BTC/1d/D1: BA Mamba 41,46%, LSTM 50,00% e AR(1) 46,34%. Checkpoints recarregados reproduzem as previsões. Backend oficial/CUDA ainda pendente por ambiente. <Fonte id="piloto-neural">Relatório do piloto neural</Fonte></>],
        ["Avaliação final", <span className="etiqueta" key="final">Planejada / bloqueada</span>, "Oito folds de 2024–2025. Exige congelamento das escolhas e declaração de exposições anteriores. Não há resultados finais."],
      ]} />
    </section>
    <section className="painel">
      <h2>Próxima etapa de trabalho</h2>
      <p>O piloto em <b>BTCUSDT, candle diário, fold D1, contexto de 7 dias e seed 42</b> foi concluído em CPU. Antes de ampliar a grade, qualificar o backend oficial em ambiente CUDA compatível e medir o custo de janelas intradiárias. A máquina atual tem GPU AMD RX 6600 e não oferece o ambiente CUDA previsto.</p>
      <p className="nota">A seção Entregas e execução reúne os comandos e as pendências. A seção Configurações experimentais apresenta as combinações previstas e as datas de treino, validação e avaliação.</p>
    </section>
  </>;
}

export function MetodologiaProjeto() {
  return <>
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
      <p className="nota">As fronteiras exatas estão em Configurações experimentais. Contextos de 7 e 14 dias são reportados separadamente. Exposições a resultados antigos devem ser declaradas antes de considerar a reserva final intocada.</p>
    </section>
    <section className="painel">
      <h2>Métricas e interpretação</h2>
      <Quadro titulo="Comparações que devem permanecer separadas" colunas={["Medida", "O que responde", "Limite da interpretação"]} linhas={[
        ["BA · métrica principal", "Média do recall de alta e do recall de não alta. Dá o mesmo peso às duas classes.", "Deve acompanhar o suporte por classe e a matriz de confusão. É indefinida se uma classe real estiver ausente."],
        ["Mamba − AR(1)", "Quanto a BA do Mamba difere da baseline estatística, em pontos percentuais.", "Diferença positiva observada não demonstra, sozinha, superioridade estatística."],
        ["Mamba − LSTM", "Quanto a BA difere entre redes com as mesmas entradas e origens.", "É uma comparação de arquiteturas nas condições adotadas, não de todos os modelos possíveis."],
        ["Referência de 50%", "Quanto a BA se afasta da referência sem habilidade direcional, quando ambas as classes estão presentes.", "O random walk sem deriva prevê não alta e atinge essa BA. A referência não é o resultado do AR(1) nem um p-valor."],
        ["Pesaran–Timmermann (PT)", "Verifica associação entre direção prevista e observada; reporta estatística e p-valor por modelo e seed.", "Não testa a diferença de desempenho entre Mamba e as baselines."],
        ["Medidas complementares", "Accuracy, F1 macro, recall e quantidade de exemplos por classe.", "Ajudam a identificar desequilíbrio e erros. Nenhuma dessas medidas comprova rentabilidade de trading."],
      ]} />
      <Fonte id="protocolo">Consultar fórmulas e critérios no protocolo</Fonte>
    </section>
  </>;
}

export function DadosProjeto() {
  return <>
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
      <p>Datas do cronograma acadêmico de 2026. O estado abaixo diferencia documentação, execução e implementação; uma data prevista não significa que a etapa foi concluída.</p>
      <Quadro titulo="Acompanhamento das 12 entregas" colunas={["Entrega", "Período previsto", "Estado registrado", "Conteúdo, evidência e pendências"]} linhas={entregas.map((e) => [
        <>{String(e.numero).padStart(2, "0")} · {e.titulo}</>, e.prazo,
        <span key={e.numero} className={`etiqueta ${e.tipo === "concluida" ? "verde" : e.tipo === "implementada" ? "ambar" : ""}`}>{e.estado}</span>,
        <>{e.detalhe}{"documento" in e && <Fonte id={e.documento}>Documento da entrega</Fonte>}</>,
      ])} />
    </section>
    <section className="painel">
      <h2>Pendências para ampliar os experimentos neurais</h2>
      <ol className="lista-metodo">
        <li>Consultar o piloto CPU concluído: artefatos auditados, previsões reproduzidas após recarga e métricas documentadas. <Fonte id="piloto-neural">Evidências do piloto</Fonte></li>
        <li>Qualificar Mamba oficial em um ambiente CUDA compatível. Medir tempo e memória em janelas intradiárias; o tempo do piloto diário não estima o custo da grade inteira.</li>
        <li>Avaliar a viabilidade da grade e iniciar as etapas E0–E4, usando somente os folds de desenvolvimento.</li>
        <li>Documentar as escolhas e as exposições anteriores antes de liberar a avaliação final.</li>
      </ol>
      <p className="nota">Orçamento planejado: até 640 treinamentos neurais no desenvolvimento e 2.112 na avaliação final (1.056 por rede). O piloto deve fornecer a estimativa de custo antes da execução da grade completa.</p>
      <Fonte id="matriz">Matriz completa e orçamento de treinamentos</Fonte>
    </section>
    <section className="painel">
      <h2>Comandos para futuras execuções</h2>
      <p>O piloto CPU já está concluído; não é necessário repeti-lo para consultar os resultados. Os comandos abaixo ficam como referência, na raiz do projeto e com as dependências instaladas. Mudanças de código ou protocolo podem produzir uma nova identidade de execução.</p>
      <span className="passo-comando">1. Conferir a configuração do piloto, sem treinar</span>
      <Comando texto="python run_treino.py --configuracao configuracoes/treino_piloto_cpu.json --planejar" />
      <span className="passo-comando">2. Executar o piloto BTC / 1d / D1 em CPU</span>
      <Comando texto="python run_treino.py --configuracao configuracoes/treino_piloto_cpu.json" />
      <span className="passo-comando">3. Após validar o piloto, planejar o desenvolvimento em WSL/CUDA</span>
      <Comando texto="python run_treino.py --configuracao configuracoes/treino_desenvolvimento_wsl.json --planejar" />
      <p className="nota">O piloto em CPU usa a implementação PyTorch de fallback. A grade WSL solicita Mamba oficial explicitamente e exige um ambiente CUDA ainda indisponível nesta máquina. Identificar o backend ao interpretar cada resultado; implementações diferentes não devem ser misturadas silenciosamente.</p>
      <Fonte id="mamba">Instruções completas e artefatos esperados</Fonte>
    </section>
  </>;
}
