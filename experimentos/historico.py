"""Exporta evidências leves sem treinar, sobrescrever ou aprovar resultados."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

import pandas as pd

from .configuracao import RAIZ

SITUACOES = ("em_revisao", "exploratorio", "inconclusivo", "invalidado", "validado_tecnicamente")
LIMITE_BYTES = 5 * 1024 * 1024


def resumo_arquivo(caminho: Path) -> str:
    with caminho.open("rb") as arquivo:
        return hashlib.file_digest(arquivo, "sha256").hexdigest()


def salvar_json(caminho: Path, valor: dict) -> None:
    caminho.write_text(json.dumps(valor, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def ler_registro(caminho: Path, avisos: list[str]) -> dict:
    if not caminho.exists():
        return {}
    try:
        valor = json.loads(caminho.read_text(encoding="utf-8"))
        if not isinstance(valor, dict):
            raise ValueError("Raiz não é objeto JSON.")
        return valor
    except (ValueError, UnicodeError) as erro:
        avisos.append(f"{caminho.name} ilegível como registro: {erro}")
        return {}


def ficha_resultado(resultado: dict) -> str:
    """Resumo legível dos campos preservados, sem preencher ausências por suposição."""
    campos = ("metodo", "serie", "contexto_dias_amostras", "fronteiras_utc", "fold",
              "configuracao", "features", "dimensao_entrada", "contagens",
              "pares_retorno_ajuste", "coeficientes")
    detalhes = {k: resultado[k] for k in campos if k in resultado}
    linhas = ["## Dados e configuração registrados", "", "```json",
              json.dumps(detalhes, ensure_ascii=False, indent=2), "```", "",
              "As datas acima são fronteiras exclusivas dos blocos. Os CSVs preservam as origens efetivamente avaliadas após a purga e exclusão de lacunas.", "",
              "## Métricas observadas", "", "| Bloco | Modelo | Amostras | BA | Accuracy | F1 macro |", "|---|---|---:|---:|---:|---:|"]
    avaliacoes = resultado.get("avaliacoes", {})
    if resultado.get("tipo") == "piloto_descritivo_baseline_ar1":
        avaliacoes = {b: {"metricas": {"ar1": m}} for b, m in resultado.get("metricas", {}).items()}
    for bloco, avaliacao in avaliacoes.items():
        for modelo, metrica in avaliacao.get("metricas", {}).items():
            if all(k in metrica for k in ("amostras", "balanced_accuracy", "accuracy", "f1_macro")):
                linhas.append(f"| {bloco} | {modelo} | {metrica['amostras']} | {metrica['balanced_accuracy']:.4f} | {metrica['accuracy']:.4f} | {metrica['f1_macro']:.4f} |")
    if not avaliacoes:
        linhas.extend(["", "Métricas não disponíveis neste registro."])
    modelos = resultado.get("modelos", {})
    treino = {nome: dados for nome, dados in modelos.items() if "regras_treino" in dados}
    if treino:
        linhas.extend(["", "## Treinamento efetivamente registrado", "", "```json",
                       json.dumps(treino, ensure_ascii=False, indent=2), "```"])
    linhas.extend(["", "BA está na escala 0–1. Matrizes de confusão, métricas por classe, versões e hashes estão nos originais. As comparações entre modelos, a referência de 50% e o PT têm interpretações separadas.", "", ""])
    return "\n".join(linhas)


def registrar_execucao(origem: Path, destino: Path, *, titulo: str,
                      situacao: str = "em_revisao", observacao: str = "") -> Path:
    origem, destino = origem.resolve(), destino.resolve()
    if not origem.is_dir() or not any((origem / n).is_file() for n in ("resultado.json", "estado.json")):
        raise ValueError("Informe uma execução com resultado.json ou estado.json, inclusive falhas.")
    if destino == origem or destino.is_relative_to(origem) or origem.is_relative_to(destino):
        raise ValueError("O histórico e a origem precisam estar em árvores separadas.")
    if situacao not in SITUACOES or not titulo.strip():
        raise ValueError("Informe título e situação de revisão válidos.")
    pasta = destino / "experimentos" / origem.name
    if pasta.exists():
        raise FileExistsError(f"Registro preservado: {pasta}. Acrescente a revisão em acompanhamento.md; não reexporte sobre ele.")
    avisos: list[str] = []
    resultado = ler_registro(origem / "resultado.json", avisos)
    estado = ler_registro(origem / "estado.json", avisos)
    auditoria = "não executada pelo exportador; preservar incerteza"
    if resultado.get("contrato") == "entregas45-v1" and resultado.get("estado") == "concluido" and "avaliacoes" in resultado:
        from .auditoria import auditar_execucao
        try:
            auditar_execucao(origem)
            auditoria = "Hashes, contratos e métricas dos parquets conferidos; não valida equivalência com Mamba oficial."
        except (ValueError, KeyError, OSError, TypeError) as erro:
            avisos.append(f"Auditoria não aprovada: {erro}")
            auditoria = "reprovada; arquivos mantidos como evidência em revisão"
    elif resultado.get("tipo") == "piloto_descritivo_baseline_ar1":
        for nome, esperado in resultado.get("arquivos", {}).items():
            arquivo = (origem / nome).resolve()
            if not arquivo.is_relative_to(origem) or not arquivo.is_file() or resumo_arquivo(arquivo) != esperado["sha256"]:
                avisos.append(f"Hash original AR(1) divergente/ausente: {nome}")
        auditoria = ("Há divergências nos hashes históricos; preservar para revisão." if avisos else
                     "Hashes históricos conferidos; sem reconstrução retroativa do ambiente/código.")
    if avisos and situacao == "validado_tecnicamente":
        raise ValueError("Há pendências: registre como em_revisao, inconclusivo ou invalidado.")

    pasta.parent.mkdir(parents=True, exist_ok=True)
    temporario = Path(tempfile.mkdtemp(prefix=".registro_", dir=pasta.parent))
    try:
        arquivos = {}
        for arquivo in sorted(origem.rglob("*")):
            if not arquivo.is_file():
                continue
            if not arquivo.resolve().is_relative_to(origem):
                raise ValueError("Arquivo da execução aponta para fora da origem.")
            relativo = arquivo.relative_to(origem).as_posix()
            registro = {"sha256_original": resumo_arquivo(arquivo), "bytes_original": arquivo.stat().st_size}
            saida = None
            if arquivo.stat().st_size > LIMITE_BYTES:
                registro["motivo_local"] = "Acima de 5 MiB; preservar em backup de artefatos."
            elif arquivo.suffix in (".json", ".md", ".csv"):
                saida = temporario / "originais" / relativo
                saida.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(arquivo, saida)
            elif arquivo.suffix == ".parquet":
                saida = temporario / "previsoes" / Path(relativo).with_suffix(".csv")
                saida.parent.mkdir(parents=True, exist_ok=True)
                try:
                    quadro = pd.read_parquet(arquivo)
                    texto = quadro.to_csv(index=False, lineterminator="\n", float_format="%.17g")
                    if len(texto.encode("utf-8")) > LIMITE_BYTES:
                        registro["motivo_local"] = "CSV excede 5 MiB; preservar parquet em backup."
                        saida = None
                    else:
                        saida.write_text(texto, encoding="utf-8", newline="\n")
                        registro["linhas"] = len(quadro)
                        registro["tipos_colunas_original"] = {nome: str(tipo) for nome, tipo in quadro.dtypes.items()}
                except (ValueError, OSError) as erro:
                    avisos.append(f"Conversão não realizada: {relativo}: {erro}")
                    registro["motivo_local"] = "Parquet ilegível; não houve fabricação de previsões."
                    saida = None
            else:
                registro["motivo_local"] = "Binário/log mantido na execução local; hash permite conferir backup."
            if saida:
                registro.update({"arquivo_versionado": saida.relative_to(temporario).as_posix(), "sha256_versionado": resumo_arquivo(saida)})
            arquivos[relativo] = registro
        if avisos and situacao == "validado_tecnicamente":
            raise ValueError("Exportação tem pendências; não marcar como validado_tecnicamente.")
        celula = resultado.get("celula", estado.get("celula", {}))
        if not celula and resultado.get("tipo") == "piloto_descritivo_baseline_ar1":
            celula = {k: resultado.get(k) for k in ("par", "fold", "tarefa", "granularidade")}
        registro = {
            "contrato": "historico-experimentos-v1", "id": origem.name, "titulo": titulo,
            "registrado_utc": datetime.now(timezone.utc).isoformat(),
            "execucao_utc": resultado.get("inicio_utc"),
            "nota_data": "Data ausente não é inferida de mtime nem da data de importação.",
            "situacao_revisao": situacao, "estado_execucao": resultado.get("estado", estado.get("estado", "historico_sem_estado_explicito")),
            "tipo_evidencia": resultado.get("tipo_fold", "não informado"),
            "origem_local": origem.relative_to(RAIZ).as_posix() if origem.is_relative_to(RAIZ) else str(origem),
            "celula": celula, "id_dataset": resultado.get("id_dataset"),
            "configuracao": resultado.get("configuracao", {}),
            "contagens": resultado.get("contagens", {"pares_retorno_ajuste": resultado.get("pares_retorno_ajuste")}),
            "auditoria": auditoria, "avisos": avisos, "observacao": observacao,
            "arquivos": arquivos,
        }
        salvar_json(temporario / "registro.json", registro)
        (temporario / "README.md").write_text(
            f"# {titulo}\n\n- ID: `{origem.name}`\n- Situação inicial: **{situacao}**\n"
            f"- Execução UTC: {registro['execucao_utc'] or 'não registrada na origem'}\n"
            f"- Célula: `{json.dumps(celula, ensure_ascii=False)}`\n"
            f"- Dataset: `{registro['id_dataset']}`\n- Estado de execução: {registro['estado_execucao']}\n"
            f"- Auditoria: {auditoria}\n\n{observacao}\n\n" + ficha_resultado(resultado) +
            "## Evidências\n\n"
            "[Registro e inventário](registro.json) contém tamanho, configuração disponível, caminhos e hashes. "
            "`originais/` preserva os JSONs e documentos existentes; `previsoes/` guarda os parquets leves convertidos em CSV, com timestamps e rótulos. "
            "O hash do CSV é distinto do hash do parquet de origem. Ausências de metadados permanecem explícitas.\n\n"
            "Checkpoints e demais binários locais não estão neste pacote; precisam de backup separado para reprodução completa. "
            "Os hashes permitem verificar a cópia, mas não recuperam arquivos perdidos.\n\n"
            "[Acompanhamento e revisões](acompanhamento.md). Nunca substituir os originais para corrigir um resultado histórico.\n",
            encoding="utf-8",
        )
        (temporario / "acompanhamento.md").write_text(
            f"# Acompanhamento\n\n## {registro['registrado_utc']} — registro inicial\n\n"
            f"Situação: **{situacao}**. {observacao}\n\n"
            "## Próximas revisões\n\nAcrescentar data, responsável, motivo, evidência, classificação e vínculo com nova execução. "
            "Preservar entradas anteriores. Resultado desfavorável não implica invalidade técnica; auditoria aprovada não implica conclusão científica.\n",
            encoding="utf-8",
        )
        temporario.rename(pasta)
    except BaseException:
        # A pasta é criada exclusivamente por esta função dentro do histórico.
        if temporario.is_dir() and temporario.resolve().parent == pasta.parent.resolve() and temporario.name.startswith(".registro_"):
            shutil.rmtree(temporario)
        raise
    atualizar_indice(destino)
    return pasta


def atualizar_indice(destino: Path) -> None:
    registros = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((destino / "experimentos").glob("*/registro.json"))]
    registros.sort(key=lambda r: (r["execucao_utc"] is not None, r["execucao_utc"] or "", r["celula"].get("par", ""), r["celula"].get("fold", ""), r["id"]))
    linhas = ["# Linha do tempo dos experimentos", "", "Gerada por `run_registro.py`. Datas ausentes ficam em um grupo sem cronologia confirmada; folds não são datas de execução.", "", "| Execução UTC | Experimento | Célula | Revisão inicial |", "|---|---|---|---|"]
    for r in registros:
        titulo = r['titulo'].replace('|', '/').replace('\n', ' ').replace('[', '(').replace(']', ')')
        celula = r['celula']
        linhas.append(f"| {r['execucao_utc'] or 'Não registrada'} | [{titulo}](experimentos/{r['id']}/README.md) | {celula.get('par', '—')} / {celula.get('fold', '—')} | {r['situacao_revisao']} |")
    linhas.extend(["", "Consultar acompanhamento.md de cada execução para revisões posteriores. A data de registro no Git não substitui a data real do experimento.", ""])
    (destino / "LINHA_DO_TEMPO.md").write_text("\n".join(linhas), encoding="utf-8")
