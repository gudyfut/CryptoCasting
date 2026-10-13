"use client";

import { useEffect, useState } from "react";
import { moedas, type RespostaResultados } from "@/lib/estudo";
import type { TipoPrevisao } from "@/lib/tarefas-previsao";
import TiposPrevisao from "@/components/TiposPrevisao";
import CombinadorExperimentos, { combinacaoInicial, chaveCombinacao, type Combinacao } from "@/components/CombinadorExperimentos";
import { LinhaTemporal } from "@/components/VisuaisPrevisao";

const secoes = [
  { id: "estudo", nome: "O estudo", titulo: "Como o estudo se organiza", descricao: "Investigar em quais condições o Mamba consegue antecipar movimentos de criptomoedas." },
  { id: "previsoes", nome: "O que prever", titulo: "Escolher a pergunta da previsão", descricao: "Cinco formas de formular a tarefa, com exemplos e referências de pesquisa." },
  { id: "combinar", nome: "Combinar testes", titulo: "Explorar uma combinação", descricao: "Escolha moeda, candle, prazo e resposta. Veja exatamente qual pergunta seria testada." },
  { id: "avaliar", nome: "Como avaliar", titulo: "Como saber se funciona", descricao: "Comparações controladas e avaliação em períodos posteriores ao treinamento." },
  { id: "andamento", nome: "Andamento e resultados", titulo: "O que já temos", descricao: "Estado documentado, resultados preliminares e próximos passos." },
] as const;
type Secao = typeof secoes[number]["id"];
const percentual = (n: number | null) => n === null ? "—" : `${(n * 100).toFixed(2).replace(".", ",")}%`;
function Documento({ id, children }: { id: string; children: React.ReactNode }) { return <a href={`/api/estudo/documentos/${id}`} target="_blank" rel="noreferrer">{children} ↗</a>; }

function VisaoEstudo({ navegar }: { navegar: (s: Secao) => void }) {
  return <>
    <section className="decisao-atual"><div><span className="selo">Decisão em aberto</span><h2>Quais previsões vamos investigar?</h2><p>Moedas e modelos estão definidos. Estamos revendo os alvos e os prazos antes de ampliar os treinamentos.</p></div><button className="botao-principal" onClick={() => navegar("previsoes")}>Examinar as opções →</button></section>
    <section className="bloco"><h2>Cada experimento é uma combinação</h2><div className="eixos-estudo">
      <button onClick={() => navegar("combinar")}><span className="rotulo-eixo">01 · MERCADO</span><div className="simbolos-moedas"><i>₿</i><i>Ξ</i><i>B</i><i>X</i></div><h3>Qual moeda?</h3><p>BTC · ETH · BNB · XRP</p><span className="selo confirmado">Definido</span></button>
      <button onClick={() => navegar("combinar")}><span className="rotulo-eixo">02 · ENTRADA</span><div className="desenho-candles" aria-hidden="true">{[18, 32, 23, 40, 28, 36].map((h, i) => <i key={i} style={{ height: h }} />)}</div><h3>Qual candle?</h3><p>15 min · 1h · 4h · 1 dia</p><span className="selo confirmado">Definido</span></button>
      <button onClick={() => navegar("combinar")}><span className="rotulo-eixo">03 · FUTURO</span><div className="desenho-prazo" aria-hidden="true">horas <b>→</b> dias <b>→</b> semanas</div><h3>Daqui a quanto tempo?</h3><p>Prazo exato da previsão</p><span className="selo">Em revisão</span></button>
      <button onClick={() => navegar("previsoes")}><span className="rotulo-eixo">04 · RESPOSTA</span><div className="desenho-resposta" aria-hidden="true">↗ <span>±%</span> ≋</div><h3>O que prever?</h3><p>Direção, magnitude, risco…</p><span className="selo">Em revisão</span></button>
    </div></section>
    <section className="bloco"><div className="titulo-com-acao"><h2>Um exemplo do protocolo atual</h2><span className="selo confirmado">Direção em 24h</span></div><p>Com os últimos <b>7 dias</b> de candles de <b>1 hora</b>, prever se o preço estará mais alto <b>24 horas depois</b>.</p><LinhaTemporal candle="1 hora" contexto={7} horizonte="24 horas" quantidade={168} /><div className="links-em-linha"><button className="botao-texto" onClick={() => navegar("combinar")}>Explorar combinações →</button><Documento id="protocolo">Contrato atual</Documento></div></section>
    <section className="bloco"><h2>Quatro ativos, contextos diferentes</h2><div className="moedas-resumo">{moedas.map((m) => <div key={m.sigla}><span className="moeda-emblema" style={{ color: m.cor }}>{m.sigla}</span><h3>{m.nome}</h3><p>{m.papel}</p></div>)}</div><details><summary>Fonte dos dados e diferenças entre moedas</summary><p>Binance Spot · pares em USDT · 2021–2025 · abertura, máxima, mínima, fechamento e volume (OHLCV). Os candles maiores são agregados a partir de 15 minutos.</p>{moedas.map((m) => <p key={m.sigla}><b>{m.sigla}.</b> {m.descricao}</p>)}<p>Diferenças de uso motivam a escolha. A volatilidade é medida nos dados e pode mudar por período; a ordem dos ativos não é uma premissa do experimento.</p><Documento id="dados">Cobertura e volatilidade observadas</Documento></details></section>
  </>;
}

