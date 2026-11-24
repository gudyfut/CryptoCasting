'use client';
import { useState } from 'react';
import { fases, etapas } from '@/lib/etapas';
import type { EvolucaoPesquisa, FasePesquisa, ResultadoDiario, CatalogoFichas } from '@/lib/panorama-tipos';
import FichaTecnica, { EssenciaisFase } from './FichaTecnica';

type Navegar = (id: string | null, aba?: string, vista?: string) => void;
const percentual = (n: number | null | undefined, sinal = false) => n === null || n === undefined ? '—' : `${sinal && n > 0 ? '+' : ''}${(n * 100).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%`;
const periodo = (r: ResultadoDiario, ano = 2025) => r.periodos.find(p => p.ano === ano);
const linkFonte = (fonte: string) => `/api/panorama/fonte?caminho=${encodeURIComponent(fonte)}`;

function Fonte({ resultado }: { resultado: ResultadoDiario }) {
  return resultado.situacao === 'conferido' ? <div className="links-resultado">{resultado.fonteOperacional && <a target="_blank" rel="noreferrer" href={linkFonte(resultado.fonteOperacional)}>Avaliação financeira vigente ↗</a>}<a target="_blank" rel="noreferrer" href={linkFonte(resultado.fonte)}>Publicação original ↗</a></div> : <p className="aviso">{resultado.situacao === 'divergente' ? 'Integridade pendente; os números não são exibidos.' : 'Publicação indisponível nesta máquina.'}</p>;
}

export function EstadoAtual({ dados, compacto = false }: { dados: EvolucaoPesquisa; compacto?: boolean }) {
  const conferido = dados.fechamento.situacao === 'conferido';
  return <section className="estado-final" aria-labelledby="titulo-atual">
    <div className="estado-final-topo"><span className="eyebrow">ÚLTIMA ETAPA · 10 NOV 2026</span><span className="selo-concluido">{conferido ? 'Concluído e conferido' : 'Fechamento a conferir'}</span></div>
    <h2 id="titulo-atual">A mesma receita em ETH, BNB e XRP</h2>
    <p>ETH mostrou ganho médio com risco elevado. BNB e XRP tiveram perda média em 2025. A receita ainda não demonstrou estabilidade entre moedas.</p>
    {conferido && <div className="escopo-final"><span><b>{dados.fechamento.ajustes}</b> treinos novos</span><span><b>{dados.fechamento.controles}</b> controles exatos</span><span><b>{dados.fechamento.carteiras}</b> carteiras conferidas</span><span>BTC herdado · sem retreino</span></div>}
    <ResultadosMoedas dados={dados} compacto={compacto} />
    {!conferido && <p className="aviso">As publicações individuais não substituem a conferência conjunta. Consulte as fontes do fechamento.</p>}
  </section>;
}

