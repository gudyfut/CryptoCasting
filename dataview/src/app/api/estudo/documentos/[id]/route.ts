import { readFile } from "node:fs/promises";
import path from "node:path";

const documentos: Record<string, string> = {
  protocolo: "docs/protocolo_experimental.md",
  tarefas: "docs/estudo_tarefas_previsao.md",
  nvidia: "docs/entregas/05_mamba_base/guia_notebook_nvidia.md",
  coleta: "docs/entregas/02_pipeline_coleta/README.md",
  dados: "docs/entregas/03_pre_processamento_amostras/resultados_execucao_oficial.md",
  infraestrutura: "docs/entregas/04_infraestrutura_baselines/README.md",
  mamba: "docs/entregas/05_mamba_base/README.md",
  matriz: "docs/entregas/05_mamba_base/matriz_experimental.md",
  piloto: "docs/entregas/04_infraestrutura_baselines/resultados_desenvolvimento_BTC_D1_D4.md",
  "piloto-neural": "docs/entregas/05_mamba_base/resultados_piloto_BTC_D1_cpu.md",
  diagnostico: "historico/analises/2026-10-13_diagnostico_mamba.md",
  historico: "historico/README.md",
  timeline: "historico/LINHA_DO_TEMPO.md",
  decisoes: "historico/DECISOES.md",
};

export async function GET(_pedido: Request, contexto: { params: Promise<{ id: string }> }) {
  const { id } = await contexto.params;
  const relativo = Object.hasOwn(documentos, id) ? documentos[id] : undefined;
  if (!relativo) return new Response("Documento não encontrado.", { status: 404 });
  try {
    const conteudo = await readFile(path.resolve(process.cwd(), "..", relativo), "utf8");
    return new Response(conteudo, { headers: { "Content-Type": "text/plain; charset=utf-8", "X-Content-Type-Options": "nosniff" } });
  } catch {
    return new Response("Documento indisponível neste ambiente.", { status: 404 });
  }
}