function Avaliacao() {
  return <>
    <section className="bloco"><h2>O Mamba é o objeto do estudo</h2><div className="modelos-estudo"><div className="modelo-principal"><span>INVESTIGADO</span><h3>Mamba</h3><p>Aprende sequências de OHLCV</p></div><div><span>COMPARAÇÃO NEURAL</span><h3>LSTM</h3><p>Mesmas entradas e regras de treino</p></div><div><span>REFERÊNCIA SIMPLES</span><h3>ARIMA(1,0,0)</h3><p>AR(1) dos log-retornos de fechamento</p></div></div><p className="miudo">Esses comparadores pertencem à tarefa direcional atual. Novos alvos exigem revisar a comparação.</p></section>
    <section className="bloco"><h2>O tempo avança; o treino cresce</h2><div className="legenda-tempo"><span>Treino</span><span>Validação</span><span>Teste</span></div><div className="walk-visual" role="img" aria-label="Esquema de três folds: a janela de treino se expande, seguida por validação e teste em datas posteriores. Desenho sem escala.">{[0, 1, 2].map((i) => <div key={i}><span>Etapa {i + 1}</span><div className="barra-fold"><i style={{ width: `${35 + i * 16}%` }} /><b /><em /></div></div>)}</div><div className="grade-tripla notas-tempo"><p><b>Treino</b>Aprender os parâmetros.</p><p><b>Validação</b>Escolher a configuração.</p><p><b>Teste</b>Medir em dados posteriores.</p></div><details><summary>Datas e proteção contra vazamento</summary><p>D1–D4: desenvolvimento em 2021–2023. F1–F8: oito trimestres de 2024–2025, bloqueados até congelar as decisões. No final, três seeds para avaliar variação de treinamento.</p><p>Normalização ajustada só no treino. Rótulos que cruzam fronteiras temporais são purgados. Alinhamento por timestamps. Validação e teste mantêm a ordem. Prazos longos e previsões sobrepostas precisam de avaliação estatística específica.</p><Documento id="protocolo">Folds e regras completas</Documento></details></section>
    <section className="bloco"><h2>Uma pergunta por comparação</h2><div className="comparacoes-curtas">{[
      ["Mamba × AR(1)", "Supera uma previsão estatística simples?"],
      ["Mamba × LSTM", "A arquitetura acrescenta valor com as mesmas entradas?"],
      ["BA × 50%", "Discrimina as duas classes além da referência de 50%?"],
      ["Teste PT", "Há associação entre a direção prevista e a realizada?"],
    ].map(([nome, pergunta]) => <div key={nome}><b>{nome}</b><p>{pergunta}</p></div>)}</div><details><summary>Como interpretar os números</summary><p>Balanced accuracy (BA) é a média do acerto entre altas e não altas. A referência de 50% vale quando ambas as classes existem; accuracy comum pode ser maior só por privilegiar a classe mais frequente. O random walk sem deriva, convertido ao alvo atual, sempre prevê não alta e atinge BA de 50% nessa condição.</p><p>Reportar BA, F1, matriz de confusão e diferenças pareadas. Uma diferença positiva observada não demonstra, sozinha, superioridade estatística. PT não verifica se o treinamento foi implementado corretamente, não compara duas baselines e não comprova lucro.</p></details></section>
    <section className="bloco"><h2>O que muda em cada teste</h2><div className="tabela-container"><table><thead><tr><th>Mudar</th><th>Manter igual</th><th>Verificar</th></tr></thead><tbody>
      <tr><th>Candle</th><td>Moeda, alvo, prazo, contexto e origens</td><td>Mais detalhe do passado ajuda?</td></tr>
      <tr><th>Contexto: 7 → 14 dias</th><td>Candle, prazo e datas avaliadas</td><td>Mais histórico ajuda?</td></tr>
      <tr><th>Moeda</th><td>Mesma tarefa, método e períodos comuns</td><td>O desempenho se repete em outros ativos?</td></tr>
      <tr><th>Prazo ou tipo de previsão</th><td>Regras pareadas dentro de cada tarefa</td><td>Em qual pergunta cada modelo funciona melhor?</td></tr>
    </tbody></table></div><p className="miudo">Tarefas diferentes podem ter populações e métricas distintas. Seus scores não formam automaticamente um ranking único.</p><details><summary>Entradas e configurações das redes</summary><p>Após qualificar o Mamba e definir as tarefas: estudar OHLCV versus indicadores causais, normalização e larguras 32/64. O protocolo define a sequência de seleção; toda decisão usa o desenvolvimento.</p><Documento id="matriz">Grade técnica vigente</Documento></details></section>
    <div className="faixa-informativa">A meta é medir previsibilidade. Validar uma estratégia de trading exigiria também entradas, saídas, custos e risco.</div>
  </>;
}

