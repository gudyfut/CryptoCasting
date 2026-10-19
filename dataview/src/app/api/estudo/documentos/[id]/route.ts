import { readFile } from "node:fs/promises";
import path from "node:path";
const documentos: Record<string, () => Promise<string>> = {
  protocolo: () => readFile(path.resolve(process.cwd(), "../docs/protocolo_experimental.md"), "utf8"),
  andamento: () => readFile(path.resolve(process.cwd(), "../docs/andamento.md"), "utf8"),
  ciclo: () => readFile(path.resolve(process.cwd(), "../historico/ciclos/ciclo_001.md"), "utf8"),
  plano: () => readFile(path.resolve(process.cwd(), "../plano.md"), "utf8"),
  resultados: () => readFile(path.resolve(process.cwd(), "../historico/analises/ciclo_001_resultados.md"), "utf8"),
  proximo: () => readFile(path.resolve(process.cwd(), "../historico/ciclos/ciclo_002_proposto.md"), "utf8")
};
export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const arquivo = Object.hasOwn(documentos, id) ? documentos[id] : undefined;
  if (!arquivo) return new Response("Documento não encontrado.", { status: 404 });
  try { return new Response(await arquivo(), { headers: { "content-type": "text/plain; charset=utf-8" } }); }
  catch { return new Response("Documento indisponível.", { status: 404 }); }
}
