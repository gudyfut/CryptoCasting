'use client';
import { createContext, useContext, useState, type ReactNode } from 'react';
import { compararFichas, valorResumido } from '@/lib/fichas';
import type { CatalogoFichas } from '@/lib/panorama-tipos';

type ModoComparacao = 'anterior' | 'referencia';
const categorias = [ ['entrada', 'Dados'], ['modelo', 'Rede'], ['treino', 'Treino'], ['avaliacao', 'Avaliação'], ['operacao', 'Operação'] ] as const;
const essenciais = new Set([
  'entrada.moedas', 'entrada.candle', 'entrada.contexto', 'entrada.canais', 'entrada.representacao', 'entrada.escala', 'entrada.alvo',
  'modelo.familias', 'modelo.estrutura', 'modelo.eixo', 'modelo.estado', 'modelo.convolucao', 'modelo.expansao', 'modelo.dropout', 'modelo.normalizacao',
  'treino.execucao', 'treino.otimizador', 'treino.taxa', 'treino.decay', 'treino.scheduler', 'treino.perda', 'treino.lote', 'treino.epocas',
  'avaliacao.calendario', 'avaliacao.selecao', 'avaliacao.seeds', 'avaliacao.controles', 'avaliacao.referencias',
  'operacao.lados', 'operacao.decisao', 'operacao.saida', 'operacao.filtro', 'operacao.capital', 'operacao.comissao', 'operacao.slippage', 'operacao.funding',
]);
const ContextoFicha = createContext<{
  comparacao: ModoComparacao; setComparacao: (modo: ModoComparacao) => void;
  grupo: string; setGrupo: (grupo: string) => void;
  soMudancas: boolean; setSoMudancas: (ativo: boolean) => void;
} | null>(null);

export function PreferenciasFicha({ children }: { children: ReactNode }) {
  const [comparacao, setComparacao] = useState<ModoComparacao>('anterior');
  const [grupo, setGrupo] = useState('entrada');
  const [soMudancas, setSoMudancas] = useState(false);
  return <ContextoFicha.Provider value={{ comparacao, setComparacao, grupo, setGrupo, soMudancas, setSoMudancas }}>{children}</ContextoFicha.Provider>;
}

export function EssenciaisFase({ pagina, catalogo }: { pagina: string; catalogo: CatalogoFichas }) {
  const ficha = catalogo.fichas[catalogo.padroes[pagina]];
  if (!ficha || ficha.integridade !== 'conferida') return null;
  const c = ficha.campos;
  const semTreino = c['treino.execucao']?.startsWith('Zero treino novo');
  const preparacao = ficha.id === 'desenho';
  const valor = (id: string) => valorResumido(id, c[id] ?? 'Consultar configuração');
  return <dl className="essenciais-fase" aria-label="Características principais">
    <div><dt>Entrada</dt><dd>{valor('entrada.candle')} · {c['entrada.contexto']}</dd><small>{valor('entrada.alvo')}</small></div>
    <div><dt>Modelo</dt><dd>{valor('modelo.estrutura')}</dd><small>{valor('modelo.eixo')}</small></div>
    <div><dt>Treinamento</dt><dd>{preparacao ? 'Preparação da receita' : semTreino ? 'Sem novo treinamento' : `${valor('treino.otimizador')} · taxa ${c['treino.taxa']}`}</dd><small>{preparacao ? 'Parâmetros planejados para a referência' : semTreino ? 'Pesos e previsões herdados' : `${valor('treino.perda')} · penalização ${c['treino.decay']}`}</small></div>
  </dl>;
}

function Valor({ id, valor }: { id: string; valor?: string }) {
  if (!valor) return <span className="valor-vazio">Não se aplica</span>;
  return <details className="valor-parametro"><summary title="Expandir definição completa">{valorResumido(id, valor)}</summary><p>{valor}</p></details>;
}

