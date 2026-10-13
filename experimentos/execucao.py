"""Uma execução pareada por célula/fold/seed, com AR(1) reutilizável por tarefa."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

from baseline_ar1.modelo import ajustar_ar1, construir_pares_autorregressivos, prever_amostras
from camada_dados.armazenamento import sha256_arquivo
from pre_processamento.folds import FOLDS
from modelo.mamba_modelo import _importar_mamba
from .avaliacao import alinhar_previsoes, comparar_modelos
from .auditoria import auditar_execucao
from .configuracao import RAIZ, VERSAO, gerar_celulas, validar_configuracao
from .dados import DatasetProcessado, preparar_entradas
from .registro import ambiente, assinatura_codigo, capturar_codigo, gravar_json, identidade, inventariar, verificar_resultado
from .treinamento import treinar_modelo, fixar_seed, REGRAS_TREINO
from .qualificacao import verificar_modelos


def obter_ar1(dataset: DatasetProcessado, celula: dict, raiz_saida: Path, codigo: str, versoes: dict):
    celula_ar1 = {**celula, "granularidade": "1d" if celula["tarefa"] == "principal" else celula["granularidade"], "contexto_dias": 7}
    chave = {k: celula_ar1[k] for k in ("par", "granularidade", "fold", "tarefa")}
    identificador = identidade({**chave, "dataset": dataset.resumo_manifesto, "codigo": codigo, "versoes": versoes})
    destino = raiz_saida / "ar1_compartilhado" / identificador
    if (destino / "resultado.json").exists():
        registro = verificar_resultado(destino / "resultado.json", ("validacao.parquet", "teste.parquet"))
        if registro["celula"] != chave or registro["id"] != identificador or registro["versoes"] != versoes:
            raise ValueError("Cache AR(1) incompatível com a execução solicitada.")
        return registro, {b: pd.read_parquet(destino / f"{b}.parquet") for b in ("validacao", "teste")}
    candles, blocos = dataset.carregar(celula_ar1)
    parametros = ajustar_ar1(*construir_pares_autorregressivos(candles, blocos["treino"]))
    destino.mkdir(parents=True, exist_ok=True)
    previsoes = {}
    for bloco in ("validacao", "teste"):
        quadro = prever_amostras(candles, blocos[bloco], parametros).rename(columns={"classe_prevista_ar1": "classe_prevista"})
        quadro.to_parquet(destino / f"{bloco}.parquet", index=False)
        previsoes[bloco] = quadro
    registro = {"contrato": VERSAO, "estado": "concluido", "id": identificador,
                "celula": chave, "sha256_manifesto_dataset": dataset.resumo_manifesto,
                "sha256_codigo": codigo, "versoes": versoes,
                "parametros": parametros.__dict__, "arquivos": inventariar(destino)}
    gravar_json(destino / "resultado.json", registro)
    return registro, previsoes


def executar_grade(configuracao: dict, *, nova_tentativa: bool = False) -> list[Path]:
    validar_configuracao(configuracao)
    caminho = Path(configuracao["dataset"])
    dataset = DatasetProcessado(caminho if caminho.is_absolute() else RAIZ / caminho)
    fixar_seed(configuracao["seeds"][0])
    ambiente_atual = ambiente()
    if configuracao["dispositivo"] == "cuda" and not ambiente_atual["cuda_disponivel"]:
        raise RuntimeError("CUDA indisponível. Revise dispositivo/backend explicitamente.")
    _importar_mamba(configuracao["backend_mamba"])
    fontes = capturar_codigo()
    codigo = assinatura_codigo(fontes)
    protocolo = sha256_arquivo(RAIZ / "docs/protocolo_experimental.md")
    raiz_saida = RAIZ / "dados/experimentos"
    saidas = []
    # A grade da invocação não integra a identidade de uma célula reutilizável.
    opcoes = {k: v for k, v in configuracao.items() if k not in ("pares", "granularidades", "contextos_dias", "folds", "seeds", "dataset", "tarefa")}
    for celula in gerar_celulas(configuracao):
        identificador = identidade({"celula": celula, "opcoes": opcoes, "dataset": dataset.resumo_manifesto,
                                   "codigo": codigo, "protocolo": protocolo, "ambiente": ambiente_atual["versoes"],
                                   "hardware": {k: ambiente_atual[k] for k in ("gpu", "cpu", "sistema", "cuda_pytorch", "cudnn")},
                                   "execucao_numerica": ambiente_atual["execucao_numerica"],
                                   "fontes_backend": ambiente_atual["fontes_backend"],
                                   "regras": REGRAS_TREINO})
        destino = raiz_saida / f"pareado_{identificador}"
        if destino.exists() and not nova_tentativa:
            if not (destino / "resultado.json").is_file():
                raise RuntimeError(f"Execução incompleta preservada em {destino}. Use --nova-tentativa para reiniciar em outro diretório.")
            existente, _ = auditar_execucao(destino)
            if existente["id"] != identificador:
                raise ValueError("Identidade do resultado diverge da execução solicitada.")
            print(f"Reutilizando execução íntegra: {destino}", flush=True)
            saidas.append(destino)
            continue
        if nova_tentativa:
            destino = destino.with_name(destino.name + "_" + uuid.uuid4().hex[:8])
        destino.mkdir(parents=True, exist_ok=False)
        inicio = datetime.now(timezone.utc).isoformat()
        gravar_json(destino / "estado.json", {"estado": "em_execucao", "inicio_utc": inicio, "celula": celula})
        try:
            gravar_json(destino / "configuracao.json", configuracao)
            gravar_json(destino / "ambiente.json", ambiente_atual)
            gravar_json(destino / "codigo_fonte.json", fontes)
            (destino / "protocolo_executado.md").write_bytes((RAIZ / "docs/protocolo_experimental.md").read_bytes())
            candles, blocos = dataset.carregar(celula)
            matriz, scaler, indices = preparar_entradas(candles, blocos, configuracao["features"], configuracao["normalizador"])
            gravar_json(destino / "normalizador.json", scaler)
            np.save(destino / "indices_ajuste_normalizador.npy", indices, allow_pickle=False)
            if configuracao["backend_mamba"] == "oficial":
                passos = int(blocos["treino"].iloc[0]["indice_contexto_fim"] - blocos["treino"].iloc[0]["indice_contexto_inicio"] + 1)
                gravar_json(destino / "qualificacao_modelos.json", verificar_modelos(configuracao, matriz.shape[1], passos))
            registro_ar1, previsoes_ar1 = obter_ar1(dataset, celula, raiz_saida, codigo, ambiente_atual["versoes"])
            for bloco in ("validacao", "teste"):
                alinhar_previsoes(blocos[bloco], previsoes_ar1[bloco])
            resultados_modelos = {"ar1": registro_ar1}
            previsoes = {b: {"ar1": previsoes_ar1[b]} for b in ("validacao", "teste")}
            for nome in ("lstm", "mamba"):
                resultados_modelos[nome], predicoes = treinar_modelo(nome, configuracao, celula, matriz, blocos, destino / nome)
                for bloco in previsoes:
                    previsoes[bloco][nome] = predicoes[bloco]
            avaliacoes = {b: comparar_modelos(p) for b, p in previsoes.items()}
            for bloco, modelos in previsoes.items():
                for nome, quadro in modelos.items():
                    quadro = quadro.assign(fold=celula["fold"], bloco=bloco, modelo=nome)
                    # AR(1) conserva metadados da própria frequência e não recebe seed.
                    if nome != "ar1":
                        quadro["seed"] = celula["seed"]
                    quadro.to_parquet(destino / f"previsoes_{nome}_{bloco}.parquet", index=False)
            fold = next(f for f in FOLDS if f.nome == celula["fold"])
            resultado = {"contrato": VERSAO, "estado": "concluido", "id": identificador,
                         "inicio_utc": inicio, "fim_utc": datetime.now(timezone.utc).isoformat(),
                         "tipo_fold": "desenvolvimento", "protocolo": "1.6", "sha256_protocolo": protocolo,
                         "sha256_codigo": codigo, "id_dataset": dataset.raiz.name,
                         "sha256_manifesto_dataset": dataset.resumo_manifesto, "celula": celula,
                         "configuracao": configuracao, "features": scaler["features"], "dimensao_entrada": matriz.shape[1],
                         "fold": fold.__dict__, "contagens": {b: len(q) for b, q in blocos.items()},
                         "ambiente": ambiente_atual, "modelos": resultados_modelos, "avaliacoes": avaliacoes,
                         "fontes_preservadas": True,
                         "arquivos": inventariar(destino)}
            gravar_json(destino / "resultado.json", resultado)
            gravar_json(destino / "estado.json", {"estado": "concluido", "celula": celula, "inicio_utc": inicio,
                                                  "fim_utc": resultado["fim_utc"]})
            print(f"Execução pareada: {destino}", flush=True)
            saidas.append(destino)
        except BaseException as erro:
            gravar_json(destino / "estado.json", {"estado": "interrompido" if isinstance(erro, KeyboardInterrupt) else "falhou",
                                                   "celula": celula, "inicio_utc": inicio,
                                                   "fim_utc": datetime.now(timezone.utc).isoformat(),
                                                   "erro": str(erro), "tipo": type(erro).__name__})
            raise
    return saidas
