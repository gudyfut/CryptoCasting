# Entrega 2 — plano de implementação do pipeline de coleta

**Período do cronograma:** 14/09–20/09  
**Resultado esperado:** dataset bruto reproduzível e script de coleta funcional.  
**Estado:** planejamento; a coleta ainda não foi executada.

## 1. Objetivo e limite da entrega

Implementar uma coleta reproduzível dos arquivos históricos de klines da Binance Spot, preservando os arquivos originais e produzindo evidências suficientes para verificar procedência, integridade e cobertura temporal.

Esta entrega termina nos dados brutos auditados. Ela não deve agregar candles, calcular indicadores, montar janelas, normalizar entradas, gerar rótulos, executar baselines ou treinar o Mamba. Essas responsabilidades pertencem às entregas seguintes.

## 2. Contrato de coleta

| Item | Definição |
|---|---|
| Fonte | Binance Public Data, mercado Spot |
| Pares | `BTCUSDT`, `ETHUSDT` e `XRPUSDT` |
| Intervalo de origem | `15m` |
| Início | `2021-01-01 00:00:00 UTC`, inclusivo |
| Fim | `2026-01-01 00:00:00 UTC`, exclusivo |
| Unidade de download | Arquivos mensais oficiais |
| Conteúdo preservado | ZIP original, checksum oficial quando disponível e metadados da coleta |
| Política de fonte | Não misturar automaticamente outras exchanges, futuros ou provedores |

O pipeline deve tratar explicitamente a mudança da unidade de timestamps da Binance Spot em 2025. A unidade detectada e a conversão aplicada precisam aparecer no relatório de auditoria; não se deve assumir milissegundos para todo o período.

## 3. Estrutura proposta

```text
coleta/
  __init__.py
  configuracao.py
  urls_binance.py
  baixar.py
  validar_arquivo.py
  auditar_candles.py
  manifesto.py
run_coleta.py
dados/
  brutos/
    binance_spot/
      BTCUSDT/15m/
      ETHUSDT/15m/
      XRPUSDT/15m/
    manifestos/
      manifesto_coleta.jsonl
      resumo_cobertura.csv
      falhas_coleta.jsonl
```

Os nomes podem ser refinados durante a implementação, mas identificadores novos devem permanecer em português. O layout final deve continuar compatível com o contrato descrito em [`dados/README.md`](../../../dados/README.md).

## 4. Fluxo de implementação

### 4.1. Configuração fechada

Criar uma configuração explícita e serializável contendo fonte, mercado, pares, intervalo, início, fim e diretório de saída. A lista de competências mensais deve ser derivada do intervalo fechado, resultando em 60 arquivos esperados por par e 180 arquivos no total.

O comando deve aceitar parâmetros úteis para retomada e diagnóstico, sem permitir que valores implícitos alterem o protocolo silenciosamente. Uma interface possível é:

```text
python run_coleta.py --config configuracoes/coleta_oficial.json
python run_coleta.py --config configuracoes/coleta_oficial.json --somente-auditoria
```

A execução da coleta será feita pelo usuário. Testes automatizados devem usar arquivos pequenos e locais, nunca iniciar o download científico completo.

### 4.2. Construção determinística das URLs

Para cada par e mês, construir a URL do arquivo mensal e a URL do checksum correspondente a partir de uma única função. Antes do download, gerar a relação completa de objetos esperados para que ausências e falhas sejam contabilizadas, em vez de simplesmente ignoradas.

Cada item planejado deve ter ao menos:

- fonte e mercado;
- par e intervalo;
- ano e mês;
- URL do ZIP e do checksum;
- caminho local esperado;
- início e fim UTC cobertos pelo arquivo.

### 4.3. Download seguro e retomável

Baixar primeiro para um arquivo temporário na mesma pasta e só renomeá-lo após a validação de integridade. Se o destino já existir e o hash for válido, reutilizá-lo; se estiver incompleto ou divergente, registrar a ocorrência e baixar novamente de forma controlada.

Definir timeout, quantidade limitada de tentativas e espera progressiva entre tentativas. Respostas HTTP, exceções e tentativas devem ser registradas sem transformar uma falha em sucesso silencioso. O processo deve poder ser reiniciado sem duplicar arquivos válidos.

### 4.4. Integridade do arquivo

Para cada ZIP:

1. calcular SHA-256 local;
2. validar o checksum oficial quando ele estiver disponível;
3. testar a integridade do contêiner ZIP;
4. confirmar que existe exatamente o CSV esperado;
5. registrar tamanho, hash, instante da coleta e resultado das verificações.

