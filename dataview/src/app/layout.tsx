import type { Metadata } from "next";
import "./globals.css";
import "./portal.css";

export const metadata: Metadata = {
  title: "CryptoCasting — Registro científico do TCC",
  description:
    "Andamento, metodologia, avaliação e previsões reais do estudo de barreiras com Mamba, LSTM e AR(1).",
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
