"use client";

import { useState } from "react";
import type { Financeiro, Resumo } from "@/lib/caderno";
import { nomes, numero, percentual, prazo } from "@/lib/didatica";
const modelos = ["mamba", "lstm", "ar1", "frequencia_treino"];
const moedas = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT"];
const cores: Record<string, string> = { mamba: "#147b68", lstm: "#7760a5", ar1: "#aa593d", frequencia_treino: "#71828a" };
export function ResultadoObservado() { return <span className="selo observado">Resultado observado · desenvolvimento 2023 · seed 42</span>; }

export function ResultadosPreditivos({ resumo }: { resumo: Resumo }) {
  const [metrica, setMetrica] = useState<"log_loss" | "brier" | "balanced_accuracy">("log_loss");
  const [recorte, setRecorte] = useState("todos");
  const linhas = recorte === "todos" ? resumo.medias : recorte.startsWith("h:") ? resumo.por_horizonte.filter(r => r.horizonte === Number(recorte.slice(2))) : recorte.startsWith("m:") ? resumo.por_moeda.filter(r => r.par === recorte.slice(2)) : resumo.por_fold.filter(r => r.fold === recorte.slice(2));
  const teto = metrica === "balanced_accuracy" ? 1 : Math.max(...linhas.map(r => r[metrica])) * 1.08;
  const contraste = resumo.contrastes_globais.mamba_menos_lstm;
  const ic = contraste.intervalos["14"].log_loss;
  const x = (v: number) => 330 + v / .008 * 265;
  return <div className="bloco-resultados"><ResultadoObservado/>
    <div className="controles dois"><label>Métrica preditiva<select value={metrica} onChange={e => setMetrica(e.target.value as typeof metrica)}><option value="log_loss">Log-loss · menor é melhor</option><option value="brier">Brier · menor é melhor</option><option value="balanced_accuracy">Acerto balanceado · maior é melhor</option></select></label>
      <label>Recorte da média<select value={recorte} onChange={e => setRecorte(e.target.value)}><option value="todos">Grade completa</option>{[1, 24, 168].map(h => <option key={h} value={`h:${h}`}>Prazo: {prazo(h)}</option>)}{moedas.map(m => <option key={m} value={`m:${m}`}>{m}</option>)}{[1, 2, 3, 4].map(f => <option key={f} value={`f:DB${f}`}>Trimestre DB{f}</option>)}</select></label></div>
    <div className="barras-resultados" aria-live="polite">{modelos.map(m => { const r = linhas.find(l => l.modelo === m); if (!r) return null; return <div className="barra-resultado" key={m}><div className="linha-valores"><b>{nomes[m]}</b><strong>{metrica === "balanced_accuracy" ? percentual(r[metrica]) : numero(r[metrica], 4)}</strong></div><div className="trilho"><span style={{ width: `${100 * r[metrica] / teto}%`, background: cores[m] }}/></div></div>; })}</div>
    <p className="legenda">Barras partem de zero e usam a mesma escala dentro do recorte. {metrica === "balanced_accuracy" ? "Escala de 0 a 100%. A referência de três classes é 33,33%, não 50%." : "Escore sem unidade; não é porcentagem. A escala se ajusta ao recorte."} Frequências do treino é uma previsão constante baseada apenas na proporção de cada classe no treino.</p>
    <p><b>Como a média foi feita:</b> primeiro calcula-se o erro nas origens de teste de cada combinação e trimestre; depois dá-se o mesmo peso às células. Um trimestre com mais observações não recebe mais peso. Não é a média dos preços, das probabilidades nem dos lucros.</p>
    <div className="insight"><b>Leia por prazo, antes de escolher um vencedor.</b><p>Em 1 hora, as duas redes melhoraram em relação à referência constante. Em 24 horas, o ganho foi pequeno. Em 7 dias, ambas ficaram piores que essa referência. A comparação entre prazos também muda a distribuição das classes e a largura das barreiras.</p></div>
    <h3>Mamba e LSTM: uma diferença pequena, cercada de incerteza</h3>
    <p>Na grade completa, Mamba − LSTM = <b>{numero(contraste.diferenca_media.log_loss, 6)}</b> em log-loss. Como menor é melhor, o sinal positivo favorece LSTM. O intervalo de 95% vai de <b>{numero(ic[0], 6)}</b> a <b>{numero(ic[1], 6)}</b>: atravessa zero.</p>
    <svg className="grafico-intervalo" viewBox="0 0 660 160" role="img" aria-label={`Intervalo da diferença Mamba menos LSTM: ${ic[0]} a ${ic[1]}; inclui zero.`}>
      <rect x="65" y="35" width="265" height="55" fill="#e4f1eb"/><rect x="330" y="35" width="265" height="55" fill="#f0ebf7"/>
      <line x1="330" x2="330" y1="20" y2="105" stroke="#586e77" strokeDasharray="4 4"/>
      <line x1={x(ic[0])} x2={x(ic[1])} y1="63" y2="63" stroke="#153945" strokeWidth="3"/>
      {ic.map(v => <line key={v} x1={x(v)} x2={x(v)} y1="53" y2="73" stroke="#153945" strokeWidth="2"/>)}
      <circle cx={x(contraste.diferenca_media.log_loss)} cy="63" r="6" fill="#153945"/>
      <text x="65" y="126">Negativo: favorece Mamba</text><text x="330" y="126" textAnchor="middle">0</text><text x="595" y="126" textAnchor="end">Positivo: favorece LSTM</text>
    </svg>
    <p className="legenda">Intervalo por blocos de 14 dias; ponto = diferença média. Este gráfico permanece global, independentemente do filtro acima. Não há superioridade demonstrada de Mamba sobre LSTM; isso também não prova que sejam equivalentes.</p>
    <p>Contra AR(1), a diferença global Mamba − AR(1) foi <b>{numero(resumo.contrastes_globais.mamba_menos_ar1.diferenca_media.log_loss, 6)}</b>, com intervalo de 95% <b>[{resumo.contrastes_globais.mamba_menos_ar1.intervalos["14"].log_loss.map(v => numero(v, 6)).join("; ")}]</b>. A faixa inteira é negativa: favorece Mamba frente a esse comparador, sob o procedimento de blocos e nesta execução. É uma comparação distinta de Mamba versus LSTM.</p>
    <details><summary>Por que o AR(1) ficou com log-loss tão alta?</summary><p>O AR(1) foi convertido em probabilidades por 4.096 trajetórias simuladas por origem. O erro é avaliado contra os desfechos reais. Sua variância residual fixa e seus ruídos gaussianos são simplificações importantes.</p>
      <div className="tabela"><table><caption>Prazo esgotado: probabilidade média prevista versus frequência observada</caption><thead><tr><th>Prazo</th><th>AR(1) previu</th><th>Foi observado</th></tr></thead><tbody>{resumo.classes_por_horizonte.filter(r => r.modelo === "ar1" && r.classe === 1).map(r => <tr key={r.horizonte}><td>{prazo(r.horizonte)}</td><td>{percentual(r.probabilidade_media)}</td><td>{percentual(r.frequencia_observada)}</td></tr>)}</tbody></table></div>
      <p>O modelo atribuiu pouca probabilidade à expiração, embora ela fosse frequente. A log-loss pune esse tipo de erro. É um diagnóstico observado, não prova isolada da causa. A vantagem das redes vale contra este AR(1), não contra toda a família ARIMA.</p></details>
  </div>;
}