export default function FichaTecnica({ pagina, catalogo }: { pagina: string; catalogo: CatalogoFichas }) {
  const opcoes = (catalogo.paginas[pagina] ?? []).map(id => catalogo.fichas[id]).filter(Boolean);
  const [escolhida, setEscolhida] = useState(catalogo.padroes[pagina]);
  const [todos, setTodos] = useState(false);
  const preferencias = useContext(ContextoFicha);
  if (!preferencias) throw new Error('Ficha fora do contexto de preferências');
  const { comparacao, setComparacao, grupo, setGrupo, soMudancas, setSoMudancas } = preferencias;
  const ficha = catalogo.fichas[escolhida] ?? opcoes[0];
  if (!ficha) return <p className="aviso">Configuração indisponível nesta máquina.</p>;
  const anteriorId = comparacao === 'anterior' ? catalogo.anteriores[pagina] : ficha.referencia;
  const base = anteriorId ? catalogo.fichas[anteriorId] : null;
  const podeComparar = base?.integridade === 'conferida';
  const grupos = compararFichas(ficha, podeComparar ? base : null);
  const selecionado = grupos.find(g => g.id === grupo) ?? grupos[0];
  const mudou = (c: { alteracao: string }) => podeComparar && c.alteracao !== 'mantido';
  const campos = selecionado.campos.filter(c => (!soMudancas || !podeComparar || mudou(c)) && (todos || essenciais.has(c.id) || mudou(c)));
  const totalMudancas = podeComparar ? grupos.flatMap(g => g.campos).filter(mudou).length : 0;
  const gruposOpcoes = [...new Set(opcoes.map(f => f.grupo))];

  return <section className="configuracao-etapa" aria-labelledby={`titulo-ficha-${pagina}`}>
    <div className="configuracao-titulo"><div><h2 id={`titulo-ficha-${pagina}`}>Configuração da fase</h2><p>Uma categoria por vez. Expanda um valor para consultar a definição completa.</p></div><span className="legenda-alteracao"><i />{podeComparar ? `${totalMudancas} ${totalMudancas === 1 ? 'alteração' : 'alterações'}` : 'Configuração inicial'}</span></div>
    <div className="configuracao-selecao">
      {opcoes.length > 1 ? <label className="receita-ficha">Receita exibida<select value={ficha.id} onChange={e => setEscolhida(e.target.value)}>{gruposOpcoes.map(g => <optgroup key={g} label={g}>{opcoes.filter(f => f.grupo === g).map(f => <option key={f.id} value={f.id}>{f.nome}</option>)}</optgroup>)}</select></label> : <div className="nome-receita"><small>Receita exibida</small><strong>{ficha.nome}</strong></div>}
      <label>Comparar com<select aria-label="Base da comparação" value={comparacao} onChange={e => setComparacao(e.target.value as ModoComparacao)}><option value="anterior">Etapa anterior</option><option value="referencia">Referência do teste</option></select></label>
    </div>
    <p className="origem-comparacao">{base ? <>Base: <strong>{base.nome}</strong>.</> : 'Ponto de partida: não há uma receita anterior para comparar.'} {comparacao === 'anterior' && ficha.referencia && ficha.referencia !== base?.id && <button onClick={() => setComparacao('referencia')}>Ver a receita de origem →</button>}</p>
    {ficha.integridade !== 'conferida' ? <p className="aviso" role="status">Uma fonte está ausente ou divergente. Os parâmetros não são presumidos.</p> : <>
      <nav className="categorias-configuracao" aria-label="Categorias da configuração">{categorias.map(([id, nome]) => {
        const n = podeComparar ? grupos.find(g => g.id === id)!.campos.filter(mudou).length : 0;
        return <button key={id} aria-pressed={selecionado.id === id} onClick={() => setGrupo(id)}>{nome}{n > 0 && <span aria-label={`${n} alterações`}>{n}</span>}</button>;
      })}</nav>
      <div className="filtros-configuracao"><h3>{selecionado.nome}</h3><label><input type="checkbox" checked={Boolean(podeComparar && soMudancas)} disabled={!podeComparar} onChange={e => setSoMudancas(e.target.checked)} />Só alterações</label><label><input type="checkbox" checked={todos} onChange={e => setTodos(e.target.checked)} />Todos os parâmetros</label></div>
      {campos.length ? <div className="tabela-parametros"><table><thead><tr><th scope="col">Característica</th>{podeComparar && <th scope="col">Antes</th>}<th scope="col">Nesta receita</th></tr></thead><tbody>{campos.map(c => <tr key={c.id} className={mudou(c) ? 'parametro-alterado' : ''}><th scope="row">{c.nome}{mudou(c) && <small>Alterado</small>}</th>{podeComparar && <td className="parametro-antes"><Valor id={c.id} valor={c.antes} /></td>}<td><Valor id={c.id} valor={c.valor} /></td></tr>)}</tbody></table></div> : <p className="categoria-vazia">Nenhuma alteração nesta categoria. Escolha outra categoria ou desmarque “Só alterações”.</p>}
      <p className="rodape-configuracao">{campos.length} de {selecionado.campos.length} parâmetros nesta categoria. <span>O dourado identifica o que mudou em relação à base.</span></p>
    </>}
    <details className="fontes-configuracao"><summary>Notas e arquivos da receita</summary>{ficha.nota && <p>{ficha.nota}</p>}<p>Valores conferidos nas fontes. A apresentação financeira usa o cenário de custos indicado no topo; os arquivos originais preservam seus valores históricos.</p><ul>{ficha.fontes.map(f => <li key={f}><a target="_blank" rel="noreferrer" href={`/api/panorama/fonte?caminho=${encodeURIComponent(f)}`}>{f}</a></li>)}</ul></details>
  </section>;
}
