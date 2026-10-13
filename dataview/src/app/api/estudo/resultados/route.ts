import { NextResponse } from "next/server";
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import type { ResultadoLocal } from "@/lib/estudo";
import { interpretarResultado } from "@/lib/resultados-locais";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  const raiz = path.resolve(process.cwd(), "../dados/experimentos");
  const resultados: ResultadoLocal[] = [];
  const avisos: string[] = [];
  try {
    const pastas = await readdir(raiz, { withFileTypes: true });
    for (const pasta of pastas.sort((a, b) => a.name.localeCompare(b.name)).filter((p) => p.isDirectory() && /^pareado_[a-f0-9]{20}(_[a-f0-9]{8})?$/.test(p.name))) {
      try {
        const registro: unknown = JSON.parse(await readFile(path.join(raiz, pasta.name, "resultado.json"), "utf8"));
        resultados.push(interpretarResultado(registro, pasta.name));
      } catch {
        avisos.push(`${pasta.name}: execução incompleta ou resumo incompatível. Consulte os artefatos locais.`);
      }
    }
    return NextResponse.json({ resultados, avisos, atualizacao: new Date().toISOString() });
  } catch (erro) {
    if ((erro as NodeJS.ErrnoException).code === "ENOENT") return NextResponse.json({ resultados, avisos, atualizacao: new Date().toISOString() });
    return NextResponse.json({ erro: "Não foi possível ler os resultados locais." }, { status: 500 });
  }
}
