"use client";

import { useState } from "react";
import { limites, numero, percentual, perdas, prazo, operacaoIlustrativa } from "@/lib/didatica";

function Exemplo() { return <span className="selo exemplo">Exemplo didático · dados fictícios</span>; }
const classes = ["Inferior primeiro", "Prazo esgotado", "Superior primeiro"];

export function LaboratorioBarreiras() {
  const [horas, setHoras] = useState(24);
  const [sigma, setSigma] = useState(.3);
  const [cenario, setCenario] = useState("recuperacao");
  const b = limites(100, sigma / 100, horas);
  const trajetorias: Record<string, number[]> = {
    recuperacao: [0, .24, -.12, -.55, -1.2, -.7, -.2, .32, .6, .24, .3],
    superior: [0, -.22, .12, .5, .78, 1.2, .9, .7, 1.1, .9, 1.25],
    prazo: [0, .32, .55, .12, -.25, -.58, -.2, .22, .48, .25, .2],
  };
  const valores = trajetorias[cenario];
  const indice = valores.findIndex(v => Math.abs(v) >= 1);
  const toque = indice >= 0;
  const limite = toque ? Math.sign(valores[indice]) : 0;
  const fracao = toque ? (limite - valores[indice - 1]) / (valores[indice] - valores[indice - 1]) : 1;
  const tempo = toque ? (indice - 1 + fracao) / 10 : 1;
  const x = (t: number) => 65 + 580 * t;
  const y = (v: number) => 165 - v * 76;
  const pontos = valores.map((v, i) => `${x(i / 10)},${y(v)}`).join(" ");
  const antes = toque ? [...valores.slice(0, indice).map((v, i) => `${x(i / 10)},${y(v)}`), `${x(tempo)},${y(limite)}`].join(" ") : pontos;
  const desfecho = toque ? (limite < 0 ? 0 : 2) : 1;
  return <div className="laboratorio">
    <Exemplo/><h3>O caminho muda a resposta</h3>
    <div className="controles">
      <label>Prazo máximo<select value={horas} onChange={e => setHoras(Number(e.target.value))}>{[1, 24, 168].map(h => <option key={h} value={h}>{prazo(h)}</option>)}</select></label>
      <label>Caminho ilustrado<select value={cenario} onChange={e => setCenario(e.target.value)}><option value="recuperacao">Cai, sai no stop e depois recupera</option><option value="superior">Atinge o limite superior</option><option value="prazo">Permanece entre os limites</option></select></label>
      <label>Volatilidade horária: {numero(sigma, 1)}%<input type="range" min="0.1" max="1" step="0.1" value={sigma} onChange={e => setSigma(Number(e.target.value))}/></label>
    </div>
    <svg className="grafico-trajeto" viewBox="0 0 730 310" role="img" aria-label={`Trajetória fictícia: ${classes[desfecho]}. Preço inicial 100, limite superior ${numero(b.superior, 2)}, inferior ${numero(b.inferior, 2)}. Eixo vertical em log-preço.`}>
      <rect x="65" y="89" width="580" height="152" fill="#edf4f0"/>
      {[1, 0, -1].map(v => <g key={v}><line x1="65" x2="645" y1={y(v)} y2={y(v)} stroke={v === 1 ? "#147b68" : v === -1 ? "#ae493c" : "#b6c9c6"} strokeDasharray="5 5"/><text className="rotulo-preco" x="57" y={y(v) + 5} textAnchor="end">{numero(v === 1 ? b.superior : v === -1 ? b.inferior : 100, 2)}</text></g>)}
      <text x="72" y="77" fill="#116a59">Superior · +{percentual(b.superior / 100 - 1)}</text>
      <text x="72" y="262" fill="#9b3d32">Inferior · −{percentual(1 - b.inferior / 100)}</text>
      <line x1="645" x2="645" y1="42" y2="267" stroke="#586f7a" strokeDasharray="4 4"/>
      <polyline points={pontos} fill="none" stroke="#a1b2b4" strokeWidth="2" strokeDasharray="5 5"/>
      <polyline points={antes} fill="none" stroke="#153945" strokeWidth="3.5" strokeLinejoin="round"/>
      <circle cx={x(tempo)} cy={y(toque ? limite : valores[10])} r="6" fill={desfecho === 0 ? "#ae493c" : desfecho === 2 ? "#147b68" : "#77709b"}/>
      <text x="65" y="294">Entrada: 100 USDT</text><text x="645" y="294" textAnchor="end">Prazo: {prazo(horas)}</text>
    </svg>
    <div className="legenda-limites"><span>Inferior <b>{numero(b.inferior, 2)}</b></span><span>Entrada <b>100,00</b></span><span>Superior <b>{numero(b.superior, 2)}</b></span></div>
    <div className="resposta" aria-live="polite"><b>{classes[desfecho]}.</b> {desfecho === 0 ? "O preço termina acima da entrada, mas a operação já teria encerrado no limite inferior. Prever apenas a direção final esconderia isso." : desfecho === 2 ? "A operação encerra no primeiro toque superior. O restante do caminho não altera o rótulo." : "Sem toque, a operação encerra ao vencer o prazo. Isso pode produzir ganho ou perda; expiração não significa retorno zero."}</div>
    <p className="legenda">Linha sólida: até a saída. Tracejado: caminho posterior, sem posição aberta. Eixo vertical em log-preço. Ao mudar o prazo ou a volatilidade, reescalamos o mesmo desenho; isto não é uma previsão do mercado.</p>
  </div>;
}

