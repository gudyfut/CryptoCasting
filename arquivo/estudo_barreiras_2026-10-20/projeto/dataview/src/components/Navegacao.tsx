import Link from "next/link";
export default function Navegacao({ ativa = "estudo" }: { ativa?: "estudo" | "previsoes" }) {
  return <header className="topo" id="inicio"><Link className="marca" href="/">CryptoCasting<span>PESQUISA EM PREVISÃO FINANCEIRA</span></Link><nav className="navegacao-principal" aria-label="Páginas do estudo"><Link href="/" aria-current={ativa === "estudo" ? "page" : undefined}>Estudo e andamento</Link><Link href="/previsoes" aria-current={ativa === "previsoes" ? "page" : undefined}>Previsões reais</Link><a href="/api/estudo/documentos/protocolo" target="_blank" rel="noreferrer">Protocolo ↗</a></nav></header>;
}
