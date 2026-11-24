import { NextRequest, NextResponse } from 'next/server';
import { panorama, conferirArquivo } from '@/lib/panorama-servidor';
export const runtime = 'nodejs';
export async function GET(req: NextRequest) {
  const id = req.nextUrl.searchParams.get('id') ?? '';
  if (!/^[a-f0-9]{64}$/.test(id) || !panorama.series.some(s => s.id === id)) return NextResponse.json({ erro: 'Série desconhecida.' }, { status: 404 });
  try {
    const b = await conferirArquivo(`dados/portal_panorama/series/${id}.json`, id);
    return new NextResponse(b.toString('utf8'), { headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'private, max-age=3600, immutable' } });
  } catch (erro) {
    const ausente = (erro as NodeJS.ErrnoException).code === 'ENOENT';
    return NextResponse.json({ erro: ausente ? 'A série exportada não está disponível nesta máquina. O treinamento histórico não é zero; restaure a exportação.' : 'A integridade da série não foi confirmada. Nenhuma previsão substituta será exibida.' }, { status: ausente ? 404 : 409 });
  }
}