Se o checksum oficial não estiver disponível, registrar essa condição. O hash local continua obrigatório, mas não deve ser descrito como validação independente da origem.

### 4.5. Leitura e auditoria dos candles

Ler os arquivos sem modificar os ZIPs originais. A auditoria deve normalizar timestamps apenas em memória e validar:

- unidade temporal original e conversão para UTC;
- ordenação crescente;
- timestamps duplicados e duplicatas conflitantes;
- frequência esperada de 15 minutos;
- intervalos ausentes;
- preços estritamente positivos;
- volume não negativo;
- `high >= max(open, close)` e `low <= min(open, close)`;
- `high >= low`;
- limites observados de cada arquivo e do conjunto por par.

Não preencher lacunas nem escolher silenciosamente uma duplicata. A auditoria deve listar os intervalos problemáticos para decisão posterior.

### 4.6. Manifesto e relatório de cobertura

Usar JSON Lines para o manifesto detalhado, com uma linha por arquivo, e CSV para um resumo facilmente inspecionável. Cada registro do manifesto deve incluir:

```text
versao_manifesto
fonte
mercado
par
intervalo
url_dados
url_checksum
caminho_relativo
periodo_solicitado_inicio_utc
periodo_solicitado_fim_utc
timestamp_minimo_observado_utc
timestamp_maximo_observado_utc
unidade_timestamp_origem
quantidade_registros
tamanho_bytes
sha256
checksum_oficial
checksum_valido
zip_valido
data_coleta_utc
status
erros
```

O resumo de cobertura deve consolidar, por par e mês, quantidade esperada e observada de candles, duplicatas, lacunas, timestamps inicial e final e estado da validação. O relatório precisa distinguir arquivo ausente, falha de download, falha de checksum e problema no conteúdo.

## 5. Testes rápidos antes da coleta oficial

Os testes devem ser independentes de rede sempre que possível:

- geração correta dos 60 meses e das 180 combinações esperadas;
- construção das URLs para primeiro e último mês;
- reconhecimento de timestamps em milissegundos e microssegundos;
- detecção de lacuna, duplicata e duplicata conflitante em fixtures mínimas;
- rejeição de OHLCV inválido;
- validação de checksum correto e incorreto;
- retomada quando um arquivo válido já existe;
- escrita estável do manifesto, sem duplicar uma execução retomada;
- compilação sintática dos módulos Python.

Agentes podem executar apenas essas verificações rápidas. A coleta completa e qualquer pipeline científico serão executados pelo usuário.

## 6. Ordem sugerida de trabalho

1. Definir a configuração oficial e gerar o inventário esperado.
2. Implementar URLs e caminhos locais determinísticos.
3. Implementar download temporário, retomada e logs estruturados.
4. Implementar checksum e validação do ZIP.
5. Implementar parser com tratamento explícito da unidade temporal.
6. Implementar auditorias de conteúdo e continuidade.
7. Gerar manifesto detalhado e resumo de cobertura.
8. Criar fixtures e testes rápidos.
9. Documentar o comando de execução e os artefatos produzidos.
10. O usuário executa a coleta oficial e revisa as ocorrências reportadas.

## 7. Critérios de aceite

A Entrega 2 pode ser considerada concluída quando:

- o inventário contém exatamente os três pares, o intervalo `15m` e os 60 meses previstos;
- o script pode retomar uma execução interrompida sem corromper ou duplicar arquivos válidos;
- cada arquivo baixado possui SHA-256 local e estado de checksum/ZIP registrado;
- os ZIPs originais permanecem inalterados;
- a unidade dos timestamps é detectada e registrada, inclusive em 2025;
- duplicatas, lacunas e violações de OHLCV são reportadas sem correção silenciosa;
- o manifesto identifica origem, URL, período, data da coleta, contagem e hash;
- o resumo mostra claramente a cobertura de cada par e mês;
- falhas permanecem visíveis e fazem o comando terminar com estado não bem-sucedido quando comprometem a completude;
- os testes rápidos passam sem executar a coleta completa;
- o README do projeto documenta como o usuário executa e audita a coleta.

## 8. Decisões que não devem ser antecipadas

- Agregação para `1h`, `4h` e `1d`: Entrega 3.
- Cálculo de retornos, indicadores, alvo e janelas: Entrega 3.
- Folds walk-forward, purga, scalers e métricas: Entregas 3 e 4.
- Baselines B0–B3 e primeiros resultados: Entrega 4.
- Integração, treino e checkpoints do Mamba: Entrega 5.

Essa separação permite que a baseline preparada em paralelo consuma posteriormente um dataset auditado, sem acoplar a coleta às regras do modelo ou aos resultados experimentais.

