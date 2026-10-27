import { NextResponse } from "next/server";
import { lerExecucoes } from "@/lib/registros";
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export async function GET() {
  try { return NextResponse.json({ ...await lerExecucoes(), atualizacao: new Date().toISOString() }); }
  catch { return NextResponse.json({ erro: "Não foi possível consultar os registros." }, { status: 500 }); }
}
