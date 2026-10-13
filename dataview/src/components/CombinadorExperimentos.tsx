"use client";
import { moedas } from "@/lib/estudo";
import { tarefasPrevisao, type TipoPrevisao } from "@/lib/tarefas-previsao";
import { LinhaTemporal } from "@/components/VisuaisPrevisao";

const candles = [{ id: "15m", nome: "15 min", minutos: 15 }, { id: "1h", nome: "1 hora", minutos: 60 }, { id: "4h", nome: "4 horas", minutos: 240 }, { id: "1d", nome: "1 dia", minutos: 1440 }];
const prazos = [
  { id: "intradia", nome: "Dentro do dia", estilo: "Referência: day trading", valores: [15, 60, 240] },
  { id: "dias", nome: "Entre dias", estilo: "Referência: swing trading", valores: [1440, 4320] },
  { id: "semanas", nome: "Uma semana ou mais", estilo: "Swing mais longo / posições", valores: [10080, 20160] },
];
export type Combinacao = { moeda: string; candle: string; horizonte: number; contexto: number; tipo: TipoPrevisao; agenda: string; politica: string };
export const combinacaoInicial: Combinacao = { moeda: "BTC", candle: "1h", horizonte: 1440, contexto: 7, tipo: "direcao", agenda: "diaria", politica: "todas" };
export const nomePrazo = (minutos: number) => minutos < 60 ? `${minutos} min` : minutos < 1440 ? `${minutos / 60}h` : minutos === 1440 ? "24h" : `${minutos / 1440} dias`;
export const chaveCombinacao = (c: Combinacao) => [c.moeda, c.candle, c.horizonte, c.contexto, c.tipo, c.agenda, c.politica].join("/");

