"use client";

import { useCallback, useEffect, useState } from "react";
import { moedas, type RespostaResultados } from "@/lib/estudo";
import MatrizExperimentos from "@/components/MatrizExperimentos";
import { ResumoProjeto, MetodologiaProjeto, DadosProjeto, EntregasProjeto } from "@/components/SecoesProjeto";

const secoes = [
  { id: "panorama", nome: "Resumo do projeto", icone: "grid" },
  { id: "metodo", nome: "Metodologia", icone: "layers" },
  { id: "matriz", nome: "Configurações experimentais", icone: "grid" },
  { id: "dados", nome: "Dados e ativos", icone: "database" },
  { id: "plano", nome: "Entregas e execução", icone: "route" },
  { id: "resultados", nome: "Resultados e interpretação", icone: "chart" },
] as const;
type Secao = typeof secoes[number]["id"];
const porcentagem = (n: number | null) => n === null ? "Indisponível" : `${(n * 100).toFixed(2).replace(".", ",")}%`;
const pontos = (n: number | null) => n === null ? "—" : `${n > 0 ? "+" : ""}${n.toFixed(2).replace(".", ",")} p.p.`;

async function consultarResultados(sinal?: AbortSignal): Promise<RespostaResultados> {
  const resposta = await fetch("/api/estudo/resultados", { cache: "no-store", signal: sinal });
  if (!resposta.ok) throw new Error("A leitura dos resultados locais falhou. Tente atualizar.");
  return resposta.json();
}

