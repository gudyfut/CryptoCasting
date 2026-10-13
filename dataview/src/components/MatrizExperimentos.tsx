"use client";

import { useState } from "react";
import plano from "@/lib/plano-experimental.json";
import PlanoTestes from "@/components/PlanoTestes";

const inteiro = (n: number) => n.toLocaleString("pt-BR");
const dataUtc = (tempo: number) => new Intl.DateTimeFormat("pt-BR", {
  timeZone: "UTC", dateStyle: "short", timeStyle: "short",
}).format(new Date(tempo));

export default function MatrizExperimentos() {
  const [par, setPar] = useState("todos");
  const [tarefa, setTarefa] = useState("principal");
  const [contexto, setContexto] = useState(7);
  const [features, setFeatures] = useState(5);
  const [fase, setFase] = useState("desenvolvimento");
  const [exemploCandle, setExemploCandle] = useState("15m");
  const pares = plano.pares.filter((p) => par === "todos" || p === par);
  const linhas = pares.flatMap((moeda) => plano.resolucoes.map((r) => ({ ...r, par: moeda })));
  const principal = tarefa === "principal";
  const quantidadeNova = linhas.filter((r) => principal || r.granularidade !== "1d").length;
  const exemplo = plano.resolucoes.find((r) => r.granularidade === exemploCandle)!;
  const origem = Date.UTC(2023, 0, 15);
  const dia = 86400000;
  const comprimento = contexto === 7 ? exemplo.janela_7d : exemplo.janela_14d;
  const folds = plano.folds.filter((f) => f.tipo === fase);

  return <>
    <PlanoTestes />
    <details className="detalhes-plano">
    <summary>Consultar matriz do protocolo 1.6, exemplos de timestamps e datas dos folds</summary>
    <section className="painel matriz-introducao">
      <h2>Como ler a matriz de configurações</h2>
      <p>Treinaremos modelos separados para cada combinação. Mamba e LSTM recebem a mesma entrada; cada um aprende seus próprios pesos. Os controles abaixo explicam o plano e não iniciam treinamentos.</p>
      <div className="glossario-matriz">
        <div><b>Candle / resolução</b><p>Quanto tempo cada linha de OHLCV representa: 15 minutos, 1 hora, 4 horas ou 1 dia.</p></div>
        <div><b>Janela / contexto</b><p>Quanto passado entra em uma previsão: 7 ou 14 dias. Isso define o comprimento da sequência.</p></div>
        <div><b>Horizonte</b><p>Quanto à frente está o alvo: as próximas 24 horas ou o próximo candle.</p></div>
        <div><b>Histórico de treino</b><p>Conjunto de muitas janelas anteriores, desde 2021. Uma janela de 7 dias não significa treinar com apenas 7 dias.</p></div>
      </div>
    </section>

    <section className="painel">
      <div className="painel-topo"><h3>Matriz de moedas e sequências</h3><span className="etiqueta">Protocolo {plano.protocolo} · planejamento</span></div>
      <div className="filtros filtros-matriz">
        <label htmlFor="matriz-par">Moeda<select id="matriz-par" value={par} onChange={(e) => setPar(e.target.value)}><option value="todos">Todas as moedas</option>{plano.pares.map((p) => <option key={p}>{p}</option>)}</select></label>
        <label htmlFor="matriz-tarefa">Horizonte<select id="matriz-tarefa" value={tarefa} onChange={(e) => { setTarefa(e.target.value); if (e.target.value === "proximo_candle") setContexto(7); }}><option value="principal">Próximas 24 horas</option><option value="proximo_candle">Próximo candle</option></select></label>
        <label htmlFor="matriz-contexto">Janela de entrada<select id="matriz-contexto" value={contexto} onChange={(e) => setContexto(Number(e.target.value))}><option value={7}>7 dias</option><option value={14} disabled={!principal}>14 dias</option></select></label>
        <label htmlFor="matriz-features">Entradas por candle<select id="matriz-features" value={features} onChange={(e) => setFeatures(Number(e.target.value))}><option value={5}>OHLCV · 5 valores</option><option value={8}>Com indicadores · 8 valores</option></select></label>
      </div>
      <p className="nota-destaque">{principal
        ? "Todas as resoluções preveem o mesmo futuro, uma vez por dia às 00:00 UTC. Mesmas origens elegíveis e mesmo alvo permitem comparar o detalhe da entrada."
        : "Aqui mudam o horizonte e a quantidade de exemplos: uma previsão a cada candle. Contexto fixo de 7 dias; a linha diária reaproveita a tarefa principal."}</p>
      <div className="tabela-container" role="region" aria-label="Tabela de configurações por moeda e resolução" tabIndex={0}>
        <table className="tabela-matriz"><caption>Configuração exibida: {contexto} dias de passado · {features} entradas por candle · {principal ? "24 horas à frente" : "um candle à frente"}</caption>
          <thead><tr><th scope="col">Par</th><th scope="col">Candle</th><th scope="col">Janela</th><th scope="col">Uma entrada do modelo</th><th scope="col">Horizonte / alvo</th><th scope="col">Quando prever</th></tr></thead>
          <tbody>{linhas.map((r) => {
            const tamanho = contexto === 7 ? r.janela_7d : r.janela_14d;
            return <tr key={`${r.par}-${r.granularidade}`}><th scope="row">{r.par}</th><td>{r.granularidade}</td><td><b>{inteiro(tamanho)}</b> candles<small className="linha-meta">{contexto} dias de histórico</small></td><td><code>[{inteiro(tamanho)}, {features}]</code><small className="linha-meta">passos temporais × features</small></td><td>{principal ? "24 horas" : r.granularidade}<small className="linha-meta">{principal ? r.horizonte_24h_candles : 1} candle(s) futuros</small></td><td>{principal ? "Diariamente, 00:00 UTC" : `A cada candle de ${r.granularidade}`}<small className="linha-meta">{!principal && r.granularidade === "1d" ? "Reutilizar principal / 7 dias" : "Somente após o fechamento"}</small></td></tr>;
          })}</tbody>
        </table>
      </div>
      <div className="contagem-matriz" aria-live="polite">
        <div><strong>{linhas.length}</strong><span>células exibidas</span></div>
        <div><strong>{quantidadeNova}</strong><span>{principal ? "células nesta configuração" : "células adicionais à principal"}</span></div>
        <p>{principal ? `${quantidadeNova} células × 4 folds × 1 seed × 2 redes = ${quantidadeNova * 8} treinamentos em uma etapa completa de desenvolvimento.` : "A complementar é uma análise posterior. Suas linhas diárias não geram novos ajustes; a avaliação final permanece bloqueada."}</p>
      </div>
      <p className="nota">Cada janela gera um único exemplo com uma classe. O batch efetivo reúne até 32 exemplos. As 1.661 origens diárias documentadas são do conjunto completo antes da purga, não o tamanho do treino de cada fold. Indicadores, normalização e larguras seguem a sequência abaixo; os filtros não representam uma busca irrestrita de combinações.</p>
    </section>

    <section className="painel">
      <div className="painel-topo"><h3>Timestamps de entrada, origem e alvo</h3><span className="etiqueta">Exemplo didático · UTC</span></div>
      <div className="filtros"><label htmlFor="exemplo-candle">Candle do exemplo<select id="exemplo-candle" value={exemploCandle} onChange={(e) => setExemploCandle(e.target.value)}>{plano.resolucoes.map((r) => <option key={r.granularidade}>{r.granularidade}</option>)}</select></label></div>
      <p>Uma previsão de {par === "todos" ? "BTCUSDT" : par} em <b>15/01/2023 às 00:00 UTC</b>, com os {contexto} dias anteriores e {inteiro(comprimento)} candles de entrada.</p>
      <ol className="exemplo-temporal">
        <li><span>01 · PRIMEIRO CANDLE ABRE</span><strong>{dataUtc(origem - contexto * dia)}</strong><small>Início do passado observado.</small></li>
        <li><span>02 · ÚLTIMO CANDLE ABRE</span><strong>{dataUtc(origem - exemplo.minutos * 60000)}</strong><small>Abertura não é o instante da previsão.</small></li>
        <li><span>03 · ORIGEM DA PREVISÃO</span><strong>{dataUtc(origem)}</strong><small>Último candle encerrado. A entrada termina aqui.</small></li>
        <li className="alvo-exemplo"><span>04 · TÉRMINO DO ALVO</span><strong>{dataUtc(origem + (principal ? dia : exemplo.minutos * 60000))}</strong><small>Futuro usado somente para avaliar a direção.</small></li>
      </ol>
      <p className="nota">Alta significa fechamento no alvo maior que o fechamento na origem; baixa ou empate significa não alta. Este exemplo explica os timestamps e não certifica que a data passou pelos filtros de qualidade do dataset.</p>
    </section>

    <section className="painel">
      <div className="painel-topo"><h3>Valores usados em cada etapa</h3><span className="etiqueta">Resumo técnico de E0–E4</span></div>
      <p>Desenvolvimento com horizonte de 24h, quatro moedas, quatro resoluções, D1–D4 e seed 42. As etapas posteriores dependem das decisões documentadas nas anteriores.</p>
      <div className="tabela-container" role="region" aria-label="Sequência de experimentos" tabIndex={0}><table className="tabela-etapas"><caption>Até 64 treinamentos por rede em cada etapa; até 640 para as duas redes nas cinco etapas.</caption><thead><tr><th>Etapa</th><th>Janela</th><th>Entradas</th><th>Normalização</th><th>Larguras</th><th>Como decidir</th></tr></thead><tbody>{plano.etapas.map((e) => <tr key={e.id}><th scope="row">{e.id}<small className="linha-meta">{e.nome}</small></th><td>{e.contexto}</td><td>{e.features}</td><td>{e.normalizador}</td><td>{e.larguras}</td><td className="celula-explicacao">{e.decisao}</td></tr>)}</tbody></table></div>
      <p className="nota">BA global usa pesos iguais entre ativos, resoluções e folds; a cobertura deve estar completa antes da escolha. Features e scaler são escolhidos pelo Mamba e compartilhados. Cada rede escolhe sua própria largura: o resultado pode ser Mamba 32 / LSTM 64. Empates favorecem a opção inicial. O AR(1) permanece fixo.</p>
    </section>

    <section className="painel">
      <div className="painel-topo"><h3>Períodos de treino, validação e avaliação</h3><span className={`etiqueta ${fase === "final" ? "ambar" : "verde"}`}>{fase === "final" ? "Finais bloqueados" : "Desenvolvimento disponível"}</span></div>
      <div className="abas-comparacao"><button aria-pressed={fase === "desenvolvimento"} className={fase === "desenvolvimento" ? "selecionada" : ""} onClick={() => setFase("desenvolvimento")}>D1–D4 · desenvolvimento</button><button aria-pressed={fase === "final"} className={fase === "final" ? "selecionada" : ""} onClick={() => setFase("final")}>F1–F8 · planejamento final</button></div>
      <div className="tabela-container" role="region" aria-label="Fronteiras temporais dos folds" tabIndex={0}><table><caption>UTC · intervalos [início, fim) · limite final exclusivo, com purga adicional do alvo</caption><thead><tr><th>Fold</th><th>Treino expansivo</th><th>Validação</th><th>{fase === "final" ? "Teste final" : "Avaliação de desenvolvimento"}</th><th>Seeds</th></tr></thead><tbody>{folds.map((f) => <tr key={f.nome}><th scope="row">{f.nome}</th><td>2021-01-01 → {f.fim_treino}</td><td>{f.fim_treino} → {f.fim_validacao}</td><td>{f.fim_validacao} → {f.fim_teste}</td><td>{fase === "final" ? plano.seeds_finais.join(" / ") : "42"}</td></tr>)}</tbody></table></div>
      <p className="nota">A origem precisa estar dentro do bloco e o alvo terminar <b>estritamente antes</b> do seu fim. O modelo começa com pesos novos em cada fold. A validação escolhe a época; o bloco seguinte mede o desempenho. D1–D4 podem orientar decisões. F1–F8 só serão executados após congelar o protocolo e declarar exposições anteriores.</p>
      <a className="link-documento" href="/api/estudo/documentos/matriz" target="_blank" rel="noreferrer">Abrir tabela completa e orçamento ↗</a>
    </section>
    </details>
  </>;
}