export function LaboratorioMetricas() {
  const [probabilidades, setProbabilidades] = useState([.1, .1, .8]);
  const [classe, setClasse] = useState(2);
  const p = probabilidades[2], resto = 1 - p;
  const divisao = resto > 1e-10 ? probabilidades[0] / resto : .5;
  const erro = perdas(probabilidades, classe);
  const pReal = probabilidades[classe];
  // Evitar diferenças de últimos bits entre Math.log de Node e Chromium no SSR.
  const curva = Array.from({ length: 100 }, (_, i) => { const q = (i + 1) / 100; return `${(45 + q * 560).toFixed(3)},${(220 - (-Math.log(q) / 4.7) * 190).toFixed(3)}`; }).join(" ");
  return <div className="laboratorio">
    <Exemplo/><h3>Uma previsão, três probabilidades, um desfecho</h3>
    <div className="botoes" aria-label="Exemplos de probabilidades">
      <button onClick={() => { setClasse(2); setProbabilidades([.1, .1, .8]); }}>80% no desfecho que ocorreu</button>
      <button onClick={() => { setClasse(2); setProbabilidades([.8, .1, .1]); }}>Só 10% no que ocorreu</button>
      <button onClick={() => { setClasse(2); setProbabilidades([1 / 3, 1 / 3, 1 / 3]); }}>Probabilidades iguais</button>
    </div>
    <div className="duas-colunas">
      <div><label>Desfecho observado<select value={classe} onChange={e => setClasse(Number(e.target.value))}>{classes.map((c, i) => <option key={c} value={i}>{c}</option>)}</select></label>
        <label>Probabilidade de superior: {percentual(p, 1)}<input type="range" min="1" max="99" step="1" value={p * 100} onChange={e => { const q = Number(e.target.value) / 100; setProbabilidades([(1 - q) * divisao, (1 - q) * (1 - divisao), q]); }}/></label>
        <label>Parcela do restante atribuída a inferior: {percentual(divisao, 0)}<input type="range" min="1" max="99" step="1" value={divisao * 100} onChange={e => { const q = Number(e.target.value) / 100; setProbabilidades([resto * q, resto * (1 - q), p]); }}/></label>
        <div className="probabilidades">{probabilidades.map((v, i) => <div key={i}><div className="linha-valores"><span>{classes[i]} {classe === i ? "✓ ocorreu" : ""}</span><b>{percentual(v, 1)}</b></div><div className="trilho"><span style={{ width: `${v * 100}%`, background: i === classe ? "var(--verde)" : "#9daeb4" }}/></div></div>)}</div>
      </div>
      <div aria-live="polite"><div className="placares"><div><small>Log-loss · menor é melhor</small><strong>{numero(erro.logLoss)}</strong><span>−ln({numero(pReal)})</span></div><div><small>Brier · menor é melhor</small><strong>{numero(erro.brier)}</strong><span>Soma de 3 erros ao quadrado</span></div></div>
        <svg viewBox="0 0 660 265" role="img" aria-label="A log-loss cai à medida que aumenta a probabilidade atribuída ao desfecho real; cresce muito perto de zero.">
          {[0, 1, 2, 3, 4].map(v => <g key={v}><line x1="45" x2="605" y1={220 - v / 4.7 * 190} y2={220 - v / 4.7 * 190} stroke="#dde4e2"/><text x="32" y={225 - v / 4.7 * 190}>{v}</text></g>)}
          <polyline points={curva} fill="none" stroke="#153945" strokeWidth="3"/>
          <circle cx={(45 + pReal * 560).toFixed(3)} cy={(220 - Math.min(4.7, erro.logLoss) / 4.7 * 190).toFixed(3)} r="6" fill="#147b68"/>
          <text x="45" y="253">0%</text><text x="325" y="253" textAnchor="middle">Probabilidade do que ocorreu</text><text x="605" y="253" textAnchor="end">100%</text>
        </svg><p className="legenda">Curva de log-loss para um caso. Erros muito confiantes recebem penalidade alta. O ponto representa sua escolha; valores acima de 4,7 ficam no topo do desenho.</p>
      </div>
    </div>
    <details><summary>Ver o cálculo do Brier deste exemplo</summary><p>O desfecho real vira uma lista com 1 na classe observada e 0 nas outras. Aqui: [{classes.map((_, i) => Number(i === classe)).join("; ")}].</p><p className="formula">{probabilidades.map((v, i) => `(${numero(v)} − ${Number(i === classe)})²`).join(" + ")} = {numero(erro.brier)}</p><p>Usamos a soma das três classes, sem dividir por 2 ou por 3. Com probabilidades iguais, log-loss = 1,099 e Brier = 0,667.</p></details>
  </div>;
}

