"""Apresentação final sobre o publicador preservado, sem mudar resultados.

Explicita colunas anualizadas herdadas e mantém linhas de falha/média
indisponível nas tabelas operacionais. Acrescenta exposição por lado.
"""
from types import FunctionType
import pandas as pd
from infraestrutura.artefatos import ler_json, salvar_json, sha256
from . import publicar as base


def tabelas_previsoes(p, destino, prefixo):
    resultado = base.tabelas_previsoes(p, destino, prefixo)
    ops = ler_json(p / 'publicacao/operacoes.json')
    linhas = []
    for x in ops['carteiras']+ops['falhas']:
        linha = {k: x[k] for k in ('bloco', 'unidade', 'custo')}
        linha.update(forma='ensemble' if x['unidade'].endswith('_ensemble') else 'individual', membro=x['membro'])
        recibo = ler_json(p / 'carteiras' / x['membro'] / 'recibo.json')
        linha['situacao'] = recibo['situacao']
        if recibo['metricas'] is not None:
            linha.update(recibo['metricas'])
            d = recibo['descricao']
            n = sum(d['decisoes'].values())
            linha.update(dias_caixa=d['exposicao_executada']['0'],
                numero_episodios=d['quantidade_episodios'], reversoes_diretas=d['reversoes_diretas'])
            for lado, nome in [('-1', 'venda'), ('0', 'caixa'), ('1', 'compra')]:
                linha['fracao_decisoes_'+nome] = d['decisoes'][lado]/n
                linha['fracao_dias_executados_'+nome] = d['exposicao_executada'][lado]/n
        linhas.append(linha)
    for chave, medidas in ops['medias_seeds'].items():
        partes = chave.split('/')
        variante = 'LSTM' if len(partes) == 2 else partes[1]
        linha = dict(bloco=partes[0], unidade=variante+'_media_seeds', custo=int(partes[-1].split('_')[-1]),
            forma='media_metricas_carteiras_individuais', identidade=chave,
            situacao='media_indisponivel_por_falha' if medidas.get('incompleto') else 'media_tres_seeds')
        if not medidas.get('incompleto'):
            linha.update({k: v['media'] for k, v in medidas.items()})
        linhas.append(linha)
    pd.DataFrame(linhas).to_csv(destino / f'{prefixo}_operacoes.csv', index=False)
    return resultado


def salvar_apresentacao(caminho, objeto):
    if caminho.name == 'consulta.json':
        objeto = dict(objeto,
            natureza='Figuras e síntese usam os períodos observados, sem anualização. CSVs preservam também as métricas anuais herdadas do motor, identificadas pelos nomes.',
            colunas_anualizadas_herdadas=['retorno_anualizado', 'sharpe_diario_rf_zero', 'calmar'],
            linhas_indisponiveis='Falhas prudenciais e médias inviáveis permanecem identificadas, sem estimativas substitutas.',
            publicador_final='codigo/experimentos/complemento_diario/publicacao_final.py')
    return salvar_json(caminho, objeto)


def congelar_apresentacao(etapa, entradas, qualificacao, extras=None):
    extras = dict(extras or {})
    extras['apresentacao'] = dict(fonte_base_sha256=sha256(base.__file__), fonte_final_sha256=sha256(__file__),
        mudancas=['Esclarecer campos anualizados herdados nos CSVs.', 'Preservar linhas de falha e médias indisponíveis.',
                  'Expor decisões e dias executados por lado nas tabelas operacionais.'],
        metricas_previsoes_carteiras_inalteradas=True)
    return base.congelar(etapa, entradas, qualificacao, extras)


def executar():
    # Namespace privado, seguindo o padrão de reutilização do repositório;
    # o publicador original e seus snapshots permanecem intactos.
    globais = dict(base.executar.__globals__)
    globais.update(tabelas_previsoes=tabelas_previsoes, salvar_json=salvar_apresentacao,
                   congelar=congelar_apresentacao)
    funcao = FunctionType(base.executar.__code__, globais, base.executar.__name__,
                          base.executar.__defaults__, base.executar.__closure__)
    funcao()


if __name__ == '__main__':
    executar()
