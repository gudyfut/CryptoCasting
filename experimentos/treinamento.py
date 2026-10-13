"""Treino supervisionado comum às duas redes; somente chamado pelo pesquisador."""

from __future__ import annotations

import os
import random
import time
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader

from modelo.lstm_modelo import LSTMClassificador
from modelo.mamba_modelo import MambaClassificador
from .avaliacao import calcular_metricas
from .dados import JanelasTemporais
from .registro import gravar_json

REGRAS_TREINO = {"otimizador": "AdamW", "taxa_aprendizado": 0.0002, "weight_decay": 0.001,
                "batch_efetivo": 32, "epocas_maximas": 100, "paciencia": 10, "clipping": 1.0,
                "perda": "cross_entropy_sem_pesos", "limiar_alta": 0.5,
                "selecao": "BA_validacao; empate mantém checkpoint mais antigo", "scheduler": None}


def fixar_seed(seed: int) -> None:
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    # Kernels oficiais podem não oferecer determinismo estrito; registrar a limitação.
    torch.use_deterministic_algorithms(True, warn_only=True)


def criar_modelo(nome: str, configuracao: dict, dimensao: int):
    if nome == "lstm":
        return LSTMClassificador(dimensao_entrada=dimensao, largura=configuracao["largura_lstm"])
    if nome != "mamba":
        raise ValueError("Modelo desconhecido.")
    return MambaClassificador(d_input=dimensao, d_model=configuracao["largura_mamba"], n_layers=2,
                             d_state=16, d_conv=4, expand=2, dropout=0.1,
                             pooling="last", backend=configuracao["backend_mamba"])


def prever(modelo, carregador, dispositivo: torch.device) -> np.ndarray:
    modelo.eval()
    probabilidades = []
    with torch.inference_mode():
        for entradas, _ in carregador:
            logits = modelo(entradas.to(dispositivo))
            if not torch.isfinite(logits).all():
                raise ValueError("Logits não finitos durante avaliação.")
            probabilidades.append(torch.softmax(logits, dim=1)[:, 1].cpu().numpy())
    return np.concatenate(probabilidades)


def quadro_previsoes(amostras: pd.DataFrame, probabilidades: np.ndarray) -> pd.DataFrame:
    probabilidades = np.asarray(probabilidades)
    if probabilidades.ndim != 1 or not np.isfinite(probabilidades).all() or ((probabilidades < 0) | (probabilidades > 1)).any():
        raise ValueError("Probabilidades devem ser um vetor finito entre zero e um.")
    if len(amostras) != len(probabilidades):
        raise ValueError("Previsões não correspondem às amostras em ordem.")
    colunas = ["par", "granularidade", "tarefa", "contexto_dias", "origem_utc", "alvo_fim_utc",
               "classe_alta", "empate", "retorno_futuro"]
    quadro = amostras[colunas].copy()
    quadro["probabilidade_alta"] = probabilidades
    quadro["classe_prevista"] = (probabilidades > 0.5).astype(np.int8)
    return quadro


