"use client";

import { useEffect, useMemo, useState } from "react";
import type { Execucao } from "@/lib/registros";

type Opcoes = { pares: string[]; contextos: number[]; horizontes: number[]; folds: string[] };
type Metrica = "log_loss" | "brier" | "balanced_accuracy" | "retorno_liquido" | "drawdown_maximo" | "operacoes";
const estados: Record<string, string> = { preparando: "Preparando", treinando: "Treinando", baseline: "Calculando AR(1)", avaliando: "Auditando", concluida_auditada: "Concluída e auditada", falha: "Falha registrada", interrompido: "Interrompida" };
const nomes: Record<Metrica, string> = { log_loss: "Log-loss", brier: "Brier", balanced_accuracy: "Acerto balanceado", retorno_liquido: "Retorno após custos", drawdown_maximo: "Drawdown máximo", operacoes: "Número de operações" };
const notas: Record<Metrica, string> = {
  log_loss: "Menor é melhor. Compare os modelos na mesma combinação; a dificuldade e a frequência das classes mudam com o prazo.",
  brier: "Menor é melhor. Mede o erro das probabilidades das três classes.",
  balanced_accuracy: "Média do acerto por classe. Fica indisponível quando alguma classe não ocorre no recorte.",
  retorno_liquido: "Cenário base, após taxas e slippage. Retorno zero com nenhuma operação significa permanência em caixa.",
  drawdown_maximo: "Maior queda relativa a um pico anterior, com patrimônio marcado a mercado a cada minuto.",
  operacoes: "Entradas efetivamente executadas pela política. Há uma posição por vez; nem todo sinal gera uma operação.",
};

function valor(r: Execucao, modelo: string, metrica: Metrica) {
  if (r.status !== "concluida_auditada") return { texto: "Aguardando", detalhe: "" };
  const f = r.financeiro?.[modelo]?.base;
  const financeira = ["retorno_liquido", "drawdown_maximo", "operacoes"].includes(metrica);
  if (financeira && f?.status !== "auditavel") return { texto: "Indisponível", detalhe: "Percurso incompleto" };
  let n: number | null | undefined;
  if (metrica === "retorno_liquido" || metrica === "drawdown_maximo" || metrica === "operacoes") n = f?.[metrica];
  else n = r.resultados?.[modelo]?.metricas.teste[metrica];
  if (n == null || !Number.isFinite(n)) return { texto: "Indisponível", detalhe: "" };
  const percentual = ["balanced_accuracy", "retorno_liquido", "drawdown_maximo"].includes(metrica);
  const casas = percentual ? 2 : metrica === "operacoes" ? 0 : 4;
  return { texto: `${(percentual ? n * 100 : n).toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas })}${percentual ? "%" : ""}`,
    detalhe: financeira && metrica !== "operacoes" ? `${f?.operacoes ?? "—"} operações` : "" };
}

