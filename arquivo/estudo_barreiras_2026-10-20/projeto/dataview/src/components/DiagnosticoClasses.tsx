"use client";
import { useMemo } from "react";
import { classesEventos, classePrevista, type Modelo, type Observacao } from "@/lib/exploracao";
import { nomes, numero, percentual, probabilidadeLegivel } from "@/lib/didatica";

export default function DiagnosticoClasses({ observacoes, modelo }: { observacoes: Observacao[]; modelo: Modelo }) {
  const linhas = useMemo(() => classesEventos.map((classe, k) => {
    const valores = observacoes.map(o => o.probabilidades[modelo][k]);
    return { classe, reais: observacoes.filter(o => o.classe === k).length,
      escolhidos: observacoes.filter(o => classePrevista(o.probabilidades[modelo]) === k).length,
      media: valores.reduce((a, b) => a + b, 0) / valores.length, minimo: Math.min(...valores), maximo: Math.max(...valores) };
  }), [observacoes, modelo]);
  const omitidas = linhas.filter(l => l.escolhidos === 0);
  return <div className="diagnostico-classes"><h3>O modelo deixou de escolher alguma classe?</h3><p>Há três perguntas diferentes: quantas vezes o evento aconteceu, quanta probabilidade recebeu e quantas vezes foi a opção mais provável de {nomes[modelo]}. Todos os números abaixo usam o recorte completo.</p>
    <div className="tabela"><table><thead><tr><th>Evento</th><th>Ocorrências reais</th><th>Probabilidade média</th><th>Variação das probabilidades</th><th>Escolhido como mais provável</th></tr></thead><tbody>{linhas.map(l => <tr key={l.classe}><th>{l.classe}</th><td>{numero(l.reais, 0)} · {percentual(l.reais / observacoes.length)}</td><td>{probabilidadeLegivel(l.media)}</td><td>{probabilidadeLegivel(l.minimo)} a {probabilidadeLegivel(l.maximo)}</td><td>{numero(l.escolhidos, 0)} · {percentual(l.escolhidos / observacoes.length)}</td></tr>)}</tbody></table></div>
    {omitidas.length > 0 && <aside className="alerta-classes"><b>Classe sem nenhuma escolha: {omitidas.map(l => l.classe.toLowerCase()).join("; ")}.</b><p>{omitidas.every(l => l.minimo > 0) ? "Recebeu probabilidade positiva em todas as origens, mas nunca a maior das três. Isso não é probabilidade zero nem ausência dessa saída no modelo." : "Há probabilidades iguais a zero neste recorte; consulte os valores individuais."} Quando o evento ocorreu e nunca foi escolhido, seu recall é zero. É uma limitação real de classificação, mesmo com probabilidades variáveis.</p></aside>}
    <p className="legenda">Exemplo: inferior 31%, expiração 40%, superior 29% escolhe expiração. Superior continua com 29% de probabilidade. Não se deve forçar escolhas equilibradas para melhorar a aparência da matriz.</p>
    {modelo === "ar1" && <aside className="alerta-classes"><b>Limitação identificada no AR(1) deste ciclo.</b><p>A simulação usa volatilidade residual fixa estimada no treino, enquanto as barreiras usam volatilidade recente. O diagnóstico encontrou escala simulada excessiva em relação às barreiras e forte subestimação da expiração. A conclusão vale para este AR(1) gaussiano, não para toda a família ARIMA.</p></aside>}
    <p><a href="/api/estudo/documentos/diagnostico" target="_blank" rel="noreferrer">Ler investigação: verificações, evidências, limitações e próximos passos ↗</a></p>
  </div>;
}
