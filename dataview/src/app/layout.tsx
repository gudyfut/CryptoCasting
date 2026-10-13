import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CryptoCasting — Documentação do TCC",
  description:
    "Objetivos, método, dados, entregas e resultados do estudo de previsão direcional de criptomoedas com Mamba, ARIMA e LSTM.",
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