export function EfeitoContexto({ resumo }: { resumo: Resumo }) {
  return <div className="bloco-resultados"><ResultadoObservado/><h3>Sete dias de contexto ajudaram?</h3>
    <p>A diferença abaixo é <b>log-loss com 24h − log-loss com 168h</b>. À direita do zero, sete dias ajudam; à esquerda, um dia foi melhor. Cada linha resume 16 pares moeda/trimestre.</p>
    <div className="contexto-cabecalho"><span>Favorece 1 dia ←</span><span>→ Favorece 7 dias</span></div>
    {resumo.contexto.filter(r => r.modelo !== "ar1").map(r => <div className="contexto-linha" key={`${r.modelo}-${r.horizonte}`}><div className="linha-valores"><b>{nomes[r.modelo]} · prazo {prazo(r.horizonte)}</b><span>{r.diferenca_log_loss >= 0 ? "+" : ""}{numero(r.diferenca_log_loss, 6)}</span></div><div className="trilho divergente"><span style={{ background: cores[r.modelo], left: `${r.diferenca_log_loss < 0 ? 50 - Math.abs(r.diferenca_log_loss) / .03 * 50 : 50}%`, width: `${Math.abs(r.diferenca_log_loss) / .03 * 50}%` }}/></div><small>7 dias tiveram menor erro em {r.favorece_168} de {r.pares} pares.</small></div>)}
    <p className="legenda">Escala fixa de −0,03 a +0,03. São médias descritivas, sem intervalo agregado neste gráfico. Mais contexto não ajudou de forma uniforme. AR(1) não usa esta janela sequencial; suas cópias entre contextos não são evidências independentes.</p>
    <aside>Os dois contextos recebem o mesmo resumo da volatilidade dos últimos sete dias. A pergunta é se acrescentar a sequência detalhada desses dias ajuda além desse resumo.</aside>
  </div>;
}

