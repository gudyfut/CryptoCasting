import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CryptoCasting — Entenda o experimento",
  description:
    "Guia do TCC: barreiras, treinamento temporal, log-loss, Brier, simulação de operações e resultados explicados passo a passo.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
