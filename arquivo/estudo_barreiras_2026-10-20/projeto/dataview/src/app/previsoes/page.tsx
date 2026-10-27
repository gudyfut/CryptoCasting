import Navegacao from "@/components/Navegacao";
import ExploradorPrevisoes from "@/components/ExploradorPrevisoes";
import { lerIndice } from "@/lib/previsoes";
import type { IndicePublico } from "@/lib/exploracao";
export const dynamic = "force-dynamic";
export const metadata = { title: "Previsões reais | CryptoCasting" };
export default async function PaginaPrevisoes({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  let indice: IndicePublico | undefined, erro: string | undefined;
  try { const { ciclo, dataset, geradoUtc, celulas, recallMedio, inicioPrecos, fimPrecos } = await lerIndice(); indice = { ciclo, dataset, geradoUtc, celulas, recallMedio, inicioPrecos, fimPrecos }; }
  catch (e) { erro = e instanceof Error ? e.message : "Exportação indisponível."; }
  const q = await searchParams;
  const inicial = indice?.celulas.find(c => c.id === q.id) ?? indice?.celulas.find(c => c.par === "BTCUSDT" && c.contexto === 24 && c.horizonte === 24 && c.fold === "DB1");
  return <><Navegacao ativa="previsoes"/><main className="pagina-explorador"><div className="abertura-explorador"><span className="selo">CICLO 001 · EVIDÊNCIA OBSERVADA</span><h1>Explorador de previsões</h1><p>Examine o que cada modelo previu, o caminho efetivamente percorrido pelo preço e o primeiro evento observado. Navegue por todas as origens de teste de desenvolvimento de 2023.</p><a href="#inspecao" className="atalho-grafico">Ir para a observação selecionada ↓</a></div>{indice && inicial ? <ExploradorPrevisoes indice={indice} inicial={inicial.id} origemInicial={typeof q.origem === "string" && Number.isSafeInteger(Number(q.origem)) ? Number(q.origem) : undefined}/> : <div className="erro-dados" role="alert"><h2>Previsões indisponíveis</h2><p>{erro}</p><p>O explorador requer a exportação local verificada dos artefatos do ciclo. Nenhuma previsão ilustrativa substitui dados ausentes.</p></div>}</main></>;
}
