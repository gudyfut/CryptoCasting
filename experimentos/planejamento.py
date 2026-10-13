"""Tabelas do protocolo geradas sem ler dados de mercado ou executar modelos."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pre_processamento.contrato import PARES, GRANULARIDADES, candles_por_contexto
from pre_processamento.folds import FOLDS


def construir_plano() -> dict:
    resolucoes = []
    for granularidade in GRANULARIDADES:
        por_dia = candles_por_contexto(granularidade, 1)
        resolucoes.append({"granularidade": granularidade, "minutos": 1440 // por_dia,
                          "janela_7d": 7 * por_dia, "janela_14d": 14 * por_dia,
                          "horizonte_24h_candles": por_dia})
    etapas = [
        {"id": "E0", "nome": "Referência inicial", "contexto": "7 dias", "features": "OHLCV (5)",
         "normalizador": "StandardScaler", "larguras": "Mamba 32 / LSTM 32",
         "decisao": "Registrar as 16 células nos quatro folds D1–D4."},
        {"id": "E1", "nome": "Sensibilidade ao contexto", "contexto": "14 dias", "features": "OHLCV (5)",
         "normalizador": "StandardScaler", "larguras": "Mamba 32 / LSTM 32",
         "decisao": "Comparar com E0. Publicar 7 e 14 dias separadamente; os próximos passos usam 7 dias."},
        {"id": "E2", "nome": "Representação", "contexto": "7 dias", "features": "OHLCV + indicadores (8)",
         "normalizador": "StandardScaler", "larguras": "Mamba 32 / LSTM 32",
         "decisao": "Comparar com E0. Escolher features pela BA global de desenvolvimento do Mamba e aplicá-las a ambas as redes."},
        {"id": "E3", "nome": "Normalização", "contexto": "7 dias", "features": "Escolhidas em E2",
         "normalizador": "MinMaxScaler", "larguras": "Mamba 32 / LSTM 32",
         "decisao": "Comparar com StandardScaler nas mesmas features. Escolher pela BA global do Mamba; aplicar a ambas."},
        {"id": "E4", "nome": "Largura das redes", "contexto": "7 dias", "features": "Escolhidas em E2",
         "normalizador": "Escolhido em E3", "larguras": "Mamba 64 / LSTM 64",
         "decisao": "Comparar cada rede à sua largura 32. Escolher cada largura pela própria BA global; empate favorece 32."},
    ]
    return {"protocolo": "1.6", "pares": list(PARES), "resolucoes": resolucoes,
            "features": {"ohlcv": 5, "ampliadas": 8}, "contextos_dias": [7, 14],
            "seeds_desenvolvimento": [42], "seeds_finais": [17, 42, 2026],
            "folds": [f.__dict__ for f in FOLDS], "etapas": etapas,
            "orcamento": {"celulas_por_contexto": 16, "treinos_por_rede_por_etapa": 64,
                           "treinos_neurais_por_etapa": 128, "maximo_desenvolvimento": 640,
                           "principal_7d_final": 768, "principal_14d_final": 768,
                           "complementar_adicional_final": 576, "total_final": 2112},
            "final_liberado": False}


def exemplo_temporal(granularidade: str, contexto_dias: int, tarefa: str = "principal") -> dict:
    plano = construir_plano()
    if contexto_dias not in (7, 14) or tarefa not in ("principal", "proximo_candle") or (tarefa == "proximo_candle" and contexto_dias != 7):
        raise ValueError("Exemplo fora da grade do protocolo.")
    resolucao = next(r for r in plano["resolucoes"] if r["granularidade"] == granularidade)
    origem = datetime(2023, 1, 15, tzinfo=timezone.utc)
    passo = timedelta(minutes=resolucao["minutos"])
    return {"contexto_inicio_utc": (origem - timedelta(days=contexto_dias)).isoformat(),
            "ultimo_candle_abertura_utc": (origem - passo).isoformat(),
            "origem_utc": origem.isoformat(),
            "alvo_fim_utc": (origem + (timedelta(days=1) if tarefa == "principal" else passo)).isoformat()}


def documento_matriz(plano: dict) -> str:
    linhas = ["# Matriz de configurações e períodos", "",
              "Gerado a partir dos contratos Python por `python scripts/atualizar_plano_experimental.py`. Não editar esta tabela manualmente.", "",
              "Protocolo 1.6. Planejamento, sem treinamento ou resultados novos. A execução final continua bloqueada.", "",
              "## 1. Moedas, resolução e janelas", "",
              "Cada linha representa um modelo separado por arquitetura, contexto, horizonte, fold e seed. As moedas não são misturadas em um único treinamento.", "",
              "| Par | Candle de entrada | Janela de 7 dias | Janela de 14 dias | Alvo principal: 24h | Alvo complementar |",
              "|---|---|---:|---:|---|---|"]
    for par in plano["pares"]:
        for r in plano["resolucoes"]:
            linhas.append(f"| {par} | {r['granularidade']} | {r['janela_7d']} candles | {r['janela_14d']} candles | {r['horizonte_24h_candles']} candle(s) | {r['granularidade']} |")
    linhas += ["", "Na tarefa principal, há uma origem por dia elegível às 00:00 UTC em todas as resoluções. Na complementar, há uma origem a cada candle completo, contexto fixo de 7 dias. A complementar diária reutiliza a principal.", "",
               "Uma janela é um exemplo: 672 candles em 15m representam 7 dias de entrada, não 672 exemplos. Tensor por exemplo: `[candles, 5]` (OHLCV) ou `[candles, 8]` (indicadores). O batch efetivo tem até 32 exemplos; o último pode ser menor.", "",
               "## 2. Timestamp de abertura, origem e alvo", "",
               "Exemplo didático: BTCUSDT, entrada 15m, contexto de 7 dias, origem em 15/01/2023 00:00 UTC. Essas datas ilustram alinhamento; não certificam elegibilidade nos dados reais.", "",
               "| Campo | Instante UTC | Significado |", "|---|---|---|"]
    exemplo = exemplo_temporal("15m", 7)
    explicacoes = {"contexto_inicio_utc": "Primeiro candle abre em 08/01; só o passado integra a entrada.",
                   "ultimo_candle_abertura_utc": "Último candle de entrada abre 15 minutos antes da origem.",
                   "origem_utc": "O último candle acabou; aqui é emitida a previsão.",
                   "alvo_fim_utc": "Fechamento 24 horas depois, usado somente como desfecho."}
    linhas += [f"| {chave} | {valor} | {explicacoes[chave]} |" for chave, valor in exemplo.items()]
    linhas += ["", "Alvo binário: `close(alvo) > close(origem)` significa alta; baixa ou empate significa não alta. Na complementar de 15m, o alvo desse exemplo é 15/01/2023 00:15 UTC.", "",
               "## 3. Sequência de configurações de desenvolvimento", "",
               "Todas as etapas abaixo usam horizonte de 24h, quatro pares, quatro resoluções, D1–D4 e seed 42. São comparações sequenciais de um fator por vez, não uma busca de todas as combinações possíveis.", "",
               "| Etapa | Contexto | Entradas | Scaler | Larguras | Decisão |", "|---|---|---|---|---|---|"]
    linhas += [f"| {e['id']} — {e['nome']} | {e['contexto']} | {e['features']} | {e['normalizador']} | {e['larguras']} | {e['decisao']} |" for e in plano["etapas"]]
    linhas += ["", "BA global: média com pesos iguais sobre os quatro ativos, quatro resoluções e quatro folds. Só concluir uma escolha após obter cobertura completa. Empates favorecem a opção inicial. A seleção final pode combinar Mamba 32 com LSTM 64, ou vice-versa, sem escolher por moeda/candle.", "",
               "As decisões de features e normalização são compartilhadas; as larguras são próprias de cada arquitetura. O AR(1) mantém a especificação fixa e não recebe as janelas/features das redes.", "",
               "O piloto CPU diário/D1 verifica funcionamento; não cobre a matriz de desenvolvimento. Não agregar backends/hardware diferentes na escolha global. Para reaproveitar o piloto na grade, configuração, dados, código, protocolo e ambiente precisam coincidir.", "",
               "## 4. Períodos dos folds", "",
               "Intervalos UTC `[início, fim)`: o fim é exclusivo. Além disso, remover rótulos cujo alvo termine no limite ou depois dele. Contexto de validação/teste pode usar passado anterior ao início do bloco.", "",
               "| Fold | Fase | Treino | Validação | Avaliação |", "|---|---|---|---|---|"]
    for f in plano["folds"]:
        linhas.append(f"| {f['nome']} | {f['tipo']} | [2021-01-01, {f['fim_treino']}) | [{f['fim_treino']}, {f['fim_validacao']}) | [{f['fim_validacao']}, {f['fim_teste']}) |")
    linhas += ["", "D1–D4 permitem desenvolvimento. F1–F8 exigem congelamento prévio e declaração de exposição aos resultados antigos; suas seeds planejadas são 17, 42 e 2026. Datas de início são limites de calendário: contexto, aquecimento, lacunas e purga reduzem a quantidade efetiva de amostras.", "",
               "## 5. Orçamento", "",
               "| Escopo | Cálculo | Treinos neurais (duas redes) |", "|---|---|---:|",
               "| Uma etapa de desenvolvimento | 4 pares × 4 resoluções × 4 folds × 1 seed × 2 redes | 128 |",
               "| Até cinco etapas | 128 × 5 | 640 |",
               "| Final: 24h / 7 dias | 4 × 4 × 8 × 3 × 2 | 768 |",
               "| Final: 24h / 14 dias | 4 × 4 × 8 × 3 × 2 | 768 |",
               "| Final: próximo candle, somente 15m/1h/4h adicionais | 4 × 3 × 8 × 3 × 2 | 576 |",
               "| Total final | 768 + 768 + 576 | 2.112 |", "",
               "Contagens planejadas, sem estimativa de duração medida. AR(1) determinístico é adicional e não é multiplicado por seeds, features ou larguras. O orçamento pode ser revisto antes dos scores finais, com justificativa registrada no protocolo.", ""]
    return "\n".join(linhas)
