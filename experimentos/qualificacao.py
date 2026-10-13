"""Verificações técnicas sem passos de otimizador ou seleção de configurações."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

from .auditoria import auditar_execucao, conferir_resumo
from .avaliacao import CHAVES
from .configuracao import RAIZ, gerar_celulas
from .dados import DatasetProcessado, JanelasTemporais, preparar_entradas
from .registro import ambiente, assinatura_codigo
from .treinamento import REGRAS_TREINO, criar_modelo, fixar_seed, prever


def carregar_dados(configuracao: dict, celula: dict):
    caminho = Path(configuracao["dataset"])
    dataset = DatasetProcessado(caminho if caminho.is_absolute() else RAIZ / caminho)
    candles, blocos = dataset.carregar(celula)
    matriz, normalizador, indices = preparar_entradas(
        candles, blocos, configuracao["features"], configuracao["normalizador"])
    return dataset, blocos, matriz, normalizador, indices


def verificar_modelos(configuracao: dict, dimensao: int, passos: int) -> dict:
    """Forward/backward sintéticos das duas redes; não atualiza nenhum peso.

    Dois exemplos bastam para exercitar os kernels. Não é medição da memória
    necessária ao batch de treino nem prova de equivalência entre backends.
    """
    dispositivo = torch.device(configuracao["dispositivo"])
    if dispositivo.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA indisponível. Ative o ambiente NVIDIA no Linux/WSL2; não há fallback neste piloto.")
    relatorio = {}
    for nome in ("mamba", "lstm"):
        fixar_seed(42)
        modelo = criar_modelo(nome, configuracao, dimensao).to(dispositivo)
        registro = {"backend": getattr(modelo, "backend", "torch.nn.LSTM"),
                    "parametros": sum(p.numel() for p in modelo.parameters()),
                    "formato_entrada": [2, passos, dimensao], "atualizacoes_pesos": 0}
        if nome == "mamba" and configuracao["backend_mamba"] == "oficial":
            from mamba_ssm.modules import mamba_simple
            if any(type(camada) is not mamba_simple.Mamba for camada in modelo.layers):
                raise ValueError("Esperado Mamba-1 oficial em todas as camadas.")
            if mamba_simple.causal_conv1d_fn is None:
                raise RuntimeError("causal-conv1d indisponível: instale os kernels antes de qualificar o piloto NVIDIA.")
            registro["dt_inicial"] = []
            for camada in modelo.layers:
                dt = torch.nn.functional.softplus(camada.dt_proj.bias.detach())
                minimo, maximo = float(dt.min()), float(dt.max())
                if not (0.001 - 1e-7 <= minimo <= maximo <= 0.1 + 1e-7):
                    raise ValueError("Inicialização dt do Mamba oficial divergente do intervalo padrão [0.001, 0.1].")
                registro["dt_inicial"].append({"min": minimo, "max": maximo})
        entradas = torch.randn(2, passos, dimensao, device=dispositivo, requires_grad=True)
        rotulos = torch.tensor([0, 1], device=dispositivo)
        modelo.train()
        logits = modelo(entradas)
        if logits.shape != (2, 2) or not torch.isfinite(logits).all():
            raise ValueError(f"Saída inválida no teste sintético de {nome}.")
        perda = torch.nn.functional.cross_entropy(logits, rotulos)
        perda.backward()
        gradientes = [p.grad for p in modelo.parameters() if p.requires_grad]
        if (not torch.isfinite(perda) or entradas.grad is None or not torch.isfinite(entradas.grad).all()
                or any(g is None or not torch.isfinite(g).all() for g in gradientes)
                or not any(bool(g.abs().max() > 0) for g in gradientes)):
            raise ValueError(f"Gradientes ausentes, não finitos ou todos nulos: {nome}.")
        modelo.eval()
        with torch.inference_mode():
            saida = modelo(entradas.detach())
            if not torch.isfinite(saida).all():
                raise ValueError(f"Inferência inválida: {nome}.")
        if dispositivo.type == "cuda":
            torch.cuda.synchronize()
        registro["forward_backward_inferencia"] = "aprovado"
        relatorio[nome] = registro
        del modelo, entradas, logits, perda, gradientes, saida
    return relatorio


def verificar_preparacao(configuracao: dict) -> dict:
    celulas = gerar_celulas(configuracao)
    if len(celulas) != 1:
        raise ValueError("A preparação do piloto requer exatamente uma célula; use treino_piloto_nvidia.json.")
    celula = celulas[0]
    # Fixar opções antes da primeira operação CUDA, inclusive consulta de ambiente.
    fixar_seed(celula["seed"])
    registro_ambiente = ambiente()
    if configuracao["dispositivo"] == "cuda" and not registro_ambiente["cuda_disponivel"]:
        raise RuntimeError("CUDA indisponível. Este computador/ambiente não pode executar o piloto NVIDIA.")
    dataset, blocos, matriz, normalizador, _ = carregar_dados(configuracao, celula)
    passos = int(blocos["treino"].iloc[0]["indice_contexto_fim"] - blocos["treino"].iloc[0]["indice_contexto_inicio"] + 1)
    return {"configuracao": configuracao, "celula": celula, "ambiente": registro_ambiente,
            "sha256_codigo": assinatura_codigo(), "sha256_manifesto_dataset": dataset.resumo_manifesto,
            "contagens": {b: len(q) for b, q in blocos.items()}, "normalizador": normalizador,
            "modelos": verificar_modelos(configuracao, matriz.shape[1], passos),
            "treinamento_executado": False, "escopo": "Qualificação técnica de uma célula, sem ajuste de pesos."}


def conferir_checkpoint(salvo: dict, historico: dict, resumo: dict) -> None:
    epocas = historico["epocas"]
    if not epocas or [e["epoca"] for e in epocas] != list(range(1, len(epocas) + 1)):
        raise ValueError("Histórico de épocas incompleto/desordenado.")
    if any(not all(math.isfinite(e[k]) for k in ("loss_treino", "ba_validacao", "f1_macro_validacao"))
           or not 0 <= e["ba_validacao"] <= 1 or not 0 <= e["f1_macro_validacao"] <= 1
           or e["loss_treino"] < 0 for e in epocas):
        raise ValueError("Histórico contém métricas inválidas.")
    melhor = max(epocas, key=lambda e: e["ba_validacao"])
    if (salvo["epoca"] != melhor["epoca"] or salvo["ba_validacao"] != melhor["ba_validacao"]
            or resumo["melhor_epoca"] != melhor["epoca"]
            or resumo["melhor_ba_validacao"] != melhor["ba_validacao"]
            or resumo["epocas_executadas"] != len(epocas)):
        raise ValueError("Checkpoint não corresponde à primeira melhor BA de validação.")
    melhor_ba, espera = -math.inf, 0
    for i, epoca in enumerate(epocas):
        if epoca["ba_validacao"] > melhor_ba:
            melhor_ba, espera = epoca["ba_validacao"], 0
        else:
            espera += 1
        if espera >= REGRAS_TREINO["paciencia"] and i != len(epocas) - 1:
            raise ValueError("Treino continuou após a parada antecipada.")
    if len(epocas) > REGRAS_TREINO["epocas_maximas"] or (len(epocas) < REGRAS_TREINO["epocas_maximas"] and espera < REGRAS_TREINO["paciencia"]):
        raise ValueError("Treino encerrado fora das regras de épocas/paciência.")


def verificar_checkpoints(pasta: Path) -> dict:
    """Reproduz probabilidades; não retreina e não procura um checkpoint melhor."""
    resultado, _ = auditar_execucao(pasta)
    if resultado["sha256_codigo"] != assinatura_codigo():
        raise ValueError("Código atual difere da execução. Use as fontes preservadas antes de reproduzir pesos.")
    c, celula = resultado["configuracao"], resultado["celula"]
    fixar_seed(celula["seed"])
    atual = ambiente()
    for chave in ("versoes", "cuda_pytorch", "cudnn", "gpu", "execucao_numerica", "fontes_backend"):
        if chave not in resultado["ambiente"] or resultado["ambiente"][chave] != atual[chave]:
            raise ValueError(f"Ambiente diverge do registrado: {chave}. Reproduza no ambiente do treino.")
    dataset, blocos, matriz, normalizador, indices = carregar_dados(c, celula)
    if dataset.resumo_manifesto != resultado["sha256_manifesto_dataset"]:
        raise ValueError("Dataset diverge da execução.")
    conferir_resumo(json.loads((pasta / "normalizador.json").read_text(encoding="utf-8")), normalizador, "normalizador")
    np.testing.assert_array_equal(np.load(pasta / "indices_ajuste_normalizador.npy", allow_pickle=False), indices)
    dispositivo = torch.device(c["dispositivo"])
    relatorio = {"execucao": resultado["id"], "diretorio": str(pasta.resolve()), "treinamento_executado": False,
                 "ambiente": atual, "tolerancia_probabilidades": {"rtol": 1e-5, "atol": 1e-6}, "modelos": {}}
    for nome in ("lstm", "mamba"):
        salvo = torch.load(pasta / nome / "melhor.pt", map_location=dispositivo, weights_only=True)
        historico = json.loads((pasta / nome / "historico.json").read_text(encoding="utf-8"))
        conferir_checkpoint(salvo, historico, resultado["modelos"][nome])
        for chave, esperado in (("configuracao", c), ("celula", celula), ("nome_modelo", nome), ("dimensao_entrada", matriz.shape[1])):
            if salvo[chave] != esperado:
                raise ValueError(f"Metadado divergente no checkpoint: {nome}/{chave}.")
        fixar_seed(celula["seed"])
        modelo = criar_modelo(nome, c, matriz.shape[1]).to(dispositivo)
        modelo.load_state_dict(salvo["modelo"], strict=True)
        relatorio["modelos"][nome] = {"epoca": salvo["epoca"], "blocos": {}}
        for bloco in ("validacao", "teste"):
            gravado = pd.read_parquet(pasta / f"previsoes_{nome}_{bloco}.parquet")
            pd.testing.assert_frame_equal(blocos[bloco][CHAVES].reset_index(drop=True), gravado[CHAVES].reset_index(drop=True))
            probabilidades = prever(modelo, DataLoader(JanelasTemporais(matriz, blocos[bloco]),
                                  batch_size=c["microbatch"], shuffle=False), dispositivo)
            np.testing.assert_allclose(probabilidades, gravado.probabilidade_alta.to_numpy(), rtol=1e-5, atol=1e-6)
            np.testing.assert_array_equal(probabilidades > 0.5, gravado.classe_prevista.to_numpy())
            relatorio["modelos"][nome]["blocos"][bloco] = {"n": len(probabilidades), "classes_identicas": True,
                "maior_diferenca_probabilidade": float(np.max(np.abs(probabilidades - gravado.probabilidade_alta.to_numpy())))}
        del modelo, salvo
    return relatorio