function ResultadosMoedas({ dados, compacto = false }: { dados: EvolucaoPesquisa; compacto?: boolean }) {
  const [ano, setAno] = useState(2025);
  const [ensemble, setEnsemble] = useState(false);
  const resultados = compacto ? dados.moedas : [dados.receitas.find(r => r.id === 'padronizado')!, ...dados.moedas];
  return <div className="resultados-moedas">
    {!compacto && <div className="controles-resultados"><label>Período<select value={ano} onChange={e => setAno(Number(e.target.value))}><option value={2025}>2025 · teste retrospectivo</option><option value={2024}>2024 · validação</option></select></label><div className="segmentado" role="group" aria-label="Como resumir as carteiras"><button aria-pressed={!ensemble} onClick={() => setEnsemble(false)}>Média das 3 seeds</button><button aria-pressed={ensemble} onClick={() => setEnsemble(true)}>Ensemble</button></div></div>}
    <div className="tabela-rolavel"><table className="tabela-final"><caption>{ano} · {ano === 2024 ? 'validação que selecionou checkpoints' : 'teste retrospectivo'} · {ensemble ? 'carteira de previsões combinadas' : 'média de três carteiras independentes'}</caption><thead><tr><th scope="col">Moeda</th><th scope="col">Retorno líquido</th><th scope="col">Maior queda{!ensemble ? ' média' : ''}</th>{!compacto && <th scope="col">{ensemble ? 'Operações' : 'Seeds com ganho'}</th>}</tr></thead><tbody>{resultados.map(r => {
      const p = periodo(r, ano);
      const retorno = ensemble ? p?.ensemble?.retorno : p?.retorno;
      const queda = ensemble ? p?.ensemble?.queda : p?.queda;
      return <tr key={r.id}><th scope="row">{r.moeda}{r.moeda === 'BTC' && <small>referência herdada</small>}</th><td className={retorno == null ? '' : retorno > 0 ? 'ganho' : retorno < 0 ? 'perda' : ''}>{percentual(retorno, true)}</td><td>{percentual(queda)}</td>{!compacto && <td>{!p ? '—' : ensemble ? p.ensemble?.operacoes ?? '—' : `${p.seeds.filter(s => s.retorno > 0).length} de 3`}</td>}</tr>;
    })}</tbody></table></div>
    <p className="nota-resultados">{ensemble ? 'Ensemble combina previsões antes de operar. Seu resultado pode ser diferente da média das carteiras.' : 'Seeds são três inicializações do treino. A queda é a média da maior perda desde um pico em cada carteira.'}</p>
    {!compacto && <>
      <div className="leitura-moedas"><strong>Como interpretar</strong><p>{ano === 2025 ? 'ETH: as três seeds ganharam, com quedas próximas de metade da carteira. BNB: as três perderam. XRP: duas perderam e uma ficou em caixa; seu ensemble ganhou, mas também sofreu queda elevada.' : 'O bom resultado médio de 2024 em todas as moedas não se repetiu em 2025. A validação foi usada na seleção; não é confirmação independente.'}</p></div>
      <details className="detalhes-resultados"><summary>Ver cada seed e o ensemble · {ano}</summary><div className="tabela-rolavel"><table><thead><tr><th scope="col">Moeda</th><th scope="col">Carteira</th><th scope="col">Retorno líquido</th><th scope="col">Maior queda</th></tr></thead><tbody>{resultados.flatMap(r => {
        const p = periodo(r, ano);
        return [...(p?.seeds ?? []).map(s => <tr key={`${r.id}-${s.seed}`}><th scope="row">{r.moeda}</th><td>Seed {s.seed}{r.id === 'xrp' && ano === 2025 && s.seed === '17' ? ' · caixa' : ''}</td><td>{percentual(s.retorno, true)}</td><td>{percentual(s.queda)}</td></tr>), ...(p?.ensemble ? [<tr className="linha-ensemble" key={`${r.id}-ensemble`}><th scope="row">{r.moeda}</th><td>Ensemble</td><td>{percentual(p.ensemble.retorno, true)}</td><td>{percentual(p.ensemble.queda)}</td></tr>] : [])];
      })}</tbody></table></div></details>
      <details className="detalhes-resultados"><summary>Ver o erro de previsão em relação ao Naive</summary><p>Diferença percentual do erro quadrático do retorno. Negativo indica erro menor que o Naive; positivo indica erro maior. Não mede lucro nem compara erros absolutos de moedas diferentes.</p><div className="tabela-rolavel"><table><thead><tr><th scope="col">Moeda</th><th scope="col">2024</th><th scope="col">2025</th></tr></thead><tbody>{resultados.map(r => <tr key={r.id}><th scope="row">{r.moeda}</th><td>{percentual(periodo(r, 2024)?.diferencaNaive, true)}</td><td>{percentual(periodo(r)?.diferencaNaive, true)}</td></tr>)}</tbody></table></div></details>
    </>}
  </div>;
}

