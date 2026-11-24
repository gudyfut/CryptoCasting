'use client';
import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { capitulos, etapas, fases } from '@/lib/etapas';
import { type DadosPanorama, type Etapa, type EvolucaoPesquisa, type CatalogoFichas } from '@/lib/panorama-tipos';
import type { Disponibilidade } from '@/lib/panorama-servidor';
import Resultados from './Resultados';
import Previsoes from './Previsoes';
import Metodo from './Metodo';
import { VisaoPesquisa, DetalheFase, Conclusoes } from './Evolucao';
import FichaTecnica, { EssenciaisFase, PreferenciasFicha } from './FichaTecnica';

const abas = [['experimento', 'Resumo'], ['configuracao', 'Configuração'], ['resultados', 'Métricas'], ['previsoes', 'Previsões'], ['fontes', 'Fontes']] as const;
const gruposFases = [
  { nome: '01 — Fundamentos', inicio: 0, fim: 3 },
  { nome: '02 — Busca de melhorias', inicio: 3, fim: 5 },
  { nome: '03 — Linha diária', inicio: 5, fim: 10 },
];
const nomesFases = ['Primeiras tentativas', 'Modelos de referência', 'Entradas e treinamento', 'Busca com IA', 'Histórico de 12 meses', 'Candles diários', 'Alvo de retorno', 'Entradas padronizadas', 'Sem penalização', 'ETH, BNB e XRP'];
type Navegar = (id: string | null, aba?: string, vista?: string) => void;
function Marca() { return <span className="marca">CryptoCasting<small>EVOLUÇÃO DA PESQUISA</small></span>; }

