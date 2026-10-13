"use client";
import { tarefasPrevisao, type TipoPrevisao } from "@/lib/tarefas-previsao";
import { MiniPrevisao } from "@/components/VisuaisPrevisao";

export default function TiposPrevisao({ explorar }: { explorar: (tipo: TipoPrevisao) => void }) {
  return <>
    <div className="faixa-informativa">Estamos escolhendo quais tarefas entram no TCC. Direção é o alvo atual; as demais opções ampliam o escopo.</div>
    <p className="legenda-catalogo">Exemplos visuais fictícios. As referências mostram usos relevantes; não estabelecem um ranking de popularidade.</p>
    <div className="catalogo-previsoes">{tarefasPrevisao.map((t, i) => <article key={t.id} className="cartao-previsao">
      <header><span className="indice-cartao">0{i + 1}</span><span className={`selo ${t.id === "direcao" ? "confirmado" : ""}`}>{t.estado}</span></header>
      <h2>{t.nome}</h2><p className="pergunta-cartao">{t.pergunta}</p>
      <MiniPrevisao tipo={t.id} />
      <p className="uso-cartao">{t.motivo}</p>
      <details><summary>Uso na pesquisa e impacto no TCC</summary>
        <dl className="detalhes-curtos"><dt>Resposta</dt><dd>{t.saida}</dd><dt>Avaliação</dt><dd>{t.metrica}</dd><dt>Para adotar</dt><dd>{t.mudanca}</dd><dt>Limite</dt><dd>{t.limite}</dd></dl>
        {t.fontes.map((f) => <div className="referencia-cartao" key={f.url}><a href={f.url} target="_blank" rel="noreferrer">{f.nome} ↗</a><p>{f.detalhe}</p></div>)}
      </details>
      <button className="botao-texto" onClick={() => explorar(t.id)}>Explorar esta combinação <span aria-hidden="true">→</span></button>
    </article>)}</div>
    <section className="bloco"><h2>Duas escolhas que acompanham o alvo</h2><div className="grade-dupla">
      <div><h3>Vários prazos</h3><div className="fluxo-chips"><span>Agora</span><span>+1h</span><span>+24h</span><span>+7 dias</span></div><p>O mesmo tipo de resposta pode ser previsto em diferentes horizontes.</p></div>
      <div><h3>Responder ou se abster</h3><div className="fluxo-chips"><span>Prever</span><span>Prever</span><span className="chip-suave">Abster-se</span></div><p>Uma regra de confiança pode selecionar respostas. Avaliar acerto e proporção respondida juntos.</p></div>
    </div><details><summary>Gatilhos, confiança e referências</summary><p>Gatilho é uma regra de entrada baseada no passado (por exemplo, aumento de volume). Abstenção é a decisão de não emitir uma previsão. Ambos precisam ser definidos no desenvolvimento; confiança declarada pela rede pode estar errada.</p><div className="links-em-linha"><a href="https://proceedings.mlr.press/v97/geifman19a.html" target="_blank" rel="noreferrer">SelectiveNet (2019) ↗</a><a href="https://proceedings.mlr.press/v70/guo17a.html" target="_blank" rel="noreferrer">Calibração (Guo et al., 2017) ↗</a><a href="/api/estudo/documentos/tarefas" target="_blank" rel="noreferrer">Pesquisa completa ↗</a></div></details></section>
  </>;
}