export function LaboratorioOperacao() {
  const [alta, setAlta] = useState(2), [p, setP] = useState(65);
  const [saida, setSaida] = useState<"superior" | "inferior" | "prazo">("inferior");
  const r = operacaoIlustrativa(alta / 100, p / 100, saida);
  return <div className="laboratorio"><Exemplo/><h3>Da probabilidade ao saldo: acompanhe uma operação</h3>
    <p>Capital inicial de 10.000 USDT, entrada bruta a 100 USDT. Suponha histórico disponível, calendário elegível e nenhuma posição aberta.</p>
    <div className="botoes"><button onClick={() => { setAlta(.4); setP(60); }}>Alvo estreito: custos impedem</button><button onClick={() => { setAlta(2); setP(55); }}>Probabilidade insuficiente</button><button onClick={() => { setAlta(2); setP(65); }}>Entrada permitida</button></div>
    <div className="controles">
      <label>Alta até a barreira: {numero(alta, 1)}%<input type="range" min="0.2" max="8" step="0.1" value={alta} onChange={e => setAlta(Number(e.target.value))}/></label>
      <label>Probabilidade superior: {p}%<input type="range" min="10" max="95" step="1" value={p} onChange={e => setP(Number(e.target.value))}/></label>
      <label>Saída hipotética<select value={saida} onChange={e => setSaida(e.target.value as typeof saida)}><option value="superior">Superior primeiro</option><option value="inferior">Inferior primeiro</option><option value="prazo">Prazo esgotado, pequena alta</option></select></label>
    </div>
    <div className="resposta" aria-live="polite"><b>{r.permitida ? "Entrada permitida." : "Permanece em caixa."}</b> Probabilidade ≥ 60%: {p >= 60 ? "sim" : "não"}. Viabilidade nominal positiva: {r.viabilidade > 0 ? "sim" : "não"} ({percentual(r.viabilidade)}).</div>
    <div className="placares tres"><div><small>Capital destinado à compra</small><strong>{numero(r.investido, 2)}</strong><span>USDT · {percentual(r.fracao)} do capital</span></div><div><small>Saldo após a saída</small><strong>{numero(r.saldo, 2)}</strong><span>USDT, incluindo caixa não investido</span></div><div><small>Retorno sobre o capital total</small><strong>{percentual(r.saldo / r.capital - 1)}</strong><span>{r.permitida ? "1 operação ilustrativa" : "0 operações"}</span></div></div>
    <p>Com estes limites, tocar o superior daria <b>{percentual(r.retornoSuperior)}</b> sobre o valor investido; tocar o inferior, <b>{percentual(r.retornoInferior)}</b>. Ambos já descontam os custos. A probabilidade não determina qual desses resultados ocorrerá.</p>
    <details><summary>Conferir cada etapa da conta</summary>
      <p>Limites brutos: {numero(r.superior, 4)} e {numero(r.inferior, 4)} USDT, simétricos em log-preço. Custo por lado: taxa de 0,10% e deslizamento de 0,05%.</p>
      <p className="formula">R(B) = (B / 100) × (0,9995 × 0,999) / (1,0005 × 1,001) − 1</p>
      <p>Viabilidade = p(superior) × R(superior) + [1 − p(superior)] × R(inferior). Todo desfecho que não seja superior é tratado nominalmente como stop neste filtro; ele não estima o retorno verdadeiro da expiração.</p>
      <p>Fração investida, se entrar = mínimo entre 100% e 1% ÷ perda nominal no stop. Quantidade comprada = {numero(r.investido, 4)} ÷ (100 × 1,0005 × 1,001) = {numero(r.quantidade, 6)} unidades.</p>
      <p>Preço bruto da saída ilustrada: {numero(r.precoSaida, 4)}. Recebimento após custos = quantidade × saída × 0,9995 × 0,999 = {numero(r.recebimento, 4)} USDT. Saldo final = caixa restante + recebimento.</p>
    </details>
    <p className="legenda">Calculadora de uma operação sem gaps. A simulação científica percorre os minutos reais e pode ter perda maior que o risco nominal de 1%. A saída hipotética não é usada para decidir a entrada.</p>
  </div>;
}