export function VisaoPesquisa({ dados, navegar }: { dados: EvolucaoPesquisa; navegar: Navegar }) {
  return <div className="visao-pesquisa">
    <header className="abertura-pesquisa"><span className="eyebrow">CRYPTOCASTING · TRAJETÓRIA DA PESQUISA</span><h1>O que testamos.<br />O que aprendemos.</h1><p>Do primeiro Mamba aos testes em quatro moedas. Acompanhe as mudanças, as conclusões e o que ainda falta demonstrar.</p></header>
    <EstadoAtual dados={dados} compacto />
    <button className="abrir-resultados-finais" onClick={() => navegar('outras-moedas', 'resultados')}>Explorar os resultados finais <span aria-hidden="true">→</span></button>
    <div className="guia-pesquisa"><strong>Qual é a referência atual?</strong><p>Mamba diário com entradas padronizadas, pelo menor erro entre as receitas diárias em BTC. Isso ainda não comprova lucro estável.</p><button className="link-discreto" onClick={() => navegar(null, 'experimento', 'sintese')}>Ver conclusões →</button></div>
    <section className="trajetoria-pesquisa" aria-labelledby="titulo-trajetoria"><div className="titulo-trajetoria"><div><span className="eyebrow">OUTUBRO → NOVEMBRO DE 2026</span><h2 id="titulo-trajetoria">Uma pergunta por fase</h2></div><span>10 fases · em ordem cronológica</span></div><ol>{fases.map((f, i) => <li key={f.id}><button onClick={() => navegar(f.id)} className="linha-fase"><span className="numero-fase">{String(i + 1).padStart(2, '0')}</span><span className="texto-fase"><time>{f.data}</time><strong>{f.titulo}</strong><span>{f.resultado}</span></span><span className="seta-fase" aria-hidden="true">→</span></button></li>)}</ol></section>
  </div>;
}

function ResultadoReceita({ resultado }: { resultado: ResultadoDiario }) {
  if (resultado.situacao !== 'conferido') return <Fonte resultado={resultado} />;
  return <section className="resultado-receita"><h2>Resultado da receita · BTC</h2><p className="descricao-secao">Média de três carteiras independentes, com os custos do cenário identificado no topo.</p><div className="tabela-rolavel"><table><thead><tr><th scope="col">Período</th><th scope="col">Erro de preço · RMSE</th><th scope="col">Retorno líquido</th><th scope="col">Maior queda média</th></tr></thead><tbody>{resultado.periodos.map(p => <tr key={p.ano}><th scope="row">{p.ano}<small>{p.ano === 2024 ? 'validação' : 'teste retrospectivo'}</small></th><td>{p.erroPreco?.toLocaleString('pt-BR', { maximumFractionDigits: 2, minimumFractionDigits: 2 }) ?? '—'} USDT</td><td className={(p.retorno ?? 0) > 0 ? 'ganho' : 'perda'}>{percentual(p.retorno, true)}</td><td>{percentual(p.queda)}</td></tr>)}</tbody></table></div><p className="nota-resultados">Menor RMSE significa menor erro, sem garantir lucro. 2024 selecionou checkpoints; 2025 já havia sido consultado.</p>
    <details className="detalhes-resultados"><summary>Ver cada seed e o ensemble · 2025</summary><div className="tabela-rolavel"><table><thead><tr><th scope="col">Carteira</th><th scope="col">Retorno líquido</th><th scope="col">Maior queda</th></tr></thead><tbody>{periodo(resultado)?.seeds.map(s => <tr key={s.seed}><th scope="row">Seed {s.seed}</th><td>{percentual(s.retorno, true)}</td><td>{percentual(s.queda)}</td></tr>)}{periodo(resultado)?.ensemble && <tr className="linha-ensemble"><th scope="row">Ensemble</th><td>{percentual(periodo(resultado)!.ensemble!.retorno, true)}</td><td>{percentual(periodo(resultado)!.ensemble!.queda)}</td></tr>}</tbody></table></div><p>Ensemble combina previsões antes da decisão de operar. Não equivale à média das carteiras.</p></details><Fonte resultado={resultado} />
  </section>;
}

