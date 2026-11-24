# Evolução da pesquisa CryptoCasting

Os números financeiros vigentes vêm de `registros/custos_vigentes/vigente.json` quando a reavaliação está concluída. `custos-servidor.ts` confere manifesto, pais e publicações antes de combinar finanças revisadas com métricas de previsão preservadas. O cenário é slippage provisório de0,01% por lado, com estresses proporcionais; as fontes históricas originais continuam acessíveis e identificadas. Sem publicação completa, o painel informa custo histórico; divergência bloqueia a apresentação como vigente.

Interface local com dez fases da pesquisa, das primeiras tentativas à generalização para ETH, BNB e XRP. A visão geral começa pelo estágio atual; cada fase explica a pergunta, a alteração, a conclusão e seus limites. **Resultados e conclusões** compara as receitas diárias de BTC, separa carteiras individuais de ensemble e permite imprimir. **Como avaliamos** explica o método atual e mantém o desenho histórico em uma seção recolhida.

Os 14 testes detalhados do panorama OHLCV de 03/11, seus gráficos e 205 séries permanecem acessíveis na terceira fase. O modo **Apresentar** usa ←/→ e Esc. Links antigos com `?etapa=` continuam funcionando.

Todas as fases e os 14 testes históricos separam **Resumo**, **Configuração** e **Fontes**; avaliações publicadas têm sua área de resultados. O resumo apresenta a mudança, a conclusão e apenas as características essenciais. A configuração mostra uma categoria por vez — dados, rede, treino, avaliação ou operação — com colunas de antes/depois e alterações em dourado. É possível selecionar a receita, comparar com a etapa anterior ou com a referência científica, filtrar alterações e consultar todos os parâmetros. Cada valor pode ser expandido para revelar sua definição integral. A categoria e a base da comparação permanecem ao navegar entre etapas.

## Executar

Executar npm neste diretório:

```sh
npm run dev
```

Abrir http://localhost:3000. Para a versão de produção: `npm run build` e `npm start`. A interface requer o repositório e os artefatos locais; não foi publicada em serviço externo.

## Dados e rastreabilidade

`scripts/exportar_panorama.py` exporta resultados existentes. Executado a partir da raiz do repositório, requer Python, pandas, NumPy e o leitor Parquet já disponíveis no ambiente científico:

```sh
python dataview/scripts/exportar_panorama.py
```

Ele confere manifestos, hashes das previsões e históricos de épocas, alinhamento de 24h, preço/alvo e o MSE de todas as origens horárias. Não importa treinadores e não inicia treinamento, inferência ou backtest. Escreve apenas o snapshot da apresentação (`src/data/panorama.json`), as séries em `dados/portal_panorama/series/` e o recibo em `registros/interface/panorama_20261103/exportacao.json`.

O snapshot atual reúne 205 séries de previsões salvas. O explorador mostra uma origem diária às 00h UTC para facilitar a leitura; as métricas publicadas usam a população horária completa. O gráfico liga previsões terminais independentes, sem representar uma trajetória prevista dentro do dia. O CSV contém os exemplos diários da série selecionada. O primeiro exemplo usa a seed 42 por convenção, sem seleção por resultado.

O servidor confere a disponibilidade e a integridade das fontes originais. Os endpoints `/api/panorama/serie` e `/api/panorama/fonte` aceitam somente identidades e caminhos da exportação e verificam SHA-256 antes da entrega. Ausência local recebe aviso explícito; nunca gera resultado artificial. Para usar em outra máquina, preservar/restaurar as fontes e as séries conforme a política de armazenamento do projeto.

Os resultados posteriores são lidos por `src/lib/evolucao-servidor.ts`, sem chamar executores científicos. Resumos e carteiras são verificados contra os hashes dos fechamentos. Fontes narrativas também têm uma lista explícita de caminhos e hashes. Ausências ou divergências não são preenchidas com zero. O snapshot histórico e seu recibo não são regenerados para incluir fases novas.

`src/lib/fichas-servidor.ts` lê configurações, receitas efetivamente ajustadas e protocolos por uma lista fixa de fontes com SHA-256. Não chama treinamento nem regenera resultados. `src/lib/fichas.ts` mantém os campos comparáveis; `FichaTecnica.tsx` exibe seus valores e diferenças. Uma fonte ausente ou alterada impede exibir a ficha dependente, em vez de presumir parâmetros. As fontes originais completas ficam acessíveis no rodapé da ficha.

O estágio atual apresenta a rodada concluída e conferida em 10/11/2026: nove treinos novos, três controles e 210 carteiras, com BTC herdado sem retreino. XRP usa a publicação de `continuacao_001`. O servidor verifica o fechamento conjunto, a conferência das quatro moedas e os fechamentos individuais por SHA-256 antes de afirmar a conclusão. A área de resultados permite alternar 2024/2025 e média das três seeds/ensemble; cada carteira e o erro relativo ao Naive ficam disponíveis sob demanda. Fontes ausentes ou divergentes não recebem números presumidos.

Controles não entram nas médias. Carteiras são independentes; ensemble combina previsões antes da operação. 2024 selecionou checkpoints e 2025 já foi consultado. Não há ranking único entre populações, moedas e políticas diferentes.

## Verificação

```sh
npm test
node --test tests/panorama.integration.mjs
npm run build
```

O teste de integração exige o servidor ativo em `http://127.0.0.1:3000`. Os testes verificam as 205 séries, pareamentos, médias, incerteza, custos, cronologia, resultados recentes e entrega pela API. A revisão visual inclui desktop/celular, navegação entre fases, conclusões e detalhes históricos.

A interface anterior foi substituída na navegação. Os componentes históricos sem uso estão preservados em `arquivo/fontes_referencia/fontes.zip`. Os endpoints históricos e seus testes continuam disponíveis, com os artefatos anteriores preservados. O aceite antigo está em `registros/interface/aceite_final.json`; a evidência desta entrega fica em `registros/interface/panorama_20261103/`.

## Fontes da trajetória

A fase de busca com IA está consolidada em [Exploração do processo de melhoria com IA](../docs/exploracao_ia.md). A [cronologia do projeto](../docs/andamento.md), o catálogo e as publicações científicas sustentam as etapas posteriores. A interface é uma leitura desses resultados; não inicia, retoma ou altera treinamentos.
