import type { TipoPrevisao } from "@/lib/tarefas-previsao";

export function MiniPrevisao({ tipo }: { tipo: TipoPrevisao }) {
  const descricoes = {
    direcao: "Exemplo fictício: preço de referência 100; alta termina acima e não alta termina em 100 ou abaixo.",
    retorno: "Exemplo fictício: de 100 para 103 equivale a retorno simples de mais 3 por cento.",
    intervalo: "Exemplo fictício: faixa entre os quantis 10 e 90 se amplia nos horizontes futuros; a mediana está no interior.",
    volatilidade: "Exemplo fictício: duas trajetórias chegam ao mesmo preço, mas uma oscila mais durante o período.",
    barreiras: "Exemplo fictício: a trajetória toca o limite inferior antes de terminar acima do preço inicial.",
  };
  return <svg viewBox="0 0 360 156" role="img" aria-label={descricoes[tipo]} className="mini-previsao">
    <rect x="112" y="12" width="234" height="116" rx="8" fill="#edf3f7" />
    <path d="M14 105 L33 97 L48 108 L65 85 L84 93 L112 78" fill="none" stroke="#798b9c" strokeWidth="2.5" />
    <path d="M112 14 V128 M14 78 H344" stroke="#a8b5c2" strokeDasharray="3 4" />
    <circle cx="112" cy="78" r="4" fill="#314e68" />
    <text x="112" y="148" textAnchor="middle">agora</text><text x="320" y="148" textAnchor="middle">futuro</text>
    {tipo === "direcao" && <><path d="M112 78 L300 35 M112 78 L300 111" stroke="#386a87" strokeWidth="2.5" fill="none" /><text x="252" y="27">alta ↗</text><text x="235" y="127">não alta ↘ / =</text></>}
    {tipo === "retorno" && <><path d="M112 78 L309 37" stroke="#257965" strokeWidth="3" strokeDasharray="5 4" /><circle cx="309" cy="37" r="5" fill="#257965" /><text x="263" y="25">103 (+3%)</text><text x="78" y="68">100</text></>}
    {tipo === "intervalo" && <><path d="M112 78 L170 62 L230 34 L320 17 L320 121 L230 109 L170 88 Z" fill="#cedfe9" /><path d="M112 78 L170 73 L230 64 L320 56" fill="none" stroke="#386a87" strokeWidth="2.5" strokeDasharray="5 3" /><text x="265" y="33">q90</text><text x="265" y="72">mediana</text><text x="265" y="115">q10</text></>}
    {tipo === "volatilidade" && <><path d="M112 78 L143 72 L170 82 L198 74 L230 84 L260 73 L312 78" fill="none" stroke="#879aa9" strokeWidth="2" /><path d="M112 78 L143 33 L170 114 L198 22 L230 116 L260 37 L312 78" fill="none" stroke="#97643e" strokeWidth="2.5" /><text x="162" y="15">oscila mais</text><text x="213" y="98">oscila menos</text></>}
    {tipo === "barreiras" && <><path d="M112 34 H334 M112 112 H334" stroke="#9b7150" strokeDasharray="5 3" /><path d="M315 16 V126" stroke="#667d93" strokeDasharray="3 4" /><path d="M112 78 L139 83 L169 112 L204 90 L238 70 L273 80 L315 55" fill="none" stroke="#386a87" strokeWidth="2.5" /><circle cx="169" cy="112" r="5" fill="#9b7150" /><text x="130" y="130">1º toque</text><text x="232" y="27">superior</text><text x="233" y="107">inferior</text></>}
  </svg>;
}

export function LinhaTemporal({ candle, contexto, horizonte, quantidade }: { candle: string; contexto: number; horizonte: string; quantidade: number }) {
  return <div className="linha-temporal">
    <div className="linha-legenda"><span>Passado observado</span><span>Momento da previsão</span><span>Período a prever</span></div>
    <svg viewBox="0 0 720 154" role="img" aria-label={`Contexto de ${contexto} dias, com ${quantidade} candles de ${candle}. Depois da origem, horizonte de ${horizonte}. Desenho esquemático, fora de escala.`}>
      <rect x="8" y="15" width="420" height="94" rx="8" fill="#e9f0f3" /><rect x="442" y="15" width="270" height="94" rx="8" fill="#f7efdf" />
      {Array.from({ length: 16 }, (_, i) => { const y = 76 - Math.sin(i * 1.5) * 13 - i * 1.3; const alta = i % 3 !== 0; return <g key={i} stroke={alta ? "#3d7b71" : "#a57662"} fill={alta ? "#3d7b71" : "#a57662"}><path d={`M${25 + i * 24} ${y - 19} v42`} /><rect x={20 + i * 24} y={y - 9} width="10" height="21" rx="1" /></g>; })}
      <path d="M435 6 V121" stroke="#344e63" strokeWidth="2" /><text x="578" y="62" textAnchor="middle" fontSize="24" fill="#8b6933">?</text>
      <path d="M18 124 H417 M452 124 H702" stroke="#7a8d9c" /><text x="214" y="147" textAnchor="middle">{contexto} dias · {quantidade.toLocaleString("pt-BR")} candles</text><text x="578" y="147" textAnchor="middle">{horizonte}</text>
    </svg>
    <p className="miudo">Candles ilustrativos · desenho fora de escala · futuro indisponível na entrada</p>
  </div>;
}
