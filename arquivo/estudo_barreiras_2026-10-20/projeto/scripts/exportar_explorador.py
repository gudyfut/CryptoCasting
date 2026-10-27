"""Exportação de leitura para a interface; não treina nem modifica o ciclo fechado."""
from pathlib import Path
import gzip
import hashlib
import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
CICLO = "4e232a796fcda0ea34c3"
DATASET = "9341610dbb329a858784"
DESTINO = RAIZ / "dataview/.dados/explorador"
MODELOS = ("lstm", "mamba", "ar1")


def hash_arquivo(caminho):
    with caminho.open("rb") as arquivo:
        return hashlib.file_digest(arquivo, "sha256").hexdigest()


def conferir(caminho, esperado):
    if hash_arquivo(caminho) != esperado:
        raise ValueError(f"Integridade divergente: {caminho}")


def alinhar(quadros):
    """Chave temporal única; nunca presumir alinhamento por número da linha."""
    resultado = {}
    referencia = None
    for modelo, quadro in quadros.items():
        if quadro.origem_utc.duplicated().any():
            raise ValueError("Origem duplicada")
        q = quadro.set_index("origem_utc").sort_index()
        if referencia is not None:
            if not q.index.equals(referencia.index):
                raise ValueError("Origens diferentes entre modelos")
            for coluna in ("classe", "entrada_utc", "expiracao_utc", "saida_utc", "preco_entrada", "preco_saida", "distancia", "ambiguo"):
                if not q[coluna].equals(referencia[coluna]):
                    raise ValueError(f"Desfecho divergente: {coluna}")
        referencia = q
        resultado[modelo] = q
    return resultado


