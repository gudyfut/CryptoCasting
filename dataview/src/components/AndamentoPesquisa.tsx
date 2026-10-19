import type { Execucao } from "@/lib/registros";
import type { Resumo } from "@/lib/caderno";

const entregas = [
  ["Implementação e verificação dos contratos", "Rotulagem, entradas causais, purgas, normalização e contabilidade. Testes de casos-limite e de vazamento.", "protocolo"],
  ["Coleta e construção do conjunto de dados", "144 arquivos mensais de 2021–2023, quatro moedas e dados de minuto. Lacunas preservadas, sem interpolação.", "andamento"],
  ["Qualificação do ambiente e dos modelos", "Mamba oficial em CUDA e AR(1) probabilístico. Verificação funcional e numérica antes dos ajustes de mercado.", "andamento"],
  ["Execução e auditoria dos casos iniciais", "Dois casos BTC/DB1, incluindo contexto e prazo longos. Recargas exatas; casos incorporados à grade, sem duplicar contagens.", "andamento"],
  ["Grade completa e auditoria integral", "Quatro trimestres de desenvolvimento, todas as moedas, contextos e prazos. Verificação dos registros, previsões e operações.", "resultados"],
  ["Consolidação e proposta do ciclo seguinte", "Relatório integral, tabelas, intervalos de incerteza e limitações. Proposta de ablação do estado do Mamba, ainda não executada.", "resultados"],
];
const agendaAcademica = [
  ["1–5", "08/09–11/10", "Protocolo, dados, amostras, infraestrutura e Mamba em GPU", "Conteúdo técnico disponível no escopo atual; pontualidade e aceite não comprovados."],
  ["6", "12/10–18/10", "Granularidade e contexto", "Parcial/alterada: contexto e prazo comparados; granularidade fixa em 1h."],
  ["7", "19/10–25/10", "Representação das entradas", "Semana corrente na data da conferência; comparação ainda não executada."],
  ["8", "26/10–01/11", "Normalização e configurações internas", "Pendente; proposta 002 não executada."],
  ["9–10", "02/11–15/11", "Múltiplas seeds e análise final", "Pendentes; uma seed no ciclo atual e avaliação final bloqueada."],
  ["11–12", "16/11–23/11", "Texto final e fechamento", "Futuros; conclusão acadêmica não comprovada."],
];
export default function AndamentoPesquisa({ resumo, execucoes }: { resumo: Resumo; execucoes: Execucao[] }) {
  const concluidas = execucoes.filter(e => e.id_ciclo === resumo.id_ciclo && e.status === "concluida_auditada" && e.auditoria === "aprovado");
  const integro = concluidas.length === resumo.celulas;
  const inicio = concluidas.map(e => e.inicio_utc).sort()[0];
  const fim = concluidas.map(e => e.fim_utc ?? "").sort().at(-1);
  const instante = (s: string | undefined) => s ? new Date(s).toLocaleString("pt-BR", { timeZone: "UTC", dateStyle: "short", timeStyle: "short" }) : "Indisponível";
  return <section id="andamento" className="andamento-pesquisa"><div className="cabecalho-capitulo"><span className="numero-capitulo">00</span><div><p className="etiqueta">SITUAÇÃO DOCUMENTADA</p><h2>Entregas e cronologia da pesquisa</h2></div></div>
    <p className="destaque-texto">{integro ? "Seis marcos do primeiro ciclo concluídos. A pesquisa continua em desenvolvimento." : "Verificação incompleta dos registros. Consulte as evidências antes de declarar o ciclo concluído."}</p>
    <p>Esta contagem segue os seis marcos registrados em <a href="/api/estudo/documentos/plano" target="_blank" rel="noreferrer">plano.md</a>. Não significa seis etapas de um TCC inteiro, nem uma porcentagem de conclusão acadêmica. Executar a primeira grade, confirmar uma hipótese e concluir a monografia são entregas distintas. Consulte o <a href="/api/estudo/documentos/entregas" target="_blank" rel="noreferrer">registro formal de entregas</a> e o <a href="/api/estudo/documentos/avaliacao" target="_blank" rel="noreferrer">guia de avaliação</a>.</p>
    <h3>Entregas ao orientador · conferência em 19/10/2026</h3>
    <p>O <a href="/api/estudo/documentos/cronograma" target="_blank" rel="noreferrer">cronograma original em PDF</a> foi recuperado do histórico e contém <b>12 entregas acadêmicas</b>. Seus números não correspondem aos seis marcos técnicos deste ciclo.</p>
    <div className="tabela"><table><caption>Correspondência com o cronograma original; situação técnica, não confirmação de envio</caption><thead><tr><th>Entrega</th><th>Período</th><th>Compromisso original</th><th>Situação verificada</th></tr></thead><tbody>{agendaAcademica.map(([n, periodo, titulo, estado]) => <tr key={n}><th>{n}</th><td>{periodo}</td><td>{titulo}</td><td>{estado}</td></tr>)}</tbody></table></div>
    <aside><b>A alteração da entrega 6 ainda precisa ser apresentada ao orientador.</b> Situação confirmada pelo pesquisador em 19/10/2026. Comparar prazos de previsão não equivale a comparar tamanhos de candle: há resultados para contexto e prazo, mas a reformulação do compromisso original está pendente de apresentação e alinhamento. Disponibilidade técnica hoje também não comprova entrega no prazo original.</aside>
    <p>Leia a <a href="/api/estudo/documentos/orientador" target="_blank" rel="noreferrer">conferência completa das 12 entregas</a> e a <a href="/api/estudo/documentos/adaptativa" target="_blank" rel="noreferrer">proposta de pesquisa adaptativa</a>. Esta proposta está em discussão: não substitui o protocolo vigente nem inicia novos treinamentos.</p>
    <h3>Seis marcos técnicos do ciclo 001</h3>
    <div className="indicadores-formais"><div><strong>{concluidas.length}/{resumo.celulas}</strong><span>células auditadas</span></div><div><strong>{resumo.treinamentos.reduce((s, t) => s + t.ajustes, 0)}</strong><span>ajustes neurais</span></div><div><strong>{new Set(concluidas.map(e => `${e.celula.par}/${e.celula.fold}`)).size}</strong><span>ajustes únicos AR(1)</span></div><div><strong>DB1–DB4</strong><span>testes de desenvolvimento</span></div></div>
    <ol className="cronologia-entregas">{entregas.map(([titulo, texto, fonte], i) => <li key={titulo}><span className="marco-indice">{String(i + 1).padStart(2, "0")}</span><div><div className="marco-titulo"><h3>{titulo}</h3><span className="estado-marco">{integro ? "Concluído" : "Verificar"}</span></div><p>{texto}</p><a href={`/api/estudo/documentos/${fonte}`} target="_blank" rel="noreferrer">Evidência documental ↗</a></div></li>)}</ol>
    <div className="duas-colunas"><article className="texto-card"><h3>Tempo do mercado</h3><p>2021–2022: passado usado nos primeiros ajustes. Janeiro a dezembro de 2023: quatro testes trimestrais. 2024–2025: avaliação final planejada e bloqueada.</p></article><article className="texto-card"><h3>Tempo de execução da pesquisa</h3><p>Primeiro ajuste registrado: <b>{instante(inicio)} UTC</b>. Último encerramento da grade: <b>{instante(fim)} UTC</b>. Fechamento documental: 18/10/2026. Revisão do portal e explorador: 19/10/2026.</p></article></div>
    <div className="proximas-entregas"><h3>Entregas ainda não concluídas</h3><ul><li><b>Próximos ciclos:</b> proposta 002 registrada; qualificação da variante e execução ainda pendentes.</li><li><b>Confirmação e congelamento:</b> avaliar estabilidade entre inicializações, documentar escolhas e exposição prévia aos dados.</li><li><b>Avaliação final B1–B4:</b> bloqueada. Não há resultado final independente para apresentar.</li><li><b>Monografia e defesa:</b> redação final, revisão pelo orientador e entrega acadêmica não comprovadas por estes registros.</li></ul><p>Uma simulação em futuros é uma possível extensão, ainda não implementada e não incluída como entrega concluída. O estudo atual avalia compra à vista ou caixa.</p></div>
  </section>;
}
