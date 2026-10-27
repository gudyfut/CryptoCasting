import {ler} from "@/lib/estudo";
import type {ResumoPortal} from "@/lib/tipos";
import ExploradorRetorno from "@/components/ExploradorRetorno";
export const dynamic="force-dynamic";
export default async function Previsoes({searchParams}:{searchParams:Promise<{id?:string}>}) {
  const resumo=await ler<ResumoPortal>("dados/portal/resumo.json");
  const parametros=await searchParams;
  return <section className="secao explorador"><p className="sobretitulo">EXPLORADOR DE PREVISÕES REAIS</p><h1>Do retorno previsto ao preço observado.</h1><p className="introducao">Compare as previsões no mesmo instante. Escolha a moeda, o período e o contexto; inspecione o preço observado exatamente 24 horas depois.</p>{!resumo?.avaliacao_completa&&<div className="aviso"><b>Resultados parciais de uma execução em andamento.</b> Somente previsões já auditadas estão disponíveis. A ausência de um modelo ou recorte nesta lista não significa resultado zero ou exclusão por desempenho.</div>}<ExploradorRetorno indice={resumo?.series??[]} idInicial={parametros.id}/></section>;
}
