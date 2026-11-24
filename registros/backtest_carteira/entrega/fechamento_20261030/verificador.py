"""Conferência posterior, sem executar estratégias, inferência ou treinamento.

Uso: python manutencao/conferir_backtest_carteira.py --saida <pasta nova>
Os recibos publicados e os artefatos da execução permanecem somente leitura.
"""
import argparse
import hashlib
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]


def ler(p):
    return json.loads(p.read_text(encoding="utf-8"))


def hash_arquivo(p):
    h = hashlib.sha256()
    with p.open("rb") as arq:
        for bloco in iter(lambda: arq.read(2**20), b""):
            h.update(bloco)
    return h.hexdigest()


def conferir_hashes(base, mapa):
    for nome, esperado in mapa.items():
        assert hash_arquivo(base / nome) == esperado, nome
    return len(mapa)


def igual(a, b):
    assert math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-10), (a, b)


def executar(dest):
    dest = dest.resolve()
    assert dest.is_relative_to(RAIZ / "registros/backtest_carteira/entrega")
    dest.mkdir(parents=True, exist_ok=False)
    shutil.copy2(__file__, dest / "verificador.py")
    ptr = ler(RAIZ / "registros/backtest_carteira/execucao_atual.json")
    pasta = RAIZ / ptr["pasta"]
    assert hash_arquivo(pasta / "congelamento.json") == ptr["congelamento_sha256"]
    f = ler(pasta / "congelamento.json")["contrato"]
    assert ler(pasta / "progresso.json") == {
        "status": "concluido", "concluidas": 369, "total": 369,
        "utc": ler(pasta / "progresso.json")["utc"]}
    assert not ler(pasta / "processo.json")["ativo"]
    quant = {
        "fontes_atuais": conferir_hashes(RAIZ, f["fontes"]),
        "fontes_copiadas": conferir_hashes(pasta / "fontes", f["fontes"]),
        "insumos": conferir_hashes(RAIZ, f["insumos"]),
        "anteriores_preservados": conferir_hashes(RAIZ, ler(
            RAIZ / "registros/backtest_carteira/revisao_loader/preservacao_antes.json")["arquivos"]),
        "publicacao": conferir_hashes(pasta / "resultados", ler(
            pasta / "resultados/manifesto.json")["arquivos"]),
        "figuras_originais": conferir_hashes(RAIZ, ler(
            pasta / "resultados/figuras.json")["arquivos"]),
    }
    r = ler(pasta / "resultados/comparacao.json")
    esperado = {"/".join(job[k] for k in ("parte", "cenario", "politica", "serie"))
                for job in f["grade"]}
    assert set(r["por_simulacao"]) == esperado and len(esperado) == 369
    encontrados = {str(p.parent.relative_to(pasta / "resultados")).replace("\\", "/")
                   for p in (pasta / "resultados").rglob("verificacao.json")}
    assert encontrados == esperado
    diarios = {}
    recusas = 0
    for chave in sorted(esperado):
        p = pasta / "resultados" / chave
        conferir_hashes(p, ler(p / "manifesto.json")["arquivos"])
        s = ler(p / "resumo.json")
        assert s == r["por_simulacao"][chave]
        assert ler(p / "verificacao.json")["status"] == "conferido"
        o = ler(p / "ordens.json")
        completos = [x for x in o if x["status"] == "executada"]
        igual(sum(x["comissao_usdt"] for x in completos), s["comissoes_usdt"])
        igual(sum(x["slippage_usdt"] for x in completos), s["slippage_usdt"])
        assert len(completos) == s["ordens_executadas"]
        assert all(x["caixa_depois"] >= -1e-8 and x["btc_depois"] >= -1e-12 for x in o)
        igual(s["caixa_final"] + s["valor_residual_usdt"], s["capital_final"])
        igual(s["capital_final"] / s["capital_inicial"] - 1, s["retorno_liquido"])
        d = pd.read_parquet(p / "diarios.parquet")
        assert len(d) == (365 if chave.startswith("validacao/") else 364)
        assert (pd.DatetimeIndex(d.origem_utc).hour == 0).all()
        calculados = np.log(d.capital_fim.to_numpy() / d.capital_inicio.to_numpy())
        np.testing.assert_allclose(calculados, d.retorno_log, rtol=1e-10, atol=1e-12)
        np.testing.assert_allclose(d.capital_fim.iloc[:-1], d.capital_inicio.iloc[1:], rtol=1e-10)
        igual(calculados.sum(), math.log(s["capital_final"] / 10000))
        curva = pd.read_parquet(p / "curva.parquet")
        igual(curva.capital.iloc[-1], s["capital_final"])
        assert 0 <= s["exposicao_media"] <= 1 + 1e-10
        if "/caixa/" in chave:
            igual(s["capital_final"], 10000)
            assert s["ordens_executadas"] == 0
        recusas += s["ordens_recusadas_filtro"]
        diarios[chave] = d
    ss = f["configuracao"]["seeds"]
    grupos = {"mamba16_seis": [f"estado16_{s}" for s in ss],
              "mamba16_tres": [f"estado16_{s}" for s in ss[:3]],
              "lstm_tres": [f"lstm_{s}" for s in ss[:3]],
              "cryptomamba_seis": [f"cryptomamba_{s}" for s in ss],
              "cryptomamba_tres": [f"cryptomamba_{s}" for s in ss[:3]],
              "naive": ["naive"], "arima": ["arima"]}
    for parte, custos in r["medias"].items():
        for custo, politicas in custos.items():
            for pol, modelos in politicas.items():
                if pol == "benchmarks":
                    continue
                for grupo, resumo in modelos.items():
                    vals = [r["por_simulacao"][f"{parte}/{custo}/{pol}/{k}"]
                            for k in grupos[grupo]]
                    for campo in ("capital_final", "retorno_liquido", "drawdown_minuto_close",
                                  "exposicao_media", "ordens_executadas", "comissoes_usdt",
                                  "slippage_usdt"):
                        igual(sum(v[campo] for v in vals) / len(vals), resumo[campo])
                    assert sum(v["retorno_liquido"] > 0 for v in vals) == resumo["seeds_lucrativas"]
    principal = np.mean([diarios[f"teste/base/smart/estado16_{s}"].retorno_log for s in ss], axis=0)
    vies = np.mean([diarios[f"teste/base/smart_constante/estado16_{s}"].retorno_log for s in ss], axis=0)
    bases = {"vies_validacao": vies,
             "comprar_manter": diarios["teste/base/comprar_manter/benchmark"].retorno_log.to_numpy(),
             "caixa": np.zeros(len(principal))}
    contrastes = {}
    for nome, base in bases.items():
        diferenca = principal - base
        rng = np.random.default_rng(20261030)
        amostras = []
        for _ in range(2000):
            inicios = rng.integers(0, len(diferenca), size=math.ceil(len(diferenca) / 14))
            indices = np.concatenate([(np.arange(14) + inicio) % len(diferenca)
                                      for inicio in inicios])[:len(diferenca)]
            amostras.append(float(diferenca[indices].mean()))
        intervalo = np.quantile(amostras, [.025, .975])
        publicado = r["contrastes"][f"smart_mamba16_menos_{nome}"]
        igual(diferenca.mean(), publicado["diferenca_media_log_diaria"])
        np.testing.assert_allclose(intervalo, publicado["ic95_log_diario"], atol=1e-12)
        contrastes[nome] = {"diferenca_log_diaria": float(diferenca.mean()),
                            "ic95": intervalo.tolist()}
    anterior = ler(RAIZ / "registros/backtest_carteira/execucao.json")
    assert anterior["id"] == "b9fce5ae0300ce91ba69"
    assert ler(RAIZ / anterior["pasta"] / "progresso.json")["concluidas"] == 0
    assert hash_arquivo(RAIZ / anterior["pasta"] / "congelamento.json") == anterior["congelamento_sha256"]
    shutil.copy2(RAIZ / "docs/resultados_backtest_carteira.md", dest / "relatorio_automatico_preservado.md")
    recibo = {"utc": datetime.now(timezone.utc).isoformat(), "situacao": "conferido",
              "execucao": ptr, "contagens": quant, "simulacoes": len(esperado),
              "recusas_filtro": recusas, "contrastes_independentes": contrastes,
              "treinamentos_ou_reexecucoes": 0,
              "anterior_interrompido_preservado": anterior,
              "resultado_sha256": hash_arquivo(pasta / "resultados/comparacao.json"),
              "verificador_sha256": hash_arquivo(dest / "verificador.py"),
              "limite": "Conferência adicional de hashes, saldos, métricas e contrastes; não certifica fills reais ou lucro futuro."}
    (dest / "conferencia.json").write_text(json.dumps(recibo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(recibo, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    executar(parser.parse_args().saida)
