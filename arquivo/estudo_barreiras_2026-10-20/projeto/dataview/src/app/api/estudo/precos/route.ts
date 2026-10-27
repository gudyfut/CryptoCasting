import { lerPrecos } from "@/lib/previsoes";
export const runtime = "nodejs";
export async function GET(request: Request) {
  const q = new URL(request.url).searchParams;
  if (!["par", "inicio", "fim", "resolucao"].every(k => q.has(k))) return Response.json({ erro: "Recorte incompleto." }, { status: 400 });
  try { return Response.json(await lerPrecos(q.get("par")!, Number(q.get("inicio")), Number(q.get("fim")), Number(q.get("resolucao")))); }
  catch (e) { return Response.json({ erro: e instanceof Error ? e.message : "Preços indisponíveis." }, { status: 400 }); }
}
