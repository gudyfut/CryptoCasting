import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = { title: 'CryptoCasting · Evolução da pesquisa', description: 'Entenda cada fase do CryptoCasting: o que testamos, o que aprendemos e o estado atual dos modelos e simulações.' };
export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="pt-BR" data-scroll-behavior="smooth"><body>{children}</body></html>; }