def exportar():
    destino = DESTINO
    destino.mkdir(parents=True, exist_ok=True)
    manifesto_anterior = destino / "indice.json"
    # Um erro interrompe a publicação. O índice só é substituído ao terminar.
    resumo_path = RAIZ / "historico/analises/ciclo_001_completo/resumo.json"
    conferir(resumo_path, "350a6b080ded621a8bf0f53f76a0a97f5168a6e580f361912f5dd88847f1e0c5")
    resumo = json.loads(resumo_path.read_text())
    arquivos, fontes, celulas = {}, {}, []

    def ler_fonte(caminho, esperado):
        conferir(caminho, esperado)
        fontes[caminho.relative_to(RAIZ).as_posix()] = esperado

    def gravar(nome, conteudo):
        caminho = destino / nome
        caminho.parent.mkdir(parents=True, exist_ok=True)
        bruto = json.dumps(conteudo, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
        comprimido = gzip.compress(bruto, compresslevel=6, mtime=0)
        temporario = caminho.with_suffix(".parcial")
        temporario.write_bytes(comprimido)
        temporario.replace(caminho)
        arquivos[nome] = hashlib.sha256(comprimido).hexdigest()

    acumulados = {m: [] for m in MODELOS}
    registros = sorted((RAIZ / "historico/execucoes").glob("*.json"))
    for caminho in registros:
        registro = json.loads(caminho.read_text())
        if registro.get("id_ciclo") != CICLO:
            continue
        if registro["status"] != "concluida_auditada" or registro.get("auditoria") != "aprovado":
            raise ValueError("Célula sem auditoria")
        identidade = registro["id"]
        pasta = RAIZ / "dados/experimentos" / f"barreiras_{CICLO}" / identidade
        integridade_path = pasta / "integridade.json"
        ler_fonte(integridade_path, resumo["fontes"][integridade_path.relative_to(RAIZ).as_posix()])
        integridade = json.loads(integridade_path.read_text())
        quadros, metricas = {}, {}
        for modelo in MODELOS:
            for nome in ("previsoes_teste.parquet", "resultado_modelo.json"):
                fonte = pasta / modelo / nome
                ler_fonte(fonte, integridade[f"{modelo}/{nome}"])
            quadros[modelo] = pd.read_parquet(pasta / modelo / "previsoes_teste.parquet")
            metricas[modelo] = json.loads((pasta / modelo / "resultado_modelo.json").read_text())["metricas"]["teste"]
        quadros = alinhar(quadros)
        base = quadros["mamba"]
        probabilidades = {}
        for modelo, q in quadros.items():
            p = q[["p0", "p1", "p2"]].to_numpy(dtype=float)
            if not np.isfinite(p).all() or (p < 0).any() or (p > 1).any() or not np.allclose(p.sum(axis=1), 1, atol=1e-6):
                raise ValueError("Probabilidades inválidas")
            y = q.classe.to_numpy(dtype=int)
            log_loss = float(-np.log(np.maximum(p[np.arange(len(y)), y], 1e-7)).mean())
            brier = float(((p - np.eye(3)[y])**2).sum(axis=1).mean())
            if abs(log_loss - metricas[modelo]["log_loss"]) > 1e-10 or abs(brier - metricas[modelo]["brier"]) > 1e-10:
                raise ValueError("Métricas não reproduzidas")
            probabilidades[modelo] = p.tolist()
            acumulados[modelo].append(metricas[modelo]["recall"])
        segundos = lambda x: int(pd.Timestamp(x).timestamp())
        observacoes = []
        for i, (origem, linha) in enumerate(base.iterrows()):
            observacoes.append({"origem": segundos(origem), "entrada": segundos(linha.entrada_utc),
                "expiracao": segundos(linha.expiracao_utc), "saida": segundos(linha.saida_utc),
                "saidaConhecida": int(linha.saida_conhecida_indice), "precoEntrada": float(linha.preco_entrada),
                "precoSaida": float(linha.preco_saida), "distancia": float(linha.distancia),
                "classe": int(linha.classe), "ambiguo": bool(linha.ambiguo),
                "probabilidades": {m: probabilidades[m][i] for m in MODELOS}})
        celula = {"id": identidade, **registro["celula"], "n": len(base), "inicio": segundos(base.index[0]), "fim": segundos(base.index[-1]),
                  "execucaoInicio": registro["inicio_utc"], "execucaoFim": registro["fim_utc"]}
        gravar(f"previsoes/{identidade}.json.gz", {"celula": celula, "metricas": metricas, "observacoes": observacoes})
        celulas.append(celula)
    if len(celulas) != resumo["celulas"] or len({(c['par'],c['contexto'],c['horizonte'],c['fold']) for c in celulas}) != 96:
        raise ValueError("Grade incompleta/duplicada")
    print("96 células alinhadas por timestamp; 288 séries de probabilidades recalculadas.", flush=True)
    pasta_dados = RAIZ / f"dados/processados/barreiras_{DATASET}"
    dataset_path = pasta_dados / "dataset.json"
    dataset = json.loads(dataset_path.read_text())
    if dataset["id"] != DATASET:
        raise ValueError("Dataset incorreto")
    fontes[dataset_path.relative_to(RAIZ).as_posix()] = hash_arquivo(dataset_path)
    inicio = int(pd.Timestamp("2022-12-24", tz="UTC").timestamp() // 60)
    fim = int(pd.Timestamp("2024-01-01", tz="UTC").timestamp() // 60)
    contagens = {}
    for par in sorted({c["par"] for c in celulas}):
        fonte = pasta_dados / par / "minutos.npy"
        ler_fonte(fonte, dataset["arquivos"][f"{par}/minutos.npy"])
        minutos = np.load(fonte, mmap_mode="r", allow_pickle=False)
        contagem = ausentes = 0
        for dia in range(inicio, fim, 1440):
            dados = minutos[dia-dataset["primeiro_minuto"]:dia-dataset["primeiro_minuto"]+1440]
            linhas = []
            for i, linha in enumerate(dados):
                t = (dia+i)*60
                if np.isfinite(linha[:5]).all():
                    linhas.append([t, *linha[:5].tolist()])
                    contagem += 1
                else:
                    linhas.append([t])
                    ausentes += 1
            nome_dia = pd.Timestamp(dia*60, unit="s", tz="UTC").strftime("%Y-%m-%d")
            gravar(f"precos/{par}/{nome_dia}.json.gz", linhas)
        contagens[par] = {"minutosObservados": contagem, "minutosAusentes": ausentes}
        print(f"{par}: preços exportados sem preencher {ausentes} minutos ausentes.", flush=True)
    indice = {"versao": 1, "ciclo": CICLO, "dataset": DATASET, "geradoUtc": datetime.now(timezone.utc).isoformat(),
              "celulas": sorted(celulas, key=lambda c: (c['par'],c['contexto'],c['horizonte'],c['fold'])),
              "recallMedio": {m: np.mean(v,axis=0).tolist() for m,v in acumulados.items()},
              "precos": contagens, "inicioPrecos": inicio*60, "fimPrecos": fim*60,
              "primeiroMinuto": dataset["primeiro_minuto"], "arquivos": arquivos, "fontes": fontes,
              "exportadorSha256": hash_arquivo(Path(__file__))}
    temporario = manifesto_anterior.with_suffix(".parcial")
    temporario.write_text(json.dumps(indice, ensure_ascii=False, indent=2), encoding="utf-8")
    temporario.replace(manifesto_anterior)
    recibo = {"ciclo": CICLO, "dataset": DATASET, "geradoUtc": indice["geradoUtc"], "celulas": len(celulas),
              "origensPorConfiguracao": 7908, "previsoesPorModelo": sum(c["n"] for c in celulas),
              "indiceSha256": hash_arquivo(manifesto_anterior), "exportadorSha256": indice["exportadorSha256"],
              "arquivos": len(arquivos), "recallMedio": indice["recallMedio"], "precos": contagens}
    (RAIZ / "historico/qualificacoes/explorador_previsoes_2026-10-19.json").write_text(json.dumps(recibo, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(recibo, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    exportar()