export default function ResultadosPesquisa({ iniciais, avisosIniciais, opcoes }: { iniciais: Execucao[]; avisosIniciais: string[]; opcoes: Opcoes }) {
  const [registros, setRegistros] = useState(iniciais);
  const [avisos, setAvisos] = useState(avisosIniciais);
  const [consulta, setConsulta] = useState("");
  const [erro, setErro] = useState("");
  const [moeda, setMoeda] = useState("");
  const [contexto, setContexto] = useState("");
  const [prazo, setPrazo] = useState("");
  const [fold, setFold] = useState("");
  const [ciclo, setCiclo] = useState("");
  const [metrica, setMetrica] = useState<Metrica>("log_loss");
  useEffect(() => {
    const controle = new AbortController();
    let encerrado = false;
    async function atualizar() {
      try {
        const resposta = await fetch("/api/estudo/resultados", { cache: "no-store", signal: controle.signal });
        if (!resposta.ok) throw new Error("Consulta indisponível.");
        const dados = await resposta.json() as { resultados: Execucao[]; avisos: string[]; atualizacao: string };
        if (!encerrado) { setRegistros(dados.resultados); setAvisos(dados.avisos); setConsulta(dados.atualizacao); setErro(""); }
      } catch { if (!encerrado) setErro("Não foi possível atualizar agora. Os últimos registros continuam exibidos."); }
    }
    void atualizar();
    const intervalo = setInterval(atualizar, 30000);
    return () => { encerrado = true; controle.abort(); clearInterval(intervalo); };
  }, []);
  const ciclos = useMemo(() => [...new Map(registros.map(r => [r.id_ciclo ?? r.ciclo, `${r.ciclo} · ${(r.id_ciclo ?? r.ciclo).slice(0, 8)}`])).entries()], [registros]);
  const exibidos = useMemo(() => registros.filter(r =>
    (!moeda || r.celula.par === moeda) && (!contexto || r.celula.contexto === Number(contexto)) &&
    (!prazo || r.celula.horizonte === Number(prazo)) && (!fold || r.celula.fold === fold) &&
    (!ciclo || (r.id_ciclo ?? r.ciclo) === ciclo)).sort((a, b) =>
    a.ciclo.localeCompare(b.ciclo) || (a.id_ciclo ?? "").localeCompare(b.id_ciclo ?? "") ||
    a.celula.fold.localeCompare(b.celula.fold) || opcoes.pares.indexOf(a.celula.par) - opcoes.pares.indexOf(b.celula.par) ||
    a.celula.horizonte - b.celula.horizonte || a.celula.contexto - b.celula.contexto ||
    a.celula.seed - b.celula.seed || (a.inicio_utc ?? "").localeCompare(b.inicio_utc ?? "")),
  [registros, moeda, contexto, prazo, fold, ciclo, opcoes.pares]);
  const concluidas = registros.filter(r => r.status === "concluida_auditada").length;
  return <section id="resultados">
    <div className="titulo"><h2>Execuções e evidências</h2><span>{concluidas} execuções auditadas</span></div>
    <div className="filtros">
      <label>Moeda<select value={moeda} onChange={e => setMoeda(e.target.value)}><option value="">Todas</option>{opcoes.pares.map(x => <option key={x}>{x}</option>)}</select></label>
      <label>Contexto<select value={contexto} onChange={e => setContexto(e.target.value)}><option value="">Todos</option>{opcoes.contextos.map(x => <option key={x} value={x}>{x} horas</option>)}</select></label>
      <label>Prazo máximo<select value={prazo} onChange={e => setPrazo(e.target.value)}><option value="">Todos</option>{opcoes.horizontes.map(x => <option key={x} value={x}>{x} horas</option>)}</select></label>
      <label>Período<select value={fold} onChange={e => setFold(e.target.value)}><option value="">Todos</option>{opcoes.folds.map(x => <option key={x}>{x}</option>)}</select></label>
      <label>Identidade do ciclo<select value={ciclo} onChange={e => setCiclo(e.target.value)}><option value="">Todas</option>{ciclos.map(([id, rotulo]) => <option key={id} value={id}>{rotulo}</option>)}</select></label>
      <label>Métrica<select value={metrica} onChange={e => setMetrica(e.target.value as Metrica)}>{Object.entries(nomes).map(([id, nome]) => <option key={id} value={id}>{nome}</option>)}</select></label>
    </div>
    <p className="nota">{notas[metrica]}</p>
    <p className="estado-consulta">{exibidos.length} de {registros.length} registros exibidos. Atualização automática a cada 30 segundos.{consulta && ` Consulta: ${new Date(consulta).toLocaleTimeString("pt-BR")}.`}</p>
    {exibidos.length === 0 ? <div className="vazio"><h3>Nenhuma execução neste recorte.</h3><p>Combinações ainda não executadas não recebem resultados simulados. Falhas e tentativas interrompidas permanecem no histórico.</p></div> :
      <div className="tabela"><table><thead><tr><th>Moeda / período</th><th>Contexto / prazo</th><th>Último estado registrado</th><th>Mamba</th><th>LSTM</th><th>AR(1)</th></tr></thead><tbody>{exibidos.map(r => <tr key={r.id}>
        <td>{r.celula.par}<small>{r.celula.fold} · seed {r.celula.seed}</small><small>{r.ciclo} · {(r.id_ciclo ?? "").slice(0, 8)}</small></td>
        <td>{r.celula.contexto}h / {r.celula.horizonte}h<small>Execução {r.id.slice(0, 8)}</small></td>
        <td>{estados[r.status] ?? r.status}{r.modelo && r.status === "treinando" && <small>{r.modelo}</small>}{r.status === "concluida_auditada" && <small>{r.resultados?.mamba?.metricas.teste.n.toLocaleString("pt-BR")} origens preditivas</small>}</td>
        {["mamba", "lstm", "ar1"].map(modelo => { const v = valor(r, modelo, metrica); return <td className="numero" key={modelo}>{v.texto}{v.detalhe && <small>{v.detalhe}</small>}</td>; })}
      </tr>)}</tbody></table></div>}
    {registros.filter(r => r.erro).map(r => <details key={r.id}><summary>Falha registrada · {r.celula.par} · {r.id.slice(0, 8)}</summary><p>{r.erro}</p></details>)}
    {[...avisos, ...(erro ? [erro] : [])].map(a => <p role="status" key={a}>{a}</p>)}
    <p className="nota">Cada linha compara os três modelos na mesma combinação. Os filtros só mudam a visualização. O estado exibido vem do último registro; não certifica que um processo permaneça ativo.</p>
  </section>;
}
