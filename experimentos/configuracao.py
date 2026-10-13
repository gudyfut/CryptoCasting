"""Grade explícita de desenvolvimento; avaliação final permanece bloqueada."""

from __future__ import annotations

import itertools
import json
from pathlib import Path

from pre_processamento.contrato import PARES, GRANULARIDADES

RAIZ = Path(__file__).resolve().parents[1]
VERSAO = "entregas45-v1"


def validar_configuracao(configuracao: dict) -> dict:
    obrigatorias = {
        "contrato", "dataset", "pares", "granularidades", "contextos_dias", "tarefa",
        "folds", "seeds", "features", "normalizador", "largura_mamba", "largura_lstm",
        "backend_mamba", "dispositivo", "microbatch",
    }
    if set(configuracao) != obrigatorias:
        raise ValueError(f"Chaves de configuração divergentes: {set(configuracao) ^ obrigatorias}")
    if configuracao["contrato"] != VERSAO:
        raise ValueError("Contrato experimental incompatível.")
    for chave in ("largura_mamba", "largura_lstm"):
        if type(configuracao[chave]) is not int:
            raise ValueError(f"{chave} deve ser inteiro.")
    for chave in ("contextos_dias", "seeds"):
        if not isinstance(configuracao[chave], list) or any(type(v) is not int for v in configuracao[chave]):
            raise ValueError(f"{chave} deve conter inteiros.")
    for chave, permitidos in {
        "pares": PARES, "granularidades": GRANULARIDADES, "contextos_dias": (7, 14),
        "folds": ("D1", "D2", "D3", "D4"), "seeds": (42,),
    }.items():
        valores = configuracao[chave]
        if not isinstance(valores, list) or not valores or any(v not in permitidos for v in valores) or len(set(valores)) != len(valores):
            raise ValueError(f"Grade inválida em {chave}. Apenas desenvolvimento D1–D4/seed 42 está liberado; F1–F8 exigem congelamento posterior.")
    for chave, permitidos in {
        "tarefa": ("principal", "proximo_candle"), "features": ("ohlcv", "ampliadas"),
        "normalizador": ("standard", "minmax"), "largura_mamba": (32, 64), "largura_lstm": (32, 64),
        "backend_mamba": ("pytorch", "oficial"), "dispositivo": ("cpu", "cuda"),
    }.items():
        if configuracao[chave] not in permitidos:
            raise ValueError(f"Opção fora do protocolo: {chave}")
    if configuracao["tarefa"] == "proximo_candle" and configuracao["contextos_dias"] != [7]:
        raise ValueError("Próximo candle exige contexto de 7 dias.")
    tamanho = configuracao["microbatch"]
    if type(tamanho) is not int or tamanho < 1 or tamanho > 32 or 32 % tamanho:
        raise ValueError("Microbatch deve dividir o batch efetivo 32: 1, 2, 4, 8, 16 ou 32.")
    if configuracao["backend_mamba"] == "oficial" and configuracao["dispositivo"] != "cuda":
        raise ValueError("Mamba oficial exige CUDA neste projeto; para CPU selecione pytorch.")
    if not isinstance(configuracao["dataset"], str) or not configuracao["dataset"].strip():
        raise ValueError("Informe o diretório do dataset.")
    return configuracao


def carregar_configuracao(caminho: Path) -> dict:
    return validar_configuracao(json.loads(caminho.read_text(encoding="utf-8")))


def gerar_celulas(configuracao: dict) -> list[dict]:
    validar_configuracao(configuracao)
    celulas = []
    for par, granularidade, contexto, fold, seed in itertools.product(*(
        configuracao[chave] for chave in ("pares", "granularidades", "contextos_dias", "folds", "seeds")
    )):
        tarefa = configuracao["tarefa"]
        if tarefa == "proximo_candle" and granularidade == "1d":
            tarefa = "principal"  # Mesma identidade: reutilizar o resultado diário.
        celulas.append({"par": par, "granularidade": granularidade, "contexto_dias": contexto,
                        "fold": fold, "seed": seed, "tarefa": tarefa})
    return celulas