def treinar_modelo(nome: str, configuracao: dict, celula: dict, matriz: np.ndarray,
                   blocos: dict, destino: Path) -> tuple[dict, dict]:
    fixar_seed(celula["seed"])
    dispositivo = torch.device(configuracao["dispositivo"])
    if dispositivo.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA solicitada e indisponível; escolha CPU/pytorch explicitamente.")
    destino.mkdir(parents=True, exist_ok=True)
    modelo = criar_modelo(nome, configuracao, matriz.shape[1]).to(dispositivo)
    otimizador = torch.optim.AdamW(modelo.parameters(), lr=0.0002, weight_decay=0.001)
    gerador = torch.Generator().manual_seed(celula["seed"])
    # Batch lógico 32 garante a mesma composição mesmo quando microbatch muda.
    carregadores = {bloco: DataLoader(JanelasTemporais(matriz, quadro), batch_size=32 if bloco == "treino" else configuracao["microbatch"],
                                     shuffle=(bloco == "treino"), num_workers=0, drop_last=False,
                                     generator=gerador if bloco == "treino" else None)
                    for bloco, quadro in blocos.items()}
    melhor_ba, melhor_epoca, espera = -float("inf"), 0, 0
    historico = []
    inicio = time.perf_counter()
    if dispositivo.type == "cuda":
        torch.cuda.reset_peak_memory_stats(dispositivo)
    for epoca in range(1, 101):
        modelo.train()
        perda_total, quantidade = 0.0, 0
        for entradas, rotulos in carregadores["treino"]:
            otimizador.zero_grad(set_to_none=True)
            tamanho = len(rotulos)
            for comeco in range(0, tamanho, configuracao["microbatch"]):
                fim = min(comeco + configuracao["microbatch"], tamanho)
                logits = modelo(entradas[comeco:fim].to(dispositivo))
                perda = nn.functional.cross_entropy(logits, rotulos[comeco:fim].to(dispositivo), reduction="sum")
                if not torch.isfinite(perda):
                    raise ValueError("Loss não finita; execução interrompida.")
                (perda / tamanho).backward()
                perda_total += float(perda.detach().cpu())
            nn.utils.clip_grad_norm_(modelo.parameters(), max_norm=1.0, error_if_nonfinite=True)
            otimizador.step()
            quantidade += tamanho
        previsao_validacao = quadro_previsoes(blocos["validacao"], prever(modelo, carregadores["validacao"], dispositivo))
        metricas = calcular_metricas(previsao_validacao)
        ba = metricas["balanced_accuracy"]
        if ba is None:
            raise ValueError("BA de validação indisponível: não selecionar checkpoint arbitrário.")
        historico.append({"epoca": epoca, "loss_treino": perda_total / quantidade,
                          "ba_validacao": ba, "f1_macro_validacao": metricas["f1_macro"]})
        if ba > melhor_ba:
            melhor_ba, melhor_epoca, espera = ba, epoca, 0
            temporario = destino / "melhor.pt.tmp"
            torch.save({"modelo": modelo.state_dict(), "otimizador": otimizador.state_dict(),
                        "epoca": epoca, "ba_validacao": ba, "nome_modelo": nome,
                        "celula": celula, "configuracao": configuracao,
                        "dimensao_entrada": matriz.shape[1]}, temporario)
            temporario.replace(destino / "melhor.pt")
        else:
            espera += 1
        gravar_json(destino / "historico.json", {"epocas": historico})
        print(f"{celula['par']} {celula['fold']} {nome} época {epoca}: loss={perda_total/quantidade:.5f} BA_val={ba:.4f}", flush=True)
        if espera >= 10:
            break
    # Nunca consultar o bloco teste durante a seleção da época.
    salvo = torch.load(destino / "melhor.pt", map_location=dispositivo, weights_only=True)
    modelo.load_state_dict(salvo["modelo"])
    previsoes = {bloco: quadro_previsoes(blocos[bloco], prever(modelo, carregadores[bloco], dispositivo))
                for bloco in ("validacao", "teste")}
    resumo = {"modelo": nome, "backend": getattr(modelo, "backend", "torch.nn.LSTM"),
              "parametros": sum(p.numel() for p in modelo.parameters()), "epocas_executadas": len(historico),
              "melhor_epoca": melhor_epoca, "melhor_ba_validacao": melhor_ba,
              "segundos_treino_e_avaliacao": time.perf_counter() - inicio,
              "pico_memoria_cuda_bytes": torch.cuda.max_memory_allocated(dispositivo) if dispositivo.type == "cuda" else None,
              "determinismo": "seeds fixas; deterministic_algorithms warn_only; kernels podem não ser estritamente determinísticos",
              "regras_treino": REGRAS_TREINO, "microbatch": configuracao["microbatch"]}
    del modelo, otimizador, salvo
    if dispositivo.type == "cuda":
        torch.cuda.empty_cache()
    return resumo, previsoes
