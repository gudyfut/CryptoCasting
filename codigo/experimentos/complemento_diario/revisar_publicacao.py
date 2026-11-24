"""Revisão identificada da escala de uma figura, preservando a publicação inicial."""
import shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256, conferir_arquivos
from .comum import contexto, congelar, exclusividade, fechar, registrar_estado
from .inventario import REG, relativo
from .publicar import salvar_figura

ETAPA = 'sintese_complemento_revisada'


def executar():
    original, anterior, _ = contexto('sintese_complemento')
    conferir_arquivos(anterior, ler_json(anterior / 'fechamento.json')['arquivos'])
    _, timestamp, _ = contexto('ablacao_timestamp')
    fonte_ramos = timestamp / 'publicacao/ramos.json'
    origem = anterior / 'publicacao'
    motivo = 'Reduzir espaço vazio e afastar marcadores das bordas na figura dos ramos; nenhuma alteração científica.'
    entradas = [anterior / 'fechamento.json', fonte_ramos, *origem.iterdir()]
    with exclusividade(ETAPA):
        ptr, p, _ = congelar(ETAPA, entradas, REG / 'qualificacao_publicacao/qualificacao.json',
            dict(publicacao_original=original, motivo=motivo, tabelas_e_resultados_inalterados=True))
        pub = p / 'publicacao'
        pub.mkdir()
        substituidos = {'timestamp_ramos.png', 'timestamp_ramos.pdf', 'consulta.json'}
        copias = {}
        for arquivo in origem.iterdir():
            if arquivo.name not in substituidos:
                shutil.copyfile(arquivo, pub / arquivo.name)
                assert sha256(arquivo) == sha256(pub / arquivo.name)
                copias[arquivo.name] = sha256(arquivo)
        ramos = ler_json(fonte_ramos)['populacoes']
        chaves = [f'{b}/{s}' for b in ('B1', 'B2', 'B3', 'B4') for s in (42, 17, 2026)]
        plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False})
        fig, ax = plt.subplots(figsize=(10, 5), constrained_layout=True)
        for deslocamento, fase, rotulo in zip([-.16, 0, .16], ['treino', 'validacao', 'teste'], ['treino', 'validação', 'teste']):
            ax.scatter(np.arange(12)+deslocamento, [ramos[k+'/'+fase]['max_abs'] for k in chaves], label=rotulo, s=25)
        maior = max(v['max_abs'] for v in ramos.values())
        ax.set_yscale('symlog', linthresh=1e-8)
        ax.set_ylim(-1e-9, max(1e-7, maior*3))
        ax.set_yticks([0, 1e-8, 1e-7, 1e-6])
        ax.set(xticks=range(12), xticklabels=chaves, ylabel='Máxima diferença absoluta no retorno previsto')
        ax.tick_params(axis='x', rotation=45)
        ax.legend()
        ax.grid(axis='y', alpha=.2)
        fig.suptitle('Novos checkpoints A: efeito de desligar os ramos Mamba\nEscala linear até 10⁻⁸ e logarítmica acima; zeros preservados')
        salvar_figura(fig, pub, 'timestamp_ramos')
        consulta = ler_json(origem / 'consulta.json')
        consulta.update(revisao_apresentacao=dict(utc=agora(), motivo=motivo,
            publicacao_original=relativo(origem), execucao=ptr,
            arquivos_alterados=sorted(substituidos), tabelas_identicas=18))
        salvar_json(pub / 'consulta.json', consulta)
        assert len(list(pub.glob('*.csv'))) == 18
        assert len(list(pub.glob('*.png'))) == len(list(pub.glob('*.pdf'))) == 8
        salvar_json(p / 'revisao_apresentacao.json', dict(utc=agora(), motivo=motivo,
            original=original, arquivos_copiados_identicos=copias,
            tabelas_identicas=sum(nome.endswith('.csv') for nome in copias),
            dados_ramos_sha256=sha256(fonte_ramos), parametros=dict(limiar_linear=1e-8, limite_inferior=-1e-9, limite_superior=max(1e-7, maior*3))))
        fechar(ETAPA, dict(tabelas=18, figuras=8, tabelas_identicas_ao_original=True, inspecao_visual='pendente'))
        ponteiro = REG / 'sintese_complemento/versao_final.json'
        assert not ponteiro.exists()
        salvar_json(ponteiro, dict(utc=agora(), etapa=ETAPA, execucao=ptr, original=original,
            motivo=motivo, fechamento=ler_json(REG / ETAPA / 'fechamento.json')))
        registrar_estado('sintese_complemento', 'preservado_com_revisao_de_apresentacao', versao_final=relativo(ponteiro))
        registrar_estado(ETAPA, 'publicado_inspecao_pendente', publicacao=relativo(pub))


if __name__ == '__main__':
    executar()