function Andamento() {
  const [dados, setDados] = useState<RespostaResultados | null>(null);
  const [erro, setErro] = useState("");
  const [tentativa, setTentativa] = useState(0);
  useEffect(() => {
    const controle = new AbortController();
    fetch("/api/estudo/resultados", { cache: "no-store", signal: controle.signal }).then((r) => { if (!r.ok) throw new Error("Não foi possível ler os resultados locais."); return r.json(); }).then((r: RespostaResultados) => { if (!controle.signal.aborted) setDados(r); }).catch((e: Error) => { if (!controle.signal.aborted) setErro(e.message); });
    return () => controle.abort();
  }, [tentativa]);
  return <>
    <section className="bloco"><h2>Andamento por etapa</h2><ol className="progresso-projeto">
      <li className="feito"><span>✓</span><div><h3>Dados preparados</h3><p>Coleta e amostras executadas · 1.661 origens diárias comuns.</p></div><Documento id="dados">Entrega 3</Documento></li>
      <li className="feito"><span>✓</span><div><h3>Baselines e piloto CPU</h3><p>AR(1), LSTM e Mamba executados no piloto documentado.</p></div><Documento id="infraestrutura">Entrega 4</Documento></li>
      <li className="em-andamento"><span>3</span><div><h3>Definir tarefas e qualificar o Mamba</h3><p>Alvos e prazos em discussão. Validação NVIDIA pendente.</p></div><Documento id="nvidia">Entrega 5</Documento></li>
      <li><span>4</span><div><h3>Ampliar os experimentos</h3><p>Comparar combinações, entradas e configurações no desenvolvimento.</p></div></li>
      <li><span>5</span><div><h3>Congelar, avaliar e escrever</h3><p>Avaliação final de 2024–2025 ainda não executada.</p></div></li>
    </ol></section>
    <section className="bloco"><div className="titulo-com-acao"><h2>Piloto documentado</h2><span className="selo">Preliminar · Mamba em revisão</span></div><p className="miudo">BTC · candle 1d · contexto 7 dias · horizonte 24h · D1 · seed 42 · CPU</p><div className="placar-piloto">{[["Mamba", "41,46%"], ["LSTM", "50,00%"], ["AR(1)", "46,34%"]].map(([nome, ba]) => <div key={nome}><span>{nome}</span><strong>{ba}</strong><small>balanced accuracy</small></div>)}</div><p>Uma combinação avaliada: 495 exemplos de treino, 91 de validação e 82 de teste de desenvolvimento.</p><details><summary>Interpretação e evidências</summary><p>Neste piloto o Mamba ficou abaixo das duas baselines. A LSTM previu não alta em todos os exemplos. Uma moeda, um fold e uma seed não permitem concluir sobre toda a arquitetura.</p><p>Os checkpoints reproduzem as previsões. Há uma diferença de inicialização da implementação local em revisão; a causa da baixa BA não foi isolada.</p><div className="links-em-linha"><Documento id="piloto-neural">Relatório do piloto</Documento><Documento id="diagnostico">Diagnóstico</Documento></div><p>O AR(1) de BTC nos quatro folds D1–D4 teve BA média de 49,11% (média não ponderada). É outro conjunto de avaliações.</p><Documento id="piloto">AR(1) em D1–D4</Documento></details></section>
    <section className="bloco"><h2>Como organizaremos os resultados</h2><div className="ficha-resultado"><div><span>IDENTIFICAÇÃO</span><b>Moeda + candle + prazo + alvo</b><small>Contexto · origens · entradas · fold · seed · backend</small></div><div><span>COMPARAÇÃO</span><b>Mamba | LSTM | AR(1)</b><small>Métricas adequadas à tarefa, tamanho da amostra e variação entre períodos.</small></div></div><p className="miudo">Cada combinação terá seu registro. Resultados finais ausentes permanecem ausentes; não há uma matriz final preenchida.</p></section>
    <section className="bloco"><details><summary>Consultar execuções locais e documentação</summary>{erro ? <div role="alert"><p>{erro}</p><button className="botao-texto" onClick={() => { setErro(""); setDados(null); setTentativa((t) => t + 1); }}>Tentar novamente</button></div> : !dados ? <p role="status">Lendo arquivos locais…</p> : <>
      {dados.resultados.length === 0 ? <p>Nenhuma execução pareada concluída encontrada neste ambiente.</p> : <div className="execucoes-locais">{dados.resultados.map((r) => <details key={r.pasta}><summary>{r.par} · {r.granularidade} · {r.fold} · {r.tarefa} · {r.id.slice(0, 8)}</summary><p>{r.contexto} dias de contexto · {r.features} · {r.normalizador} · seed {r.seed} · {r.amostras} exemplos avaliados</p><p>Backend: {r.backend} · {r.dispositivo} · larguras M{r.larguraMamba}/L{r.larguraLstm} · código {r.codigo.slice(0, 10)}</p><p>BA: Mamba {percentual(r.ba.mamba)} · LSTM {percentual(r.ba.lstm)} · AR(1) {percentual(r.ba.ar1)}</p><p className="miudo">{r.pasta}{r.id === "481b79d054b046fe6b70" ? " · Piloto em revisão" : " · Registro local, validade científica exige auditoria"}</p></details>)}</div>}
      {dados.avisos.length > 0 && <div role="status"><h3>Pendências na leitura</h3><ul>{dados.avisos.map((a) => <li key={a}>{a}</li>)}</ul></div>}
    </>}<div className="links-em-linha"><Documento id="tarefas">Pesquisa de tarefas</Documento><Documento id="protocolo">Protocolo</Documento><Documento id="mamba">Mamba base</Documento><Documento id="timeline">Histórico de execuções</Documento><Documento id="decisoes">Registro de decisões</Documento></div></details></section>
  </>;
}