export function DetalheFase({ fase, dados, fichas, navegar, aba = 'experimento' }: { fase: FasePesquisa; dados: EvolucaoPesquisa; fichas: CatalogoFichas; navegar: Navegar; aba?: string }) {
  const r = dados.receitas.find(r => r.id === fase.receita);
  const temResultados = Boolean(r) || fase.id === 'outras-moedas';
  const secoes = [['experimento', 'Resumo'], ['configuracao', 'Configuração'], ...(temResultados ? [['resultados', 'Resultados']] : []), ['fontes', 'Fontes']];
  const atual = secoes.some(([id]) => id === aba) ? aba : 'experimento';
  return <div className="detalhe-fase"><header className="cabecalho-etapa"><div className="etapa-marcadores"><span className="eyebrow">FASE {String(fases.indexOf(fase) + 1).padStart(2, '0')} / {fases.length}</span><time>{fase.data} 2026</time></div><h1>{fase.titulo}</h1><p className="pergunta-etapa">{fase.pergunta}</p></header>
    <nav className="abas" aria-label="Seções da etapa">{secoes.map(([id, nome]) => <button key={id} aria-current={atual === id ? 'page' : undefined} onClick={() => navegar(fase.id, id)}>{nome}</button>)}</nav>
    <div className="conteudo-etapa" key={fase.id + atual}>
      {atual === 'experimento' && <><div className="resumo-narrativo"><section className="mudanca-etapa"><span className="rotulo-secao">O QUE TESTAMOS</span><h2>Mudança desta fase</h2><p>{fase.mudanca}</p></section><section className="conclusao-etapa"><span className="rotulo-secao">O QUE APRENDEMOS</span><h2>{fase.resultado}</h2><p>{fase.conclusao}</p></section></div>{fase.id === 'outras-moedas' ? <div className="previa-resultados"><ResultadosMoedas dados={dados} compacto /></div> : <EssenciaisFase pagina={fase.id} catalogo={fichas} />}<p className="limite-discreto"><strong>Limite da conclusão.</strong> {fase.limite}</p><div className="acoes-resumo"><button onClick={() => navegar(fase.id, 'configuracao')}>Comparar configuração <span>→</span></button>{temResultados && <button onClick={() => navegar(fase.id, 'resultados')}>Examinar os resultados <span>→</span></button>}</div>{fase.detalhes && <TestesHistoricos fase={fase} navegar={navegar} />}</>}
      {atual === 'configuracao' && <FichaTecnica pagina={fase.id} catalogo={fichas} />}
      {atual === 'resultados' && (r ? <ResultadoReceita resultado={r} /> : <EstadoAtual dados={dados} />)}
      {atual === 'fontes' && <section className="fontes-etapa"><h2>Evidências desta etapa</h2><p>Publicações e registros conferidos. Os arquivos originais preservam o cenário histórico de custos.</p>{fase.fontes?.map((f, i) => <a className="fonte-etapa" key={f} target="_blank" rel="noreferrer" href={linkFonte(f)}><span>{i + 1}</span><div><strong>{f.endsWith('.md') ? 'Relato e conclusões do estudo' : 'Registro científico'}</strong><small>{f}</small></div>↗</a>)}{r && <Fonte resultado={r} />}{fase.id === 'outras-moedas' && <>{dados.fechamento.situacao === 'conferido' ? <><a className="fonte-etapa" target="_blank" rel="noreferrer" href={linkFonte(dados.fechamento.fonte!)}>Fechamento conjunto · 9 treinos, 3 controles e 210 carteiras ↗</a><a className="fonte-etapa" target="_blank" rel="noreferrer" href={linkFonte(dados.fechamento.comparacao!)}>Conferência das quatro moedas ↗</a></> : <p className="aviso">Fechamento conjunto indisponível ou divergente.</p>}{dados.moedas.map(m => <div className="fontes-moeda" key={m.id}><h3>{m.moeda}</h3><Fonte resultado={m} /></div>)}</>}<details><summary>Configurações, técnicas e protocolos</summary><p>Os arquivos que definem cada receita estão em Configuração → Notas e arquivos da receita.</p><button className="link-discreto" onClick={() => navegar(fase.id, 'configuracao')}>Abrir configuração →</button></details></section>}
    </div>
  </div>;
}