export default function CombinadorExperimentos({ valor, alterar, propostas, guardar, remover }: { valor: Combinacao; alterar: (c: Combinacao) => void; propostas: Combinacao[]; guardar: () => void; remover: (chave: string) => void }) {
  const candle = candles.find((c) => c.id === valor.candle)!;
  const tarefa = tarefasPrevisao.find((t) => t.id === valor.tipo)!;
  const prazo = prazos.find((p) => p.valores.includes(valor.horizonte))!;
  const contextoCandles = valor.contexto * 1440 / candle.minutos;
  const diario = valor.horizonte === 1440 && valor.agenda === "diaria";
  const proximo = valor.horizonte === candle.minutos && valor.contexto === 7 && (valor.agenda === "candle" || (candle.id === "1d" && valor.agenda === "diaria"));
  const noProtocolo = valor.tipo === "direcao" && valor.politica === "todas" && (diario || proximo);
  const pergunta = {
    direcao: `O preço de ${valor.moeda} estará acima do último fechamento daqui a ${nomePrazo(valor.horizonte)}?`,
    retorno: `Qual será o retorno de ${valor.moeda} nas próximas ${nomePrazo(valor.horizonte)}?`,
    intervalo: `Qual será a faixa prevista para o retorno de ${valor.moeda} em ${nomePrazo(valor.horizonte)}?`,
    volatilidade: `Qual será a volatilidade de ${valor.moeda} ao longo de ${nomePrazo(valor.horizonte)}?`,
    barreiras: `Qual limite ${valor.moeda} tocará primeiro, dentro de ${nomePrazo(valor.horizonte)}?`,
  }[valor.tipo];
  function mudar<K extends keyof Combinacao>(campo: K, novo: Combinacao[K]) { alterar({ ...valor, [campo]: novo }); }
  return <>
    <div className="faixa-informativa">Rascunho para discussão. Estas escolhas não alteram arquivos de configuração nem iniciam treinos.</div>
    <div className="construtor-grade"><section className="bloco seletores-combinacao" aria-label="Escolhas da combinação">
      <fieldset><legend><span>1</span> Moeda</legend><div className="opcoes-linha">{moedas.map((m) => <button key={m.sigla} aria-pressed={valor.moeda === m.sigla} onClick={() => mudar("moeda", m.sigla)}>{m.sigla}</button>)}</div></fieldset>
      <fieldset><legend><span>2</span> Duração de cada candle</legend><div className="opcoes-linha">{candles.map((c) => <button key={c.id} aria-pressed={c.id === valor.candle} onClick={() => mudar("candle", c.id)}>{c.nome}</button>)}</div><p className="miudo">Define o detalhe do histórico que o modelo recebe.</p></fieldset>
      <fieldset><legend><span>3</span> Prazo da previsão</legend><div className="opcoes-prazo">{prazos.map((p) => <button key={p.id} aria-pressed={p.id === prazo.id} onClick={() => mudar("horizonte", p.valores[0])}><b>{p.nome}</b><small>{p.estilo}</small></button>)}</div><div className="opcoes-linha subopcoes">{prazo.valores.map((h) => <button key={h} aria-pressed={h === valor.horizonte} onClick={() => mudar("horizonte", h)}>{nomePrazo(h)}</button>)}</div><button className="botao-texto" onClick={() => alterar({ ...valor, horizonte: candle.minutos, agenda: "candle" })}>Usar próximo candle: {nomePrazo(candle.minutos)}</button></fieldset>
      <label className="campo"><span><b className="numero-campo">4</b> Tipo de previsão</span><select value={valor.tipo} onChange={(e) => mudar("tipo", e.target.value as TipoPrevisao)}>{tarefasPrevisao.map((t) => <option key={t.id} value={t.id}>{t.nome}</option>)}</select></label>
    </section><section className="bloco resumo-combinacao" aria-live="polite">
      <span className={`selo ${noProtocolo ? "confirmado" : ""}`}>{noProtocolo ? "Prevista no protocolo 1.6" : "Proposta · requer novo protocolo"}</span>
      <h2>{pergunta}</h2>
      <div className="resposta-esperada"><span>O modelo responderia</span><strong>{tarefa.saida}</strong></div>
      <dl className="ficha-combinacao"><div><dt>Entrada</dt><dd>{contextoCandles.toLocaleString("pt-BR")} candles de {candle.nome}</dd></div><div><dt>Passado observado</dt><dd>{valor.contexto} dias · OHLCV</dd></div><div><dt>Nova previsão</dt><dd>{valor.agenda === "diaria" ? "Diariamente, 00:00 UTC" : `A cada candle de ${candle.nome}`}</dd></div><div><dt>Respostas</dt><dd>{valor.politica === "todas" ? "Todas as origens válidas" : valor.politica === "abstencao" ? "Só acima do limiar de confiança" : "Só após um gatilho do passado"}</dd></div></dl>
      {valor.tipo !== "direcao" && <p className="miudo">Saída, treino, métricas e baselines precisam de adaptação.</p>}
      <button className="botao-principal" disabled={propostas.some((c) => chaveCombinacao(c) === chaveCombinacao(valor))} onClick={guardar}>{propostas.some((c) => chaveCombinacao(c) === chaveCombinacao(valor)) ? "Já está na lista" : "Adicionar à lista de discussão"}</button>
      <p className="miudo">Lista temporária, mantida ao trocar de seção. Recarregar a página limpa o rascunho.</p>
    </section></div>
    <section className="bloco"><h2>O que entra e o que queremos antecipar</h2><LinhaTemporal candle={candle.nome} contexto={valor.contexto} horizonte={nomePrazo(valor.horizonte)} quantidade={contextoCandles} />
      <div className="grade-tripla ajustes-combinacao"><label className="campo">Passado observado<select value={valor.contexto} onChange={(e) => mudar("contexto", Number(e.target.value))}><option value={7}>7 dias de contexto</option><option value={14}>14 dias de contexto</option></select></label><label className="campo">Quando prever<select value={valor.agenda} onChange={(e) => mudar("agenda", e.target.value)}><option value="diaria">Todo dia, às 00:00 UTC</option><option value="candle">Após cada candle fechado</option></select></label><label className="campo">Quando responder<select value={valor.politica} onChange={(e) => mudar("politica", e.target.value)}><option value="todas">Em todas as origens válidas</option><option value="abstencao">Permitir abstenção (em estudo)</option><option value="gatilho">Só após um gatilho (em estudo)</option></select></label></div>
      <details><summary>Como interpretar prazos, janelas e estilos</summary><p>Os prazos são candidatos para discussão. Day trading envolve encerrar a posição no mesmo dia; prever 24h à frente não define uma operação desse tipo. Swing pode durar dias ou semanas. Uma semana não é uma fronteira universal entre estilos. <a href="https://www.schwab.com/learn/story/swing-trading-strategies" target="_blank" rel="noreferrer">Referência de uso profissional ↗</a></p><p>Contexto é a janela deslizante de passado. Horizonte é o futuro previsto. A janela avança com cada nova origem; isso não implica treinar de novo a cada candle. O timestamp identifica um instante, enquanto 15m/1h/4h/1d são durações.</p><p>Trocar o candle e usar “próximo candle” muda também o prazo. Para medir só o efeito da resolução, manter horizonte, contexto e horários comuns. Se o horizonte for menor que o candle, será necessário construir o alvo usando dados mais finos. Horizontes longos com origens frequentes geram alvos sobrepostos, exigindo purga e inferência adequadas.</p></details>
    </section>
    <section className="bloco"><div className="titulo-com-acao"><h2>Lista para discutir com o orientador</h2><span className="selo">{propostas.length} combinações</span></div>
      {propostas.length === 0 ? <p className="miudo">Adicione combinações para comparar suas perguntas. Nenhuma foi selecionada ainda.</p> : <div className="tabela-container"><table><thead><tr><th>Moeda / candle</th><th>Previsão / prazo</th><th>Contexto / origens</th><th>Respostas</th><th><span className="sr-only">Ação</span></th></tr></thead><tbody>{propostas.map((c) => <tr key={chaveCombinacao(c)}><th scope="row">{c.moeda} · {c.candle}</th><td>{tarefasPrevisao.find((t) => t.id === c.tipo)!.nome}<small>{nomePrazo(c.horizonte)}</small></td><td>{c.contexto} dias<small>{c.agenda === "diaria" ? "00:00 UTC" : "Cada candle"}</small></td><td>{c.politica === "todas" ? "Todas" : c.politica === "abstencao" ? "Com abstenção" : "Por gatilho"}</td><td><button className="botao-texto" aria-label={`Remover ${c.moeda}, ${c.candle}, ${nomePrazo(c.horizonte)}, ${c.tipo}, ${c.contexto} dias, ${c.agenda}, ${c.politica}`} onClick={() => remover(chaveCombinacao(c))}>Remover</button></td></tr>)}</tbody></table></div>}
    </section>
  </>;
}
