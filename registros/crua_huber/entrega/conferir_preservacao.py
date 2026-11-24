"""Conferencia posterior de leitura; nao importa nem executa treinadores."""
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


RAIZ = Path(__file__).resolve().parents[3]
def ler(p):
    return json.loads(p.read_text(encoding="utf-8"))

def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()

def conferir(mapa, base):
    for nome, esperado in mapa.items():
        p = base / nome
        assert p.is_file(), f"Ausente: {p}"
        assert sha(p) == esperado, f"Divergencia: {p}"
    return len(mapa)

reg = RAIZ / "registros/crua_huber"
ponteiro = ler(reg / "execucao.json")
pasta = RAIZ / ponteiro["pasta"]
fechamento = ler(reg / "fechamento.json")
assert fechamento["situacao"] == "concluido_conferido"
assert sha(pasta / "congelamento.json") == ponteiro["congelamento_sha256"]
assert not ler(pasta / "processo.json")["ativo"]
assert not ler(pasta / "processo_publicacao.json")["ativo"]
fontes = ler(pasta / "congelamento.json")["contrato"]["fontes"]
contagens = {"fontes_checkout": conferir(fontes, RAIZ),
             "fontes_congeladas": conferir(fontes, pasta / "fontes")}
contagens["preservados"] = conferir(ler(reg / "preservacao_antes.json")["arquivos"], RAIZ)
pub = RAIZ / fechamento["publicacao"]
assert sha(pub / "manifesto.json") == fechamento["manifesto_sha256"]
contagens["publicados"] = conferir(ler(pub / "manifesto.json")["arquivos"], pub)
r = ler(pub / "resultados.json")
assert len(r["por_ajuste"]) == 128 and len(r["carteiras"]) == 792
seeds = [17, 42, 2026, 7, 123, 31415, 271828, 161803]
variantes = ["relativa_mse", "relativa_huber", "crua_mse", "crua_huber"]
assert set(r["por_ajuste"]) == {f"B{b}_{v}_{s}" for b in range(1, 5) for v in variantes for s in seeds}
origens, medias = {}, {}
contagens["artefatos_ajustes"] = 0
for chave, ajuste in r["por_ajuste"].items():
    tentativa = RAIZ / ajuste["tentativa_origem"]
    contagens["artefatos_ajustes"] += conferir(ler(tentativa / "conclusao.json")["arquivos"], tentativa)
    bloco = chave.split("_")[0]
    variante = chave[len(bloco) + 1:].rsplit("_", 1)[0]
    for parte in ["validacao", "teste"]:
        q = pd.read_parquet(tentativa / f"previsoes_{parte}.parquet")
        observado = q.drop(columns="previsao")
        if (bloco, parte) in origens:
            pd.testing.assert_frame_equal(observado, origens[bloco, parte])
        else:
            origens[bloco, parte] = observado
        erro = q.previsao.to_numpy() - q.alvo.to_numpy()
        mse = math.fsum(float(e) ** 2 for e in erro) / len(erro)
        mae = math.fsum(abs(float(e)) for e in erro) / len(erro)
        for metrica, valor in [("mse", mse), ("mae", mae)]:
            assert math.isclose(valor, ajuste["metricas"][parte][metrica], rel_tol=1e-12, abs_tol=1e-15)
            medias.setdefault((parte, variante, metrica), []).append(valor)
for (parte, variante, metrica), valores in medias.items():
    assert len(valores) == 32
    assert math.isclose(math.fsum(valores)/32, r["medias_globais"][parte][variante][metrica], rel_tol=1e-12, abs_tol=1e-15)
controles = list((pasta / "controles").glob("*/tentativa_001/conclusao.json"))
assert len(controles) == 1
contagens["artefatos_controle"] = conferir(ler(controles[0])["arquivos"], controles[0].parent)
controle = ler(pasta / "controle_reproducao.json")
assert controle["mesma_epoca"]
assert max(controle["maxima_diferenca_previsoes"].values()) <= controle["limites"]["diferenca_absoluta_previsao"]
assert controle["diferenca_relativa_mse_validacao"] <= controle["limites"]["diferenca_relativa_mse"]
instante = datetime.now(timezone.utc)
saida = reg / "entrega" / instante.strftime("conferencia_%Y%m%dT%H%M%S%fZ.json")
recibo = {"utc": instante.isoformat(), "situacao": "conferido", "execucao": ponteiro,
          "verificador_sha256": sha(Path(__file__)), "contagens": contagens,
          "metricas_recalculadas": "MSE/MAE de validacao/teste dos 128 ajustes e medias das quatro variantes",
          "mesmas_origens_alvos": True, "controle_reproducao_conferido": True,
          "novos_treinamentos": 0, "novas_simulacoes": 0,
          "medias_globais": r["medias_globais"], "criterio_primario": r["criterio_primario"],
          "limites": ["Conferencia local de integridade, nao backup externo.",
                      "Sem nova inferencia CUDA, bootstrap ou reconstrucao de carteiras; recibos originais preservados.",
                      "2024/2025 retrospectivos; nenhuma promocao ou novo ciclo autorizado por este recibo."]}
with saida.open("x", encoding="utf-8") as f:
    json.dump(recibo, f, ensure_ascii=False, indent=2)
print(json.dumps({"recibo": str(saida), "contagens": contagens, "situacao": "conferido"}, ensure_ascii=False))