function TestesHistoricos({ fase, navegar }: { fase: FasePesquisa; navegar: Navegar }) {
  return <details className="testes-historicos"><summary>Explorar os {fase.detalhes?.length} testes desta fase</summary><p>Abra um teste para ver a hipótese, sua receita e os gráficos preservados.</p><div className="atalhos-testes">{etapas.filter(e => fase.detalhes?.includes(e.id)).map(e => <button key={e.id} onClick={() => navegar(e.id)}>{e.curto}<span aria-hidden="true">→</span></button>)}</div></details>;
}

export function Conclusoes({ dados, navegar }: { dados: EvolucaoPesquisa; navegar: Navegar }) {
  const ensemble = periodo(dados.receitas.find(r => r.id === 'padronizado')!)?.ensemble;
  return <section className="sintese conclusoes-pesquisa"><span className="eyebrow">RESULTADOS E CONCLUSÕES</span><h1>Avançamos no diagnóstico.<br />A estabilidade ainda falta.</h1><p className="lede">Há resultados positivos, mas nenhum vencedor geral que reúna menor erro, lucro e risco controlado.</p><div className="achados"><article><h2>Melhor previsão</h2><p>Na comparação ampla original, LSTM superou Mamba. Na linha diária de BTC, o Mamba com entradas padronizadas teve o menor erro entre as quatro receitas. Em 2025, ficou 0,47% acima do Naive.</p><button className="link-discreto" onClick={() => navegar('padronizacao-diaria', 'resultados')}>Ver a referência diária →</button></article><article><h2>Melhor retorno depende do recorte</h2><p>A receita que prevê preço teve maior retorno médio em BTC em 2025. A receita padronizada teve média negativa, embora seu ensemble tenha rendido {percentual(ensemble?.retorno, true)} em apenas {ensemble?.operacoes ?? '24'} operações. Menor erro não significou maior lucro.</p></article></div>
    <section className="resultado-receita"><h2>A evolução diária em BTC</h2><div className="tabela-rolavel"><table><caption>2025 · mesmas origens · média de três carteiras independentes</caption><thead><tr><th scope="col">Receita</th><th scope="col">Erro de preço · RMSE</th><th scope="col">Retorno líquido</th><th scope="col">Maior queda média</th></tr></thead><tbody>{dados.receitas.map(r => { const p = periodo(r); return <tr key={r.id}><th scope="row">{r.nome}{r.id === 'padronizado' && <small>Referência de erro atual</small>}</th><td>{p?.erroPreco?.toLocaleString('pt-BR', { maximumFractionDigits: 2, minimumFractionDigits: 2 }) ?? '—'}{p ? ' USDT' : ''}</td><td>{percentual(p?.retorno, true)}</td><td>{percentual(p?.queda)}</td></tr>; })}</tbody></table></div></section>
    <div className="achados"><article><h2>O último teste de mecanismo</h2><p>Retirar a penalização reativou a contribuição dos ramos Mamba, mas aumentou o erro médio em 5,22% em 2025. A referência padronizada continua com colapso funcional documentado.</p><button className="link-discreto" onClick={() => navegar('sem-penalizacao')}>Entender a hipótese →</button></article><article><h2>O estágio atual</h2><p>Generalização para ETH, BNB e XRP concluída. ETH teve ganho médio; BNB e XRP tiveram perda média em 2025. O ensemble de XRP foi positivo, evidenciando a diferença entre combinar previsões e tirar a média de carteiras.</p><button className="link-discreto" onClick={() => navegar('outras-moedas', 'resultados')}>Ver os resultados finais →</button></article></div>
    <p className="limite-discreto"><strong>Próximo passo.</strong> Discutir uma nova hipótese com lucro, risco e estabilidade explícitos. Taxa menor continua apenas proposta. Esta rodada terminou; nenhum novo treinamento foi iniciado.</p><p className="nota-resultados">2024 e 2025 já foram consultados. As simulações são retrospectivas, com slippage provisório; não certificam lucro futuro nem custos históricos reais da Binance.</p>
  </section>;
}
