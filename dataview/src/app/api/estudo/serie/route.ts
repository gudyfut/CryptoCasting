import { NextRequest, NextResponse } from "next/server";
import fs from "node:fs/promises";
import path from "node:path";
import { createHash } from "node:crypto";
import { gunzipSync } from "node:zlib";
import { raiz, ler } from "@/lib/estudo";
import type { ResumoPortal } from "@/lib/tipos";
export const dynamic = "force-dynamic";
export async function GET(req:NextRequest) {
  const id = req.nextUrl.searchParams.get("id");
  if (!id || !/^[a-f0-9]{20}$/.test(id)) return NextResponse.json({erro:"Identificador inválido."},{status:400});
  const resumo = await ler<ResumoPortal>("dados/portal/resumo.json");
  const serie = resumo?.series.find(s=>s.id===id);
  if (!serie) return NextResponse.json({erro:"Série auditada não disponível."},{status:404});
  const base = path.join(raiz,"dados/portal");
  const arquivo = path.resolve(base,serie.arquivo);
  if (!arquivo.startsWith(base+path.sep)) return NextResponse.json({erro:"Caminho inválido."},{status:500});
  const bytes = await fs.readFile(arquivo);
  if (createHash("sha256").update(bytes).digest("hex")!==serie.sha256) return NextResponse.json({erro:"Integridade da exportação não confirmada. Atualize a página."},{status:503});
  return new NextResponse(gunzipSync(bytes).toString("utf8"),{headers:{"Content-Type":"application/json; charset=utf-8","Cache-Control":"no-store"}});
}
