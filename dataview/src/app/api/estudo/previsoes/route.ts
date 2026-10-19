import { lerIndice, lerSerie } from "@/lib/previsoes";
export const runtime = "nodejs";
export async function GET(request: Request) {
  try {
    const id = new URL(request.url).searchParams.get("id");
    if (id) {
      if (!/^[a-f0-9]{20}$/.test(id)) return Response.json({ erro: "Identificador inválido." }, { status: 400 });
      return Response.json(await lerSerie(id));
    }
    const { ciclo, dataset, geradoUtc, celulas, recallMedio, inicioPrecos, fimPrecos } = await lerIndice();
    return Response.json({ ciclo, dataset, geradoUtc, celulas, recallMedio, inicioPrecos, fimPrecos });
  } catch (e) { return Response.json({ erro: e instanceof Error ? e.message : "Dados indisponíveis." }, { status: 503 }); }
}
