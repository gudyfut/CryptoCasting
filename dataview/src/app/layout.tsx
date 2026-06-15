import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CryptoCasting — Dataview",
  description:
    "Visualização de resultados do sistema de previsão direcional de criptomoedas com arquitetura Mamba",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body className="bg-gray-950 text-gray-100 antialiased">{children}</body>
    </html>
  );
}
