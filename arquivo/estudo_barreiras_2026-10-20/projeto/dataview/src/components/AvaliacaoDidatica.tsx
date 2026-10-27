"use client";
import { useState } from "react";
import { numero, percentual } from "@/lib/didatica";
import { classesEventos } from "@/lib/exploracao";

export function LaboratorioClassificacao() {
  const [taxas, setTaxas] = useState([0, 100, 0]);
  const [modo, setModo] = useState("expiracao");
  const [celula, setCelula] = useState([1, 1]);
  const suporte = [20, 60, 20];
  const matriz = suporte.map((n, i) => {
    const certos = Math.round(n * taxas[i] / 100), resto = n - certos;
    const linha = [0, 0, 0]; linha[i] = certos;
    if (modo === "expiracao" && i !== 1) linha[1] = resto;
    else { linha[(i + 1) % 3] = Math.floor(resto / 2); linha[(i + 2) % 3] = resto - Math.floor(resto / 2); }
    return linha;
  });
  const recall = matriz.map((r, i) => r[i] / suporte[i]);
  const acuracia = matriz.reduce((s, r, i) => s + r[i], 0) / 100;
  const balanceada = recall.reduce((a, b) => a + b, 0) / 3;
  const previstos = matriz.reduce((s, r) => s + r[celula[1]], 0);
  return <div className="laboratorio"><span className="selo exemplo">EXEMPLO DIDÁTICO · 100 CASOS FICTÍCIOS</span><h3>Acertar a classe frequente não basta</h3><p>Neste exemplo, existem 20 inferiores, 60 expirações e 20 superiores. Compare uma resposta constante com um modelo que reconhece as três classes.</p><div className="botoes"><button aria-pressed={modo === "expiracao"} onClick={() => { setModo("expiracao"); setTaxas([0, 100, 0]); }}>Sempre prevê expiração</button><button aria-pressed={modo === "equilibrado"} onClick={() => { setModo("equilibrado"); setTaxas([60, 60, 60]); }}>Reconhece 60% de cada classe</button></div><div className="controles">{classesEventos.map((c, i) => <label key={c}>Recall de {c.toLowerCase()}: {taxas[i]}%<input type="range" min="0" max="100" step="5" value={taxas[i]} onChange={e => { setModo("personalizado"); setTaxas(taxas.map((v, j) => j === i ? Number(e.target.value) : v)); }}/></label>)}</div><div className="placares"><div><small>Acurácia comum</small><strong>{percentual(acuracia)}</strong><span>Acertos ÷ 100 observações</span></div><div><small>Acerto balanceado</small><strong>{percentual(balanceada)}</strong><span>Média dos três recalls</span></div></div><div className="tabela"><table><caption>Matriz de confusão: clique em uma contagem · linhas = real; colunas = previsão</caption><thead><tr><th>Real ↓ / Previsto →</th>{classesEventos.map(c => <th key={c}>{c}</th>)}</tr></thead><tbody>{matriz.map((r, i) => <tr key={i}><th>{classesEventos[i]}<small> · {suporte[i]} casos reais</small></th>{r.map((n, j) => <td key={j} className={i === j ? "diagonal" : ""}><button aria-pressed={celula[0] === i && celula[1] === j} aria-label={`${n} casos reais de ${classesEventos[i]} previstos como ${classesEventos[j]}`} onClick={() => setCelula([i, j])}>{n}</button></td>)}</tr>)}</tbody></table></div><p className="resposta" aria-live="polite">{matriz[celula[0]][celula[1]]} casos eram <b>{classesEventos[celula[0]].toLowerCase()}</b>, mas receberam a classe <b>{classesEventos[celula[1]].toLowerCase()}</b>. {celula[0] === celula[1] ? "São acertos, na diagonal." : "São confusões entre classes."} A precisão dos anúncios de {classesEventos[celula[1]].toLowerCase()} é {previstos ? percentual(matriz[celula[1]][celula[1]] / previstos) : "indisponível: nenhum anúncio dessa classe"}.</p><p className="legenda">Nos ajustes manuais, os erros são divididos entre as outras duas classes. É uma construção para ensino, não um resultado dos modelos.</p></div>;
}

export function LaboratorioCalibracao() {
  const [anunciado, setAnunciado] = useState(70), [observado, setObservado] = useState(40);
  return <div className="laboratorio"><span className="selo exemplo">EXEMPLO DIDÁTICO · GRUPO DE 100 PREVISÕES</span><h3>Quando o modelo diz 70%, acontece aproximadamente 70% das vezes?</h3><div className="controles dois"><label>Probabilidade anunciada de superior: {anunciado}%<input type="range" min="10" max="90" step="5" value={anunciado} onChange={e => setAnunciado(Number(e.target.value))}/></label><label>Frequência real de superior no grupo: {observado}%<input type="range" min="0" max="100" step="5" value={observado} onChange={e => setObservado(Number(e.target.value))}/></label></div><div className="probabilidades"><div><div className="linha-valores"><span>Probabilidade anunciada</span><b>{anunciado}%</b></div><div className="trilho"><span style={{ width: `${anunciado}%`, background: "var(--azul)" }}/></div></div><div><div className="linha-valores"><span>Frequência observada</span><b>{observado}%</b></div><div className="trilho"><span style={{ width: `${observado}%`, background: "var(--verde)" }}/></div></div></div><p className="resposta" aria-live="polite">{anunciado === observado ? "A frequência coincide com a probabilidade anunciada neste grupo." : anunciado > observado ? `O modelo superestimou superior em ${anunciado - observado} pontos percentuais neste grupo.` : `O modelo subestimou superior em ${observado - anunciado} pontos percentuais neste grupo.`}</p><p className="legenda">Um grupo pequeno pode divergir por acaso. Calibração requer amostra suficiente, análise por faixas e incerteza; uma correspondência agregada não prova calibração em todas as situações.</p></div>;
}

export function ExemploCustoAcerto() {
  const [acertos, setAcertos] = useState(55), [custo, setCusto] = useState(12);
  const saldo = acertos * 100 - (100 - acertos) * 100 - 100 * custo;
  return <div className="laboratorio"><span className="selo exemplo">EXEMPLO DIDÁTICO · SEM EXPIRAÇÕES</span><h3>Uma taxa de acerto maior que 50% pode dar prejuízo</h3><p>100 operações hipotéticas: ganho bruto de 100 USDT em cada acerto, perda bruta de 100 USDT em cada erro. Sem reinvestimento ou alavancagem.</p><div className="controles dois"><label>Operações vencedoras: {acertos} de 100<input type="range" min="0" max="100" value={acertos} onChange={e => setAcertos(Number(e.target.value))}/></label><label>Custo total por operação: {custo} USDT<input type="range" min="0" max="30" value={custo} onChange={e => setCusto(Number(e.target.value))}/></label></div><p className="resposta" aria-live="polite">Resultado líquido: <b>{numero(saldo, 2)} USDT</b>. Ganhos ({numero(acertos * 100, 0)}) − perdas ({numero((100 - acertos) * 100, 0)}) − custos ({numero(100 * custo, 0)}).</p><p className="legenda">Custos hipotéticos para demonstrar a conta; não representam tarifas de futuros nem uma estratégia executada.</p></div>;
}
