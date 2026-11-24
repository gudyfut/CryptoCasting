"""Leitura posterior dos históricos e sondas existentes; não executa modelos."""
import argparse
import json
import shutil
import numpy as np
from infraestrutura.artefatos import RAIZ, ler_json, salvar_json, sha256, agora


def executar(conferencia):
    destino = RAIZ / conferencia
    assert (destino / 'conferencia.json').is_file()
    assert not (destino / 'treinamento.json').exists(), 'Recibo existente é imutável'
    ponteiro = ler_json(RAIZ / 'registros/sem_penalizacao_diaria/execucao.json')
    pasta = RAIZ / ponteiro['pasta']
    verificacao = ler_json(destino / 'conferencia.json')
    assert verificacao['execucao'] == ponteiro
    sementes = (42, 17, 2026)
    historicos = {}
    resumo = {}
    for nome in ('seed_42', 'controle_42', 'seed_17', 'seed_2026'):
        ajuste = pasta / 'ajustes' / nome
        historia = [json.loads(l) for l in (ajuste / 'epocas.jsonl').read_text().splitlines()]
        assert [h['epoca'] for h in historia] == list(range(1, 1001))
        selecionado = ler_json(ajuste / 'selecao.json')
        melhor = min(historia, key=lambda h: h['rmse_global_validacao_retorno'])
        assert selecionado['epoca'] == melhor['epoca']
        assert selecionado['rmse_validacao'] == melhor['rmse_global_validacao_retorno']
        observacoes = [ler_json(q) for q in sorted((ajuste / 'observacoes').glob('*.json'))]
        assert len(observacoes) == 11
        for obs in observacoes:
            assert obs['pesos_e_rng_preservados']
            assert len(obs['ativacoes']) == 12
            if obs['gradiente_ultimo_lote_antes_atualizacao']:
                assert all(g['norma_l2'] == 0 for g in obs['gradiente_ultimo_lote_antes_atualizacao'].values())
        obs = ler_json(ajuste / 'observacoes/selecionado.json')
        resumo[nome] = {
            'epoca_selecionada': melhor['epoca'], 'melhor_validacao': melhor['rmse_global_validacao_retorno'],
            'ultima_epoca': historia[-1], 'contribuicao_ramos_selecionado': obs['contribuicao_ramos'],
            'normas_selecionado': obs['normas'],
            'ramos_com_saida_nao_nula_sonda': sum(v['max_saida'] > 0 for v in obs['ativacoes'].values()),
            'observacoes_preservam_pesos_rng': True, 'l2_zero_em_todas_as_observacoes': True,
        }
        historicos[nome] = historia
    limpar = lambda h: [{k: v for k, v in ep.items() if k != 'segundos'} for ep in h]
    assert limpar(historicos['seed_42']) == limpar(historicos['controle_42'])
    relatorio = {
        'utc': agora(), 'execucao': ponteiro, 'ajustes': resumo, 'historico_controle_exato': True,
        'conferencia_sha256': sha256(destino / 'conferencia.json'), 'fonte_sha256': sha256(__file__),
        'limites': 'Sondas em 32 janelas de treino fixas, não teste. Atividade funcional não prova uso preditivo útil. Perda por lote inclui epsilon e não equivale ao RMSE global. Leitura posterior, sem novos treinos ou políticas.',
    }
    salvar_json(destino / 'treinamento.json', relatorio)
    shutil.copyfile(__file__, destino / 'fonte_diagnostico.py')
    shutil.copyfile(RAIZ / 'codigo/analises/etapas/sem_penalizacao_diaria/conferir_sem_penalizacao_diaria.py', destino / 'fonte_conferencia.py')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, eixos = plt.subplots(1, 3, figsize=(14, 4.5), sharey=True)
    for eixo, seed in zip(eixos, sementes):
        historia = historicos[f'seed_{seed}']
        x = np.arange(1, 1001)
        eixo.plot(x, [h['perda_treino_rmse_lotes'] for h in historia], label='Treino: média dos lotes + epsilon', alpha=.8)
        eixo.plot(x, [h['rmse_global_validacao_retorno'] for h in historia], label='Validação: RMSE global', alpha=.8)
        ep = resumo[f'seed_{seed}']['epoca_selecionada']
        eixo.axvline(ep, color='#555', linestyle='--', label=f'Checkpoint: época {ep}')
        eixo.set_yscale('log'); eixo.set_title(f'Seed {seed}'); eixo.set_xlabel('Época'); eixo.grid(alpha=.15)
        eixo.legend(fontsize=7, loc='lower left')
    eixos[0].set_ylabel('Erro em retorno decimal · escala logarítmica')
    fig.suptitle('Sem penalização: evolução do treino e da validação\nMedidas têm agregações distintas; o teste não selecionou épocas', fontsize=12)
    fig.tight_layout(); fig.savefig(destino / 'treinamento.png', dpi=160); plt.close(fig)
    print(json.dumps({'destino': str(destino), 'controle_exato': True, 'epocas': {k:v['epoca_selecionada'] for k,v in resumo.items()}}))


if __name__ == '__main__':
    argumentos = argparse.ArgumentParser()
    argumentos.add_argument('conferencia')
    executar(argumentos.parse_args().conferencia)
