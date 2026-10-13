"""Diagnóstico descritivo do checkpoint existente; não treina nem escolhe limiar."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import torch
from sklearn.metrics import balanced_accuracy_score, log_loss
from torch.utils.data import DataLoader

from experimentos.auditoria import auditar_execucao
from experimentos.configuracao import RAIZ
from experimentos.dados import DatasetProcessado, JanelasTemporais, preparar_entradas
from experimentos.treinamento import criar_modelo, fixar_seed, prever


def diagnosticar(pasta: Path) -> dict:
    resultado, _ = auditar_execucao(pasta)
    fontes = json.loads((pasta / "codigo_fonte.json").read_text(encoding="utf-8"))
    for relativo, conteudo in fontes.items():
        caminho = (RAIZ / relativo).resolve()
        if not caminho.is_relative_to(RAIZ) or caminho.read_text(encoding="utf-8") != conteudo:
            raise ValueError("Código atual diverge do snapshot; diagnostique com as fontes da execução.")
    c, celula = resultado["configuracao"], resultado["celula"]
    if c["backend_mamba"] != "pytorch" or c["dispositivo"] != "cpu":
        raise ValueError("Este diagnóstico foi delimitado ao piloto PyTorch/CPU.")
    raiz_dataset = Path(c["dataset"])
    candles, blocos = DatasetProcessado(raiz_dataset if raiz_dataset.is_absolute() else RAIZ / raiz_dataset).carregar(celula)
    matriz, _, _ = preparar_entradas(candles, blocos, c["features"], c["normalizador"])
    saida = {"execucao": resultado["id"], "treinamento_adicional": False,
             "uso": "Pós-hoc descritivo; não selecionar época, limiar ou configuração.", "modelos": {}}
    for nome in ("lstm", "mamba"):
        fixar_seed(celula["seed"])
        modelo = criar_modelo(nome, c, matriz.shape[1])
        if nome == "mamba":
            saida["softplus_bias_dt_inicial"] = [
                {"min": float(torch.nn.functional.softplus(camada.dt_proj.bias).min().detach()),
                 "max": float(torch.nn.functional.softplus(camada.dt_proj.bias).max().detach())}
                for camada in modelo.layers
            ]
        salvo = torch.load(pasta / nome / "melhor.pt", map_location="cpu", weights_only=True)
        modelo.load_state_dict(salvo["modelo"])
        diagnosticos = {}
        for bloco, amostras in blocos.items():
            janelas = JanelasTemporais(matriz, amostras)
            probabilidades = prever(modelo, DataLoader(janelas, batch_size=c["microbatch"], shuffle=False), torch.device("cpu"))
            reais = amostras.classe_alta.to_numpy()
            entradas_finais = np.stack([janelas[i][0][-1].numpy() for i in range(len(janelas))])
            diagnosticos[bloco] = {
                "n": len(amostras), "altas_reais": int(reais.sum()),
                "altas_previstas": int((probabilidades > .5).sum()),
                "ba_checkpoint": float(balanced_accuracy_score(reais, probabilidades > .5)),
                "cross_entropy_checkpoint": float(log_loss(reais, probabilidades, labels=[0, 1])),
                "quantis_probabilidade_alta": dict(zip(("min", "q25", "mediana", "q75", "max"), np.quantile(probabilidades, [0, .25, .5, .75, 1]).tolist())),
                "probabilidades_entre_49_e_51_porcento": int((np.abs(probabilidades - .5) <= .01).sum()),
                "media_entrada_ultimo_candle_normalizado": entradas_finais.mean(axis=0).tolist(),
                "features": resultado["features"],
            }
        saida["modelos"][nome] = diagnosticos
    return saida


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execucao", type=Path, required=True)
    parser.add_argument("--saida", type=Path, required=True)
    opcoes = parser.parse_args()
    if opcoes.saida.exists():
        raise FileExistsError("Preserve o diagnóstico anterior; use outro destino.")
    resultado = diagnosticar(opcoes.execucao)
    opcoes.saida.parent.mkdir(parents=True, exist_ok=True)
    with opcoes.saida.open("x", encoding="utf-8") as arquivo:
        json.dump(resultado, arquivo, ensure_ascii=False, indent=2, allow_nan=False)
        arquivo.write("\n")
    print(json.dumps(resultado, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