export default function Dashboard() {
  const [secao, setSecao] = useState<Secao>("estudo");
  const [combinacao, setCombinacao] = useState<Combinacao>(combinacaoInicial);
  const [propostas, setPropostas] = useState<Combinacao[]>([]);
  const indice = secoes.findIndex((s) => s.id === secao);
  const atual = secoes[indice];
  function navegar(destino: Secao) { setSecao(destino); }
  useEffect(() => { window.scrollTo({ top: 0, behavior: "instant" }); document.getElementById("conteudo")?.focus({ preventScroll: true }); }, [secao]);
  return <div className="caderno-app"><a href="#conteudo" className="pular">Pular para o conteúdo</a><aside className="caderno-menu"><a href="#conteudo" className="caderno-marca" onClick={() => navegar("estudo")}>CryptoCasting<small>Caderno do projeto · TCC</small></a><nav aria-label="Seções do projeto">{secoes.map((s, i) => <button key={s.id} aria-current={secao === s.id ? "page" : undefined} onClick={() => navegar(s.id)}><span>0{i + 1}</span>{s.nome}</button>)}</nav><div className="caderno-referencia"><span className="selo">Desenho em revisão</span><p>Contrato executável 1.6</p><Documento id="protocolo">Protocolo experimental</Documento></div></aside><div className="caderno-corpo"><header className="caderno-topo"><span>Mamba · previsão de criptomoedas</span><span>Revisão de conteúdo · 13 out 2026</span></header><main id="conteudo" tabIndex={-1}><header className="caderno-titulo"><span>0{indice + 1} / 05</span><h1>{atual.titulo}</h1><p>{atual.descricao}</p></header>
    {secao === "estudo" && <VisaoEstudo navegar={navegar} />}
    {secao === "previsoes" && <TiposPrevisao explorar={(tipo: TipoPrevisao) => { setCombinacao((c) => ({ ...c, tipo })); navegar("combinar"); }} />}
    {secao === "combinar" && <CombinadorExperimentos valor={combinacao} alterar={setCombinacao} propostas={propostas} guardar={() => setPropostas((p) => p.some((c) => chaveCombinacao(c) === chaveCombinacao(combinacao)) ? p : [...p, { ...combinacao }])} remover={(chave) => setPropostas((p) => p.filter((c) => chaveCombinacao(c) !== chave))} />}
    {secao === "avaliar" && <Avaliacao />}{secao === "andamento" && <Andamento />}
    <nav className="caderno-paginacao" aria-label="Continuar a leitura">{indice > 0 ? <button onClick={() => navegar(secoes[indice - 1].id)}>← {secoes[indice - 1].nome}</button> : <span />}{indice < 4 ? <button onClick={() => navegar(secoes[indice + 1].id)}>{secoes[indice + 1].nome} →</button> : <button onClick={() => navegar("estudo")}>Voltar ao início ↑</button>}</nav><footer className="caderno-rodape">CryptoCasting · Murilo R. F. Monferrari · Documentação do estudo</footer>
  </main></div></div>;
}
