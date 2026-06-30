import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ par: string }> }
) {
  const { par } = await params;

  const filePath = path.resolve(
    process.cwd(),
    "..",
    "dados",
    "resultados",
    `${par}_previsoes.json`
  );

  try {
    const content = await fs.readFile(filePath, "utf-8");
    return NextResponse.json(JSON.parse(content));
  } catch {
    return NextResponse.json(
      { error: `Previsões não encontradas para ${par}. Rode o treino primeiro.` },
      { status: 404 }
    );
  }
}
