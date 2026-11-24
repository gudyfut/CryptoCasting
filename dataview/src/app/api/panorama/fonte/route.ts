import { NextRequest, NextResponse } from 'next/server';
import { panorama, conferirArquivo } from '@/lib/panorama-servidor';
import { fontesEvolucao } from '@/lib/evolucao-servidor';
import { fontesFichas } from '@/lib/fichas-servidor';
import { carregarCustos } from '@/lib/custos-servidor';
export const runtime = 'nodejs';
export async function GET(req: NextRequest) {
  const caminho = req.nextUrl.searchParams.get('caminho') ?? '';
  const custos = await carregarCustos();
  const hash = panorama.fontes[caminho] ?? fontesFichas()[caminho] ?? (await fontesEvolucao())[caminho] ?? custos.arquivos?.[caminho];
  if (!hash || !/\.(md|json)$/.test(caminho)) return NextResponse.json({ erro: 'Fonte fora do índice da apresentação.' }, { status: 404 });
  try {
    const b = await conferirArquivo(caminho, hash);
    return new NextResponse(b.toString('utf8'), { headers: { 'Content-Type': 'text/plain; charset=utf-8', 'X-Content-Type-Options': 'nosniff', 'Cache-Control': 'no-store', 'X-Source-SHA256': hash } });
  } catch (erro) {
    return NextResponse.json({ erro: (erro as NodeJS.ErrnoException).code === 'ENOENT' ? 'Fonte indisponível nesta máquina.' : 'Fonte alterada desde a exportação; conferir antes de apresentar.' }, { status: 409 });
  }
}