function Icone({ nome, tamanho = 20 }: { nome: string; tamanho?: number }) {
  const caminhos: Record<string, React.ReactNode> = {
    grid: <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></>,
    layers: <path d="m12 3 9 5-9 5-9-5 9-5Zm-9 9 9 5 9-5M3 16l9 5 9-5" />,
    database: <><ellipse cx="12" cy="5" rx="8" ry="3" /><path d="M4 5v14c0 4 16 4 16 0V5M4 12c0 4 16 4 16 0" /></>,
    route: <><circle cx="5" cy="5" r="2" /><circle cx="19" cy="19" r="2" /><path d="M7 5h9a4 4 0 0 1 0 8H8a3 3 0 0 0 0 6h9" /></>,
    chart: <path d="M3 3v18h18M7 16l4-6 4 3 6-9" />,
    arrow: <path d="M5 12h14m-5-5 5 5-5 5" />,
    file: <><path d="M14 2H5v20h14V7l-5-5Z" /><path d="M14 2v6h5M8 12h8M8 16h6" /></>,
  };
  return <svg aria-hidden="true" width={tamanho} height={tamanho} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">{caminhos[nome] ?? caminhos.grid}</svg>;
}
function Etiqueta({ children, tom = "neutro" }: { children: React.ReactNode; tom?: string }) {
  return <span className={`etiqueta ${tom}`}><span className="ponto" />{children}</span>;
}
function Documento({ id, children = "Ler documento" }: { id: string; children?: React.ReactNode }) {
  return <a className="link-documento" href={`/api/estudo/documentos/${id}`} target="_blank" rel="noreferrer"><Icone nome="file" tamanho={15} />{children}<span aria-hidden="true">↗</span></a>;
}
function Titulo({ titulo, texto }: { titulo: string; texto: string }) {
  return <div className="titulo-secao"><h2>{titulo}</h2><p>{texto}</p></div>;
}
export default function Dashboard() {
  const [secao, setSecao] = useState<Secao>("panorama");
  const [moeda, setMoeda] = useState("BTC");
  const [comparacao, setComparacao] = useState("ar1");
  const [locais, setLocais] = useState<RespostaResultados | null>(null);
  const [erro, setErro] = useState("");
  const [carregando, setCarregando] = useState(true);
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" });
  }, [secao]);
  const carregar = useCallback(async () => {
    setCarregando(true); setErro("");
    try {
      setLocais(await consultarResultados());
    } catch (falha) { setErro(falha instanceof Error ? falha.message : "Falha de conexão."); }
    finally { setCarregando(false); }
  }, []);
  useEffect(() => {
    const controlador = new AbortController();
    consultarResultados(controlador.signal).then((dados) => {
      if (!controlador.signal.aborted) setLocais(dados);
    }).catch((falha) => {
      if (!controlador.signal.aborted) setErro(falha instanceof Error ? falha.message : "Falha de conexão.");
    }).finally(() => {
      if (!controlador.signal.aborted) setCarregando(false);
    });
    return () => controlador.abort();
  }, []);
  const resultados = (locais?.resultados ?? []).filter((r) => r.par === `${moeda}USDT`);
  const descricoes: Record<Secao, string> = {
    panorama: "Objetivo, escopo, situação atual e próximos passos do trabalho de conclusão de curso.",
    metodo: "Modelos, regras de comparação, divisão temporal e critérios de avaliação.",
    matriz: "Combinações de ativos, resoluções, janelas, entradas e períodos previstas no protocolo.",
    dados: "Origem dos dados, propriedades dos ativos, cobertura e análise descritiva de volatilidade.",
    plano: "Cronograma, evidências de conclusão e pendências para a execução dos experimentos.",
    resultados: "Resultados documentados, execuções disponíveis e formato previsto para a análise final.",
  };

  return <div className="estudo-app">
    <a href="#conteudo" className="pular">Pular para o conteúdo</a>
    <aside className="barra-lateral">
      <a className="marca" href="#conteudo" onClick={() => setSecao("panorama")}><div>CryptoCasting<small>Documentação do TCC</small></div></a>
      <div className="rotulo-nav">SUMÁRIO</div>
      <nav aria-label="Seções do projeto">{secoes.map((s, i) => <button key={s.id} className={s.id === secao ? "ativo" : ""} aria-current={s.id === secao ? "page" : undefined} onClick={() => setSecao(s.id)}><span className="nav-numero">{String(i + 1).padStart(2, "0")}</span><span>{s.nome}</span></button>)}</nav>
      <div className="lateral-nota"><span className="pequeno">REFERÊNCIA METODOLÓGICA</span><p>Protocolo experimental 1.6</p><Documento id="protocolo">Consultar documento</Documento></div>
      <div className="lateral-rodape">Estado documentado<small>13 de outubro de 2026</small><small>Resultados locais lidos separadamente.</small></div>
    </aside>
    <div className="area-principal">
      <header className="barra-superior"><div>TCC · Ciência da Computação <span>/</span> CryptoCasting</div><span>Consulta do projeto</span></header>
      <main id="conteudo" className="conteudo" tabIndex={-1}>
        <div className="cabecalho-pagina"><div><h1>{secoes.find((s) => s.id === secao)?.nome}</h1><p>{descricoes[secao]}</p></div></div>
        {secao === "panorama" && <ResumoProjeto />}
        {secao === "metodo" && <MetodologiaProjeto />}
        {secao === "matriz" && <MatrizExperimentos />}
        {secao === "dados" && <DadosProjeto />}
        {secao === "plano" && <EntregasProjeto />}
        {secao === "resultados" && <>
          <Titulo titulo="Estado das avaliações" texto="O piloto histórico e as execuções locais são desenvolvimento. A matriz final de 2024–2025 será preenchida após o congelamento metodológico." />
          <section className="painel"><h2>Piloto neural CPU concluído</h2><p>Em 13/10/2026, o piloto BTCUSDT / 1d / D1 foi treinado e auditado: BA Mamba 41,46%, LSTM 50,00% e AR(1) 46,34%. A recarga dos checkpoints reproduziu exatamente as previsões. Este resultado valida o funcionamento do fluxo em CPU; o desempenho observado não favoreceu o Mamba.</p><p className="nota">Uma moeda, um fold e uma seed. O backend oficial/CUDA permanece pendente por indisponibilidade do ambiente. As métricas detalhadas desta execução aparecem na tabela de arquivos locais abaixo, quando seus artefatos estão presentes.</p><Documento id="piloto-neural">Relatório, matrizes de confusão e auditoria</Documento></section>
          <section className="painel"><div className="painel-topo"><div><span className="sobretitulo">EVIDÊNCIA DOCUMENTADA · 2023</span><h3>Piloto AR(1) — Bitcoin</h3></div><Etiqueta tom="ambar">Desenvolvimento</Etiqueta></div><div className="piloto-conteudo"><div className="piloto-numero"><strong>49,11<span>%</span></strong><span>BA média dos quatro folds</span><small>Média não ponderada · BTCUSDT</small></div><div className="piloto-folds">{[['D1','46,34%'],['D2','50,11%'],['D3','47,06%'],['D4','52,94%']].map(([fold, ba]) => <div key={fold}><span>{fold}</span><b>{ba}</b></div>)}</div></div><p className="nota">Este AR(1) apresentou baixo recall de alta. O resultado não avalia toda a família ARIMA, outras moedas ou a capacidade do Mamba. O treino cresce entre folds, mas o trimestre avaliado também muda.</p><Documento id="piloto">Relatório e interpretação do piloto</Documento></section>
          <section className="painel"><div className="painel-topo"><div><span className="sobretitulo">FORMATO DOS RESULTADOS FINAIS</span><h3>Matriz prevista para a avaliação final</h3></div><Etiqueta>F1–F8 · pendente</Etiqueta></div><div className="abas-comparacao" aria-label="Tipo de comparação">{[['ar1','Mamba × AR(1)'],['lstm','Mamba × LSTM'],['acaso','Referência de 50%'],['pt','Teste PT']].map(([id, texto]) => <button key={id} aria-pressed={comparacao === id} className={comparacao === id ? 'selecionada' : ''} onClick={() => setComparacao(id)}>{texto}</button>)}</div><p className="texto-suave">{comparacao === 'ar1' ? 'BA de cada modelo e diferença Mamba − AR(1), em pontos percentuais.' : comparacao === 'lstm' ? 'BA das duas redes nas mesmas entradas e diferença Mamba − LSTM, em pontos percentuais.' : comparacao === 'acaso' ? 'Distância da BA do Mamba a 50%, quando ambas as classes reais aparecem. Não é um p-valor.' : 'Estatística e p-valor por modelo e seed. PT avalia associação direcional; não testa a diferença de desempenho entre modelos.'}</p><div className="tabela-container"><table className="matriz-final"><caption>Modelo de apresentação · horizonte 24h · contexto 7 dias · sem resultados finais</caption><thead><tr><th>Moeda / candle</th>{['15 min','1 hora','4 horas','1 dia'].map((c) => <th key={c}>{c}</th>)}</tr></thead><tbody>{moedas.map((m) => <tr key={m.sigla}><th scope="row"><span className="ponto-moeda" style={{background:m.cor}} />{m.sigla}</th>{[0,1,2,3].map((i) => <td key={i}><span className="pendente-celula">— <small>A avaliar</small></span></td>)}</tr>)}</tbody></table></div><p className="nota">As matrizes serão repetidas para contexto de 14 dias e próximo candle. A célula diária de próximo candle reutiliza a principal. Uma diferença positiva observada não prova superioridade estatística.</p></section>
          <section className="painel"><div className="painel-topo"><div><span className="sobretitulo">ARQUIVOS LOCAIS · NOVA INFRAESTRUTURA</span><h3>Execuções pareadas {locais && <span className="contador">{locais.resultados.length}</span>}</h3></div><button className="botao-contorno" onClick={() => void carregar()} disabled={carregando}>{carregando ? 'Lendo…' : 'Atualizar'}</button></div><p className="texto-suave">Resumos concluídos em <code>dados/experimentos/pareado_*</code>. Cada linha identifica uma execução; não se escolhe automaticamente a melhor tentativa.</p><div className="filtros"><label>Moeda<select value={moeda} onChange={(e) => setMoeda(e.target.value)}>{moedas.map((m) => <option key={m.sigla}>{m.sigla}</option>)}</select></label></div>{erro && <p role="alert" className="aviso-erro">{erro}</p>}{!erro && !carregando && resultados.length === 0 && <div className="estado-vazio"><Icone nome="chart" tamanho={34} /><h4>Nenhuma execução pareada de {moeda} encontrada.</h4><p>Depois de executar o piloto, atualize esta seção para ler o resultado real.</p><button className="link-botao" onClick={() => setSecao('plano')}>Ver como executar <Icone nome="arrow" tamanho={15} /></button></div>}{resultados.length > 0 && <div className="tabela-container"><table><caption>Resultados por fold de desenvolvimento · BA e diferenças em p.p.</caption><thead><tr><th>Execução</th><th>Configuração</th><th>BA Mamba</th><th>BA LSTM</th><th>BA AR(1)</th><th>Δ AR(1)</th><th>Δ LSTM</th><th>Δ 50%</th></tr></thead><tbody>{resultados.map((r) => <tr key={r.pasta}><th scope="row">{r.fold} · n={r.amostras}<small className="linha-meta">{r.pasta}</small></th><td>{r.granularidade} · {r.contexto}d · {r.tarefa}<small className="linha-meta">{r.features} · {r.normalizador} · seed {r.seed}<br />M{r.larguraMamba}/L{r.larguraLstm} · {r.backend} · {r.dispositivo}<br />código {r.codigo.slice(0,10)}</small></td><td>{porcentagem(r.ba.mamba)}</td><td>{porcentagem(r.ba.lstm)}</td><td>{porcentagem(r.ba.ar1)}</td><td>{pontos(r.diferencas.mamba_menos_ar1)}</td><td>{pontos(r.diferencas.mamba_menos_lstm)}</td><td>{pontos(r.diferencas.mamba_menos_50)}</td></tr>)}</tbody></table></div>}{locais && locais.avisos.length > 0 && <details className="avisos-locais"><summary>{locais.avisos.length} execução(ões) com pendências</summary><ul>{locais.avisos.map((a) => <li key={a}>{a}</li>)}</ul></details>}<p className="nota">Leitura de resumos locais; a auditoria completa dos hashes é feita por <code>run_avaliacao.py</code>. Resultados ausentes são exibidos como ausentes, nunca como zero.</p></section>
        </>}
        <footer className="rodape"><span>CryptoCasting <b>·</b> Murilo R. F. Monferrari</span><span>Protocolo 1.6 · Estado técnico de 13/10/2026</span></footer>
      </main>
    </div>
  </div>;
}