export default function Panorama({ dados, disponibilidade, evolucao, fichas, inicial }: { dados: DadosPanorama; disponibilidade: Disponibilidade; evolucao: EvolucaoPesquisa; fichas: CatalogoFichas; inicial: { etapa?: string; aba?: string; vista?: string } }) {
  const router = useRouter();
  const [selecionada, setSelecionada] = useState([...etapas, ...fases].some(e => e.id === inicial.etapa) ? inicial.etapa! : null);
  const [aba, setAba] = useState(inicial.aba ?? 'experimento');
  const [vista, setVista] = useState(inicial.vista === 'metodo' || inicial.vista === 'sintese' ? inicial.vista : 'percurso');
  const [apresentacao, setApresentacao] = useState(false);
  const [menu, setMenu] = useState(false);
  const [copiado, setCopiado] = useState(false);
  const [avisoCopia, setAvisoCopia] = useState('');
  const etapa = etapas.find(e => e.id === selecionada);
  const fase = fases.find(f => f.id === selecionada);
  const sequencia = etapa ? etapas : fases;
  const ativa = etapa ?? fase;
  const indice = sequencia.findIndex(e => e.id === selecionada);
  useEffect(() => {
    const atualizar = () => { if (document.visibilityState === 'visible') router.refresh(); };
    const intervalo = window.setInterval(atualizar, 60_000);
    return () => window.clearInterval(intervalo);
  }, [router]);
  const abasVisiveis = abas.filter(([id]) => (id !== 'previsoes' || etapa?.exemplos) && (id !== 'resultados' || etapa?.publicacao));
  const abaAtual = abasVisiveis.some(([id]) => id === aba) ? aba : 'experimento';
  const navegar: Navegar = useCallback((id, abaNova = 'experimento', vistaNova = 'percurso') => {
    setSelecionada(id); setAba(abaNova); setVista(vistaNova); setMenu(false);
    const q = new URLSearchParams();
    if (id) { q.set('etapa', id); q.set('aba', abaNova); }
    else if (vistaNova !== 'percurso') q.set('vista', vistaNova);
    window.history.pushState({}, '', `/${q.size ? '?' + q : ''}`);
    window.scrollTo({ top: 0, behavior: 'instant' });
  }, []);
  useEffect(() => {
    const voltar = () => {
      const q = new URLSearchParams(window.location.search);
      setSelecionada([...etapas, ...fases].some(e => e.id === q.get('etapa')) ? q.get('etapa') : null);
      setAba(q.get('aba') ?? 'experimento'); setVista(q.get('vista') ?? 'percurso');
    };
    window.addEventListener('popstate', voltar);
    return () => window.removeEventListener('popstate', voltar);
  }, []);
  useEffect(() => {
    if (!apresentacao) return;
    const tecla = (e: KeyboardEvent) => {
      if (['INPUT', 'SELECT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)) return;
      if (e.key === 'Escape') setApresentacao(false);
      if (e.key === 'ArrowRight' && indice < sequencia.length - 1) { e.preventDefault(); navegar(sequencia[indice + 1].id, aba); }
      if (e.key === 'ArrowLeft' && indice > 0) { e.preventDefault(); navegar(sequencia[indice - 1].id, aba); }
    };
    window.addEventListener('keydown', tecla);
    return () => window.removeEventListener('keydown', tecla);
  }, [apresentacao, indice, navegar, sequencia, aba]);
  function apresentar() { if (!ativa) navegar(fases[0].id); setApresentacao(true); }
  async function copiar() {
    try { await navigator.clipboard.writeText(window.location.href); setCopiado(true); setAvisoCopia(''); setTimeout(() => setCopiado(false), 2200); }
    catch { setAvisoCopia('Copie o endereço da barra do navegador.'); }
  }
  return <div className={apresentacao ? 'aplicacao apresentacao' : 'aplicacao'}>
    <a className="pular" href="#conteudo">Pular para o conteúdo</a>
    <header className="cabecalho">
      <button className="marca-botao" aria-label="Voltar à visão geral" onClick={() => navegar(null)}><Marca /></button>
      <div className="identidade-tcc">Murilo R. F. Monferrari · UNIFEI</div>
      <div className="acoes-topo"><button className="botao secundario pequeno" onClick={apresentacao ? () => setApresentacao(false) : apresentar}>{apresentacao ? 'Sair da apresentação' : 'Apresentar'}</button><button className="abrir-menu" aria-expanded={menu} aria-label="Abrir navegação" onClick={() => setMenu(!menu)}>☰</button></div>
    </header>
    <aside className={menu ? 'lateral aberta' : 'lateral'} aria-label="Etapas do estudo">
      <div className="lateral-inicio">
        <button className={!ativa && vista === 'percurso' ? 'nav-geral ativo' : 'nav-geral'} onClick={() => navegar(null)}>Visão geral</button>
        <button className={!ativa && vista === 'sintese' ? 'nav-geral ativo' : 'nav-geral'} onClick={() => navegar(null, 'experimento', 'sintese')}>Resultados e conclusões</button>
        <button className={!ativa && vista === 'metodo' ? 'nav-geral ativo' : 'nav-geral'} onClick={() => navegar(null, 'experimento', 'metodo')}>Como avaliamos</button>
      </div>
      <nav className="lista-etapas">{gruposFases.map(g => <div className="grupo-lateral" key={g.nome}><h2>{g.nome}</h2>{fases.slice(g.inicio, g.fim).map((f, j) => { const i = g.inicio + j; return <button key={f.id} className={f.id === fase?.id ? 'item-etapa atual' : 'item-etapa'} aria-current={f.id === fase?.id ? 'step' : undefined} onClick={() => navegar(f.id, aba)}><span className="indice-lateral">{String(i + 1).padStart(2, '0')}</span><span>{nomesFases[i]}</span></button>; })}</div>)}</nav>
      <div className="lateral-fim"><button className="nav-geral" onClick={() => navegar('outras-moedas')}>Ver estágio atual ↗</button><p>Registros consultados em<br />{new Date(evolucao.observadoEm).toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo', day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })} · Brasília</p></div>
    </aside>
    <PreferenciasFicha><main id="conteudo" className="conteudo">
      <div className="barra-contexto"><span>{etapa ? `Detalhe histórico · ${capitulos[etapa.capitulo].titulo}` : fase ? `Trajetória / fase ${indice + 1} de ${fases.length}` : vista === 'metodo' ? 'Como avaliamos' : vista === 'sintese' ? 'Resultados e conclusões' : 'Visão geral da pesquisa'}</span><span>CryptoCasting · 2026</span></div>
      <details className={`cenario-financeiro ${evolucao.custos?.situacao === 'divergente' ? 'cenario-pendente' : ''}`}><summary>{evolucao.custos?.situacao === 'vigente' ? 'Cenário financeiro · slippage provisório de 0,01% por lado' : evolucao.custos?.situacao === 'divergente' ? 'Cenário financeiro · integridade pendente' : 'Cenário histórico · slippage de 0,05% por lado'}</summary><p>Slippage é a diferença simulada entre o preço esperado e o executado. A releitura vigente ajusta esse custo, mantendo previsões, taxas, funding e filtros. As fontes originais permanecem históricas; 0,01% é uma hipótese provisória, não um custo real certificado. {typeof dados.custos_vigentes?.fonte === 'string' && <a href={`/api/panorama/fonte?caminho=${encodeURIComponent(dados.custos_vigentes.fonte)}`} target="_blank" rel="noreferrer">Cenário e evidências ↗</a>}</p></details>
      {fase ? <DetalheFase fase={fase} dados={evolucao} fichas={fichas} navegar={navegar} aba={aba} /> : etapa ? <>
        <button className="link-discreto voltar-trajetoria" onClick={() => navegar('receitas-ohlcv')}>← Voltar à fase de entradas e treinamento</button>
        <div className="cabecalho-etapa">
          <div className="etapa-marcadores"><span className="eyebrow">{etapa.categoria}</span><time>{etapa.data}</time></div>
          <h1>{etapa.titulo}</h1><p className="pergunta-etapa">{etapa.pergunta}</p>
          <div className="etapa-meta"><span>{etapa.contagem}</span><button className="link-discreto" onClick={copiar}>{copiado ? 'Link copiado' : 'Copiar link'}</button></div>
          {avisoCopia && <p role="status">{avisoCopia}</p>}
        </div>
        <nav className="abas" aria-label="Seções da etapa">{abasVisiveis.map(([id, nome]) => <button key={id} aria-current={abaAtual === id ? 'page' : undefined} onClick={() => navegar(etapa.id, id)}>{nome}</button>)}</nav>
        <div key={`${etapa.id}/${abaAtual}`} className="entrada-conteudo">
          {abaAtual === 'experimento' ? <Experimento etapa={etapa} fichas={fichas} navegar={navegar} /> : abaAtual === 'configuracao' ? <FichaTecnica key={etapa.id} pagina={etapa.id} catalogo={fichas} /> : abaAtual === 'resultados' ? <><AvisoFonte etapa={etapa} dados={dados} disponibilidade={disponibilidade} /><Resultados etapa={etapa} dados={dados} /></> : abaAtual === 'previsoes' ? <Previsoes etapa={etapa} dados={dados} /> : <Evidencias etapa={etapa} dados={dados} disponibilidade={disponibilidade} />}
        </div>
      </> : vista === 'metodo' ? <Metodo /> : vista === 'sintese' ? <Conclusoes dados={evolucao} navegar={navegar} /> : <VisaoPesquisa dados={evolucao} navegar={navegar} />}
      {ativa && <div className="navegacao-etapas"><button disabled={indice === 0} onClick={() => navegar(sequencia[indice - 1].id, aba)}><span>← Anterior</span><b>{sequencia[indice - 1]?.titulo ?? 'Início'}</b></button><small>{indice + 1} / {sequencia.length}{apresentacao && <span>← → para navegar · Esc para sair</span>}</small><button onClick={() => indice < sequencia.length - 1 ? navegar(sequencia[indice + 1].id, aba) : navegar(null, 'experimento', 'sintese')}><span>{indice < sequencia.length - 1 ? 'Próxima →' : 'Conclusões →'}</span><b>{sequencia[indice + 1]?.titulo ?? 'Resultados da pesquisa'}</b></button></div>}
      <footer className="rodape"><p>Resultados retrospectivos. Erro de previsão e retorno financeiro são avaliados separadamente.</p><span>TCC · 2026</span></footer>
    </main></PreferenciasFicha>
  </div>;
}

function Experimento({ etapa, fichas, navegar }: { etapa: Etapa; fichas: CatalogoFichas; navegar: Navegar }) {
  return <>
    <div className="resumo-narrativo"><section className="mudanca-etapa"><span className="rotulo-secao">O QUE TESTAMOS</span><h2>Mudança deste teste</h2><p>{etapa.mudanca}</p></section><section className="conclusao-etapa"><span className="rotulo-secao">O QUE APRENDEMOS</span><h2>{etapa.resultado}</h2><p>{etapa.conclusao}</p></section></div>
    <EssenciaisFase pagina={etapa.id} catalogo={fichas} />
    <p className="limite-discreto"><strong>Limite da conclusão.</strong> {etapa.limite}</p>
    <div className="acoes-resumo"><button onClick={() => navegar(etapa.id, 'configuracao')}>Comparar configuração <span>→</span></button>{etapa.publicacao && <button onClick={() => navegar(etapa.id, 'resultados')}>Ver métricas e comparação <span>→</span></button>}</div>
    {etapa.visual === 'entradas' && <details><summary>Entender as representações comparadas</summary><Representacoes /></details>}
    {(etapa.visual === 'blocos' || etapa.visual === 'entradas') && <details className="detalhes-metodo"><summary>Divisões de treino, validação e teste</summary><Metodo compacto /></details>}
    <details className="interpretacao"><summary>Interpretação do resultado</summary><p>{etapa.leitura}</p></details>
    {etapa.exemplos && <button className="botao secundario" onClick={() => navegar(etapa.id, 'previsoes')}>Ver previsões salvas →</button>}
  </>;
}

function Representacoes() {
  const [id, setId] = useState(0);
  const receitas = [
    { letra: 'A', nome: 'Relativa', resumo: 'Transformada e padronizada', preco: 'ln(O / C anterior) · ln(H / C anterior) · ln(L / C anterior) · ln(C / C anterior)', volume: 'ln(1 + volume em BTC)', explicacao: 'Remove o nível nominal do preço e comprime o volume. Cada canal é padronizado com a média e o desvio do treino.' },
    { letra: 'B', nome: 'Crua', resumo: 'Valores originais', preco: 'O · H · L · C, em USDT', volume: 'Volume em BTC, sem transformação', explicacao: 'Recebe os níveis originais, sem normalização da entrada. O alvo continua sendo log-retorno padronizado.' },
    { letra: 'C', nome: 'Níveis padronizados', resumo: 'Níveis com escala ajustada', preco: '(O − média de O) / desvio de O · o mesmo para H/L/C', volume: '(V − média de V) / desvio de V', explicacao: 'Padroniza cada canal somente com dados de treino. B versus C isola essa padronização; A versus B também muda a representação.' },
  ];
  const r = receitas[id];
  return <section className="painel representacoes"><h2>Representações comparadas</h2><div className="opcoes-representacao">{receitas.map((v, i) => <button key={v.letra} aria-pressed={id === i} onClick={() => setId(i)}><b>{v.letra}</b><span>{v.nome}<small>{v.resumo}</small></span></button>)}</div><div className="receita"><div><small>Preço</small><p>{r.preco}</p></div><div><small>Volume</small><p>{r.volume}</p></div></div><p className="descricao-painel">{r.explicacao}</p></section>;
}

function AvisoFonte({ etapa, dados, disponibilidade }: { etapa: Etapa; dados: DadosPanorama; disponibilidade: Disponibilidade }) {
  const p = etapa.publicacao ? String(dados.publicacoes[etapa.publicacao].fonte) : null;
  return p && disponibilidade[p] !== 'conferida' ? <div className="aviso">A fonte original está {disponibilidade[p] === 'ausente' ? 'ausente nesta máquina' : 'diferente da exportação'}. Os valores abaixo pertencem à exportação de 03/11/2026; confira a fonte antes de apresentar.</div> : null;
}
function Evidencias({ etapa, dados, disponibilidade }: { etapa: Etapa; dados: DadosPanorama; disponibilidade: Disponibilidade }) {
  const fontes = [...new Set([...etapa.fontes, ...(etapa.publicacao ? [String(dados.publicacoes[etapa.publicacao].fonte)] : [])])];
  return <section className="painel"><h2>Fontes da etapa</h2><p className="descricao-painel">Relatórios e resultados originais. A integridade dos arquivos é conferida antes da abertura.</p><div className="lista-fontes">{fontes.map((f, i) => <article key={f}><span className="icone-fonte">{f.endsWith('.md') ? 'TXT' : 'JSON'}</span><div><h3>{i === 0 ? 'Relatório da etapa' : f.endsWith('resultados.json') ? 'Resultados estruturados' : 'Documento de referência'}</h3><p>{f}</p><small>{disponibilidade[f] === 'conferida' ? 'Disponível e conferido' : disponibilidade[f] === 'ausente' ? 'Indisponível nesta máquina' : 'Integridade a reconferir'}</small></div><a className="botao pequeno secundario" target="_blank" rel="noreferrer" href={`/api/panorama/fonte?caminho=${encodeURIComponent(f)}`}>Abrir ↗</a></article>)}</div><details><summary>Identidade dos arquivos</summary><p>Exportação: {new Date(dados.gerado_utc).toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo' })} · Brasília.</p>{fontes.map(f => <div className="hash-fonte" key={f}><b>{f}</b><code>{dados.fontes[f]}</code></div>)}</details></section>;
}

