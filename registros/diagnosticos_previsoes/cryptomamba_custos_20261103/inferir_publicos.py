"""Inferência dos dois checkpoints públicos, sem treinamento ou fallback CPU."""
import hashlib
import importlib.util
import json
from pathlib import Path
import platform

import numpy as np
import pandas as pd
import torch

PASTA = Path(__file__).resolve().parent


def carregar(nome, caminho):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    assert torch.cuda.is_available(), "Exige CUDA, sem fallback"
    torch.set_num_threads(1)
    torch.manual_seed(23)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    fonte = PASTA / "fontes_publicas"
    cm = carregar("cmamba_publico", fonte / "models/cmamba.py")
    dt = carregar("transform_publico", fonte / "data_utils/data_transforms.py")
    tr = carregar("trade_publico", fonte / "utils/trade.py")
    resultado = {"ambiente": {"python": platform.python_version(), "torch": torch.__version__,
                 "gpu": torch.cuda.get_device_name()}, "treinamentos": 0, "series": {}}
    for volume in (False, True):
        nome = "cmamba_v" if volume else "cmamba_nv"
        modelo = cm.CMamba(num_features=6 if volume else 5, hidden_dims=[14, 16, 32, 1],
                           d_states=64, layer_density=4).cuda().eval()
        ckpt = torch.load(fonte / f"checkpoints/{nome}.ckpt", map_location="cpu", weights_only=True)
        pesos = {k.removeprefix("model."): v for k, v in ckpt["state_dict"].items() if k.startswith("model.")}
        modelo.load_state_dict(pesos, strict=True)
        for parte in ("val", "test"):
            dados = pd.read_csv(fonte / f"data/2018-09-17_2024-09-16_86400/{parte}.csv", index_col=0)
            transformar = dt.DataTransform(is_train=False, use_volume=volume)
            # Exatamente CMambaDataset.__len__ e __getitem__, inclusive a exclusão terminal.
            amostras = [transformar(dados.iloc[i:i + 15]) for i in range(len(dados) - 15)]
            x = torch.stack([a["features"] for a in amostras])
            ts = np.array([a["Timestamp"].item() for a in amostras])
            alvos = np.array([a["Close"].item() for a in amostras])
            with torch.inference_mode():
                previsoes = np.concatenate([modelo(b.cuda()).reshape(-1).cpu().numpy() for b in x.split(32)])
                recarga = cm.CMamba(num_features=6 if volume else 5, hidden_dims=[14, 16, 32, 1],
                                   d_states=64, layer_density=4).cuda().eval()
                recarga.load_state_dict(pesos, strict=True)
                repetidas = np.concatenate([recarga(b.cuda()).reshape(-1).cpu().numpy() for b in x.split(32)])
                assert np.array_equal(previsoes, repetidas)
                del recarga
            anterior = np.array([dados.loc[dados.Timestamp == int(t - 86400), "Close"].iloc[0] for t in ts])
            saida = pd.DataFrame({"timestamp": ts, "preco_anterior": anterior, "alvo": alvos, "previsao": previsoes})
            saida.to_csv(PASTA / f"{nome}_{parte}_previsoes.csv", index=False)
            r = {"n": len(saida), "inicio_alvo_utc": pd.to_datetime(ts[0], unit="s", utc=True).isoformat(),
                 "fim_alvo_utc": pd.to_datetime(ts[-1], unit="s", utc=True).isoformat(),
                 "rmse": float(np.sqrt(np.mean((previsoes-alvos)**2))),
                 "mape": float(np.mean(np.abs((previsoes-alvos)/alvos))*100),
                 "recarga_exata": True, "epoca_checkpoint": ckpt["epoch"], "politicas": {}}
            for politica in ("vanilla", "smart", "smart_w_short", "no_strategy"):
                saldo, curva = tr.trade(dados, "Timestamp", ts, alvos, previsoes, mode=politica, risk=2)
                c = np.array(curva)
                dd = float(np.max(1-c/np.maximum.accumulate(c)))
                r["politicas"][politica] = {"saldo": float(saldo), "mdd_curva_publica": dd}
            resultado["series"][f"{nome}_{parte}"] = r
            print(nome, parte, json.dumps(r), flush=True)
        del modelo
    (PASTA / "reproducao_publica.json").write_text(json.dumps(resultado, indent=2), encoding="utf-8")
    arquivos = {str(p.relative_to(PASTA)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in PASTA.rglob("*") if p.is_file() and "__pycache__" not in p.parts}
    (PASTA / "manifesto_inferencia.json").write_text(json.dumps(arquivos, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