const variantes: Record<string, string> = { base: "Custos base", custos_agravados: "Custos agravados", ambiguidade_superior: "Ambiguidade: superior primeiro", sem_filtro: "Controle sem filtro preditivo" };
const exibirPercentual = (n: number | null | undefined) => n == null ? "Indisponível" : percentual(n);
export function ResultadosFinanceiros({ linhas }: { linhas: Financeiro[] }) {
  const [moeda, setMoeda] = useState("BTCUSDT"), [contexto, setContexto] = useState(24), [horas, setHoras] = useState(24);
  const [variante, setVariante] = useState("base"), [modeloMapa, setModeloMapa] = useState("mamba");
  const bases = linhas.filter(r => r.variante === "base");
  const combinacoes = [24, 168].flatMap(w => [1, 24, 168].map(h => ({ w, h })));
  return <div className="bloco-resultados"><ResultadoObservado/><h3>Resultados de operações: todas as estratégias contam</h3>
    <div className="tabela"><table><caption>Saldo de estratégias anuais no cenário base</caption><thead><tr><th>Modelo</th><th>Retorno positivo</th><th>Retorno negativo</th><th>Sem operações</th></tr></thead><tbody>{modelos.slice(0, 3).map(m => { const lista = bases.filter(r => r.modelo === m && r.status === "auditavel"); return <tr key={m}><th>{nomes[m]}</th><td>{lista.filter(r => (r.retorno_liquido ?? 0) > 0).length} / 24</td><td>{lista.filter(r => (r.retorno_liquido ?? 0) < 0).length} / 24</td><td>{lista.filter(r => r.operacoes === 0).length} / 24</td></tr>; })}</tbody></table></div>
    <p>Uma estratégia = uma moeda + um contexto + um prazo + um modelo. Os quatro trimestres são concatenados mantendo o capital. São 24 estratégias por modelo, não uma carteira de 24 ativos. Resultados de estratégias sobrepostas não podem ser somados.</p>
    <div className="controles dois"><label>Modelo no mapa<select value={modeloMapa} onChange={e => setModeloMapa(e.target.value)}>{modelos.slice(0, 3).map(m => <option key={m} value={m}>{nomes[m]}</option>)}</select></label><label>Cenário econômico<select value={variante} onChange={e => setVariante(e.target.value)}>{Object.entries(variantes).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label></div>
    <div className="tabela mapa"><table><caption>Retorno após custos e número de operações · clique para detalhar</caption><thead><tr><th>Moeda</th>{combinacoes.map(c => <th key={`${c.w}-${c.h}`}>Contexto {c.w}h<br/>Prazo {c.h}h</th>)}</tr></thead><tbody>{moedas.map(m => <tr key={m}><th>{m.replace("USDT", "")}</th>{combinacoes.map(c => {
      const r = linhas.find(r => r.par === m && r.contexto === c.w && r.horizonte === c.h && r.modelo === modeloMapa && r.variante === variante);
      const valor = r?.status === "auditavel" ? r.retorno_liquido : null;
      return <td key={`${c.w}-${c.h}`}><button className={valor == null ? "ausente" : valor > 0 ? "ganho" : valor < 0 ? "perda" : "caixa"} onClick={() => { setMoeda(m); setContexto(c.w); setHoras(c.h); }} aria-pressed={m === moeda && c.w === contexto && c.h === horas} aria-label={`${m}, contexto ${c.w} horas, prazo ${prazo(c.h)}: ${exibirPercentual(valor)}, detalhar`}><b>{exibirPercentual(valor)}</b><small>{valor == null ? "Percurso incompleto" : `${r?.operacoes} ${r?.operacoes === 1 ? "operação" : "operações"}`}</small></button></td>;
    })}</tr>)}</tbody></table></div>
    <p className="legenda">Verde: ganho; terracota: perda; cinza: caixa; hachurado: indisponível. Os sinais e valores permitem ler o mapa sem depender de cores. A seleção abaixo compara os três modelos.</p>
    <div className="controles"><label>Moeda da estratégia<select value={moeda} onChange={e => setMoeda(e.target.value)}>{moedas.map(m => <option key={m}>{m}</option>)}</select></label><label>Contexto da estratégia<select value={contexto} onChange={e => setContexto(Number(e.target.value))}>{[24, 168].map(w => <option key={w} value={w}>{w} horas</option>)}</select></label><label>Prazo da estratégia<select value={horas} onChange={e => setHoras(Number(e.target.value))}>{[1, 24, 168].map(h => <option key={h} value={h}>{prazo(h)}</option>)}</select></label></div>
    <div className="cards-financeiros" aria-live="polite">{modelos.slice(0, 3).map(m => {
      const r = linhas.find(r => r.par === moeda && r.contexto === contexto && r.horizonte === horas && r.modelo === m && r.variante === variante);
      const disponivel = r?.status === "auditavel";
      return <article key={m}><h4><i style={{ background: cores[m] }}/>{nomes[m]}</h4>{!disponivel ? <><strong>Indisponível</strong><p>Uma lacuna impede reconstruir o percurso completo. Não foi substituído por zero.</p></> : <><small>Retorno sobre o capital inicial</small><strong>{exibirPercentual(r.retorno_liquido)}</strong><dl><div><dt>Operações</dt><dd>{r.operacoes ?? "Indisponível"}</dd></div><div><dt>Drawdown máximo</dt><dd>{exibirPercentual(r.drawdown_maximo)}</dd></div><div><dt>Tempo com posição</dt><dd>{exibirPercentual(r.tempo_exposto)}</dd></div><div><dt>Intervalo de retorno (95%)</dt><dd>{exibirPercentual(r.retorno_ic14_inferior)} a {exibirPercentual(r.retorno_ic14_superior)}</dd></div></dl>{r.operacoes === 0 && <p>Ficou em caixa. Zero não significa que o modelo acertou todas as previsões.</p>}</>}</article>;
    })}</div>
    <p className="legenda">Intervalo por blocos de 14 dias, condicional a esta execução. Poucas operações tornam a estimativa de rentabilidade especialmente frágil. Os filtros mudam a exibição, não reotimizam a política.</p>
    {variante === "custos_agravados" && <aside>Taxa de 0,20% e deslizamento de 0,10% por lado. Mantêm-se os sinais e as frações de exposição do cenário base, recalculando o saldo com custos maiores.</aside>}
    {variante === "ambiguidade_superior" && <aside>Sensibilidade à ordem desconhecida dentro do minuto. As previsões continuam as originais; a convenção de execução é alterada. Nesta grade, os resultados financeiros anuais ficaram iguais aos do cenário base.</aside>}
    {variante === "sem_filtro" && <aside>O controle entra quando está em caixa, sem exigir a previsão favorável. Seus 72 percursos anuais estão indisponíveis pela lacuna de dados. A ausência impede concluir que o filtro superou esse controle no ano.</aside>}
  </div>;
}
