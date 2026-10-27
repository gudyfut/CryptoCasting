"""Registra o aceite observado nesta sessão; não treina nem altera fontes científicas.

As verificações visuais são observações do agente, não testes automáticos deste
script. Ele vincula essas observações à publicação e às fontes efetivamente vistas.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from previsao24.arquivos import RAIZ, agora, ler_json, salvar_json, sha256


def main():
    ponteiro = ler_json(RAIZ/'registros/execucao_atual.json')
    fechamento = RAIZ/'registros/auditorias'/ponteiro['id']/'fechamento.json'
    auditoria = ler_json(fechamento)
    portal = RAIZ/'dados/portal/resumo.json'
    resumo = ler_json(portal)
    if auditoria['status'] != 'aprovado' or auditoria['execucao'] != ponteiro['id'] or auditoria['resumo_portal_sha256'] != sha256(portal):
        raise ValueError('Fechamento ausente ou incompatível com a publicação atual.')
    if len(resumo['metricas']) != 832 or len(resumo['series']) != 384 or not resumo['avaliacao_completa'] or not resumo['desenvolvimento_completo']:
        raise ValueError('Publicação incompleta.')
    imagens = ['avaliacao_sintese_desktop.png','avaliacao_sintese_mobile.png',
               'avaliacao_financeiro_desktop.png','avaliacao_financeiro_mobile.png',
               'avaliacao_final_explorador_desktop.png','avaliacao_final_explorador_mobile.png']
    fontes = sorted(p for p in (RAIZ/'dataview/src').rglob('*') if p.is_file())
    fontes += [RAIZ/'dataview/package.json', RAIZ/'dataview/package-lock.json',
               RAIZ/'dataview/tests/api.integration.mjs', RAIZ/'dataview/tests/previsoes.test.mjs']
    recibo = {
        'status':'aprovado', 'utc':agora(), 'execucao':ponteiro['id'], 'dataset':resumo['dataset'],
        'entregas_protocolo':8, 'resultados':832, 'ajustes_neurais':768, 'referencias':64,
        'candidatos_arima':288, 'series':384,
        'fechamento_sha256':sha256(fechamento), 'resumo_portal_sha256':sha256(portal),
        'publicacoes':auditoria['publicacoes'],
        'fontes_interface_sha256':{p.relative_to(RAIZ).as_posix():sha256(p) for p in fontes},
        'imagens_sha256':{n:sha256(RAIZ/'registros/interface'/n) for n in imagens},
        'comandos_observados':[
            {'comando':'npm run build','diretorio':'dataview','codigo_saida':0,'observacao':'Após ajuste de busca de data; compilação, TypeScript e geração de rotas aprovados.'},
            {'comando':'npm run lint','diretorio':'dataview','codigo_saida':0,'observacao':'Após revisão final do teste de API.'},
            {'comando':'npm test','diretorio':'dataview','codigo_saida':0,'aprovados':2,'escopo':'Todas as 384 séries: hashes, timestamps, preços de origem/destino, alvo, MSE e modelos presentes.'},
            {'comando':'node --test tests/api.integration.mjs','diretorio':'dataview','codigo_saida':0,'aprovados':2,'escopo':'Séries de ambas as fases; JSON/3 CSVs/operação financeira com bytes iguais ao manifesto; seleções inválidas recusadas.'},
            {'comando':'git diff --check','codigo_saida':0,'observacao':'Somente avisos de normalização futura LF/CRLF; nenhuma normalização científica foi executada.'}
        ],
        'verificacoes_visuais_observadas':[
            'Ambas as fases disponíveis e separadas; 768 ajustes neurais e 64 referências exibidos a partir dos registros.',
            'Síntese da avaliação: LSTM melhor que Mamba; Mamba pior que Naive; diferença LSTM–Naive inclui zero. Desenvolvimento: ambas as redes piores que Naive.',
            'Placar global e BTC/B4/336h conferidos contra resumo auditado; médias por seed não tratadas como ensemble. Ganho médio por célula distinguido da razão de MSEs globais.',
            'Intervalos de 7/14/28 dias, seis contrastes de contextos, estabilidade das seis combinações modelo/seed e 16 ordens ARIMA conferidos.',
            'BTC/LSTM/W24: seed17 +14,90%, capital 11489,90, oito entradas; seed2026 -7,39%, capital 9260,79, sete entradas. Agravado seed2026 -9,32%, mesmos sinais, custo 405,57.',
            'Naive em caixa: capital 10000, retorno zero, sem operações; contexto/seed desabilitados. Controle compra diária com perda. Risco integral não auditável preservado no desenvolvimento e disponível na avaliação.',
            'Curva financeira real inspecionada no desktop; cartões e filtros no celular 390px, sem transbordamento horizontal.',
            'XRP/B4/W336/seed2026: origem 1751328000, destino +86400; preço 2,2362 para 2,172. Retornos exibidos +0,68% LSTM, +0,17% Mamba, zero Naive, +0,07% ARIMA; observado -2,87%. Preços implícitos e erros de log-retorno conferidos.',
            'Explorador com todos os quatro modelos, sem aviso de ausência; gráfico real desktop/celular. Seleção de Naive/ARIMA, próxima/anterior e recarga com origem preservada verificadas.',
            'Busca por 02/07/2025 00:00 levou à origem 1751414400, posição25/4392, após ajuste do evento de entrada do campo de data.',
            'Laboratório de erro respondeu aos controles; previsão -10 e observado3 produziram erro absoluto13 e quadrático169, identificados como exemplo didático.',
            'Console da aba final sem erros após as interações; viewport temporário restaurado.'
        ],
        'limites':[
            'Aceite das oito entregas computacionais do plano; não representa aprovação pelo orientador nem conclusão da redação/defesa do TCC.',
            'Exposição anterior classificada pela declaração humana preservada, sem certificação universal de holdout intocado. Avaliação consultada: novos ciclos nesses períodos são desenvolvimento.',
            'Simulação Spot comprada/caixa, sem futuros, alavancagem ou stops; não há demonstração de rentabilidade consistente.',
            'Arquivo histórico local íntegro; não é cópia externa de segurança. Interrupção operacional e retomada permanecem preservadas.'
        ],
        'registrador_sha256':sha256(Path(__file__)),
        'origem_evidencia_visual':'Inspeção do agente no navegador nesta sessão, comparada com os arquivos auditados; não é uma alegação de automação visual pelo presente script.'
    }
    destino = RAIZ/'registros/interface/aceite_final.json'
    if destino.exists():
        raise FileExistsError('Aceite já registrado; não sobrescrever silenciosamente.')
    salvar_json(destino, recibo)
    print(f'Aceite registrado: {destino}', flush=True)


if __name__ == '__main__':
    main()
