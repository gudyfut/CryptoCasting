import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = { title: "CryptoCasting · Pesquisa em 24 horas", description: "Comparação experimental de Mamba, LSTM, ARIMA e persistência na previsão de retornos de criptomoedas." };
export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="pt-BR"><body><header className="topo"><Link className="marca" href="/">CC<span>CryptoCasting<small>CADERNO DE PESQUISA · TCC</small></span></Link><nav aria-label="Navegação principal"><Link href="/">Estudo</Link><Link href="/#metodologia">Metodologia</Link><Link href="/#resultados">Resultados</Link><Link href="/previsoes">Explorar previsões</Link></nav></header><main>{children}</main><footer>Pesquisa experimental · Binance Spot · Horários em UTC · Resultados sujeitos às condições documentadas de avaliação.</footer></body></html>;
}
