"""Descreve as barreiras e os desfechos observados sem selecionar modelos ou operações."""
import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from barreiras.arquivos import agora, identidade, ler_json, salvar_json, sha256
from barreiras.dados import verificar_dataset
from barreiras.particoes import separar


def quantis(valores):
    valores = np.asarray(valores, dtype=float)
    if not len(valores) or not np.isfinite(valores).all():
        raise ValueError('Resumo descritivo exige valores observados e finitos.')
    return dict(zip(('p05', 'mediana', 'p95'), np.quantile(valores, [.05, .5, .95]).tolist()))


def descrever(q):
    n = len(q)
    if not n or not q.classe.isin([0, 1, 2]).all():
        raise ValueError('População preditiva vazia ou com desfechos não observados.')
    inicio = q.saida_indice.to_numpy() - q.entrada_indice.to_numpy()
    fim = q.saida_conhecida_indice.to_numpy() - q.entrada_indice.to_numpy()
    if np.any(inicio < 0) or np.any(fim < inicio) or np.any(fim - inicio > 1):
        raise ValueError('Tempos incompatíveis com resolução de um minuto.')
    d = q.distancia.to_numpy()
    r = {'n': n, 'primeira_origem': q.origem_utc.iloc[0].isoformat(),
         'ultima_origem': q.origem_utc.iloc[-1].isoformat(),
         'inferior_primeiro': int(q.classe.eq(0).sum()),
         'prazo_esgotado': int(q.classe.eq(1).sum()),
         'superior_primeiro': int(q.classe.eq(2).sum()),
         'ambiguos': int(q.ambiguo.sum())}
    for nome in ('inferior_primeiro', 'prazo_esgotado', 'superior_primeiro', 'ambiguos'):
        r[f'proporcao_{nome}'] = r[nome] / n
    for nome, valores in (
        ('sigma_horario', q.sigma), ('distancia_logaritmica', d),
        ('alta_limite_relativa', np.expm1(d)), ('queda_limite_relativa', -np.expm1(-d)),
        ('duracao_minutos_limite_inferior', inicio), ('duracao_minutos_limite_superior', fim),
    ):
        r.update({f'{nome}_{chave}': valor for chave, valor in quantis(valores).items()})
    return r


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('diretorio', type=Path)
    args = parser.parse_args()
    ciclo = ler_json(args.diretorio / 'ciclo.json')
    if identidade(ciclo['assinatura'])[:20] != ciclo['id']:
        raise ValueError('Identidade do ciclo inválida.')
    c = ciclo['assinatura']['configuracao']
    if not set(c['folds']).issubset({'DB1', 'DB2', 'DB3', 'DB4'}):
        raise ValueError('Este diagnóstico está restrito ao desenvolvimento.')
    if sha256(RAIZ / 'barreiras/particoes.py') != ciclo['assinatura']['codigo']['barreiras/particoes.py']:
        raise ValueError('Cortes temporais atuais divergem da execução.')
    dataset = RAIZ / 'dados/processados' / f"barreiras_{ciclo['assinatura']['dataset']}"
    meta = verificar_dataset(dataset)
    comuns = np.load(dataset / 'origens_comuns.npy', allow_pickle=False)
    linhas, operacionais, populacoes = [], [], {}
    for par in c['pares']:
        for h in c['horizontes']:
            amostras = pd.read_parquet(dataset / par / f'amostras_H{h}.parquet')
            for fold in c['folds']:
                blocos = separar(amostras, comuns, fold)
                for nome in ('treino', 'validacao', 'teste'):
                    q = blocos[nome]
                    chave = (fold, nome)
                    if chave in populacoes and not q.origem_utc.equals(populacoes[chave]):
                        raise ValueError('Descrição não usa origens comuns entre moedas e prazos.')
                    populacoes[chave] = q.origem_utc
                    linhas.append({'par': par, 'horizonte': h, 'fold': fold, 'particao': nome, **descrever(q)})
                q = blocos['operacional']
                operacionais.append({'par': par, 'horizonte': h, 'fold': fold,
                    'origens_causais': len(q), 'desfechos_observados': int(q.classe.ge(0).sum()),
                    'desfechos_nao_observados': int(q.classe.lt(0).sum()),
                    'exclusoes_do_recorte_preditivo': len(q) - len(blocos['teste'])})
    destino = args.diretorio / 'consolidacao'
    destino.mkdir(exist_ok=True)
    indice = {(r['par'], r['horizonte'], r['fold']): r for r in linhas if r['particao'] == 'teste'}
    conferidos = []
    for arquivo in sorted(args.diretorio.glob('*/estado.json')):
        estado = ler_json(arquivo)
        if estado['status'] != 'concluida_auditada':
            continue
        if estado['id_ciclo'] != ciclo['id']:
            raise ValueError('Tentativa de outra identidade no diretório do ciclo.')
        celula = estado['celula']
        esperado = indice[celula['par'], celula['horizonte'], celula['fold']]
        hashes = ler_json(arquivo.parent / 'integridade.json')
        for modelo in ('mamba', 'lstm', 'ar1'):
            relativo = f'{modelo}/previsoes_teste.parquet'
            previsoes = arquivo.parent / relativo
            if sha256(previsoes) != hashes[relativo]:
                raise ValueError('Previsões mudaram desde a auditoria.')
            y = pd.read_parquet(previsoes, columns=['classe']).classe
            contagens = [int(y.eq(i).sum()) for i in range(3)]
            if len(y) != esperado['n'] or contagens != [esperado[k] for k in ('inferior_primeiro', 'prazo_esgotado', 'superior_primeiro')]:
                raise ValueError('Descrição dos desfechos diverge das previsões avaliadas.')
        conferidos.append(estado['id'])
    pd.DataFrame(linhas).to_csv(destino / 'descricao_amostras.csv', index=False)
    pd.DataFrame(operacionais).to_csv(destino / 'populacoes_operacionais.csv', index=False)
    salvar_json(destino / 'descricao_amostras.json', {
        'id_ciclo': ciclo['id'], 'dataset': meta['id'], 'gerado_utc': agora(),
        'script_sha256': sha256(Path(__file__)),
        'natureza': 'Descrição de dados do desenvolvimento; não comprova conclusão da grade de modelos.',
        'notas': [
            'W não duplica esta tabela: alvos, distâncias e origens preditivas são comuns aos dois contextos.',
            'Durações referem-se a todas as origens preditivas, não apenas às operações selecionadas por uma política.',
            'Limites de duração representam a incerteza dentro do minuto; toques no open e expirações têm duração exata.',
            'Alta/queda e sigma estão em frações; multiplicar por 100 para exibir percentuais.',
            'Exclusões preditivas incluem purga comum de 168h e qualidade futura; não são todas falhas de dados.',
            'Desfechos não observados permanecem na população operacional; não autorizam excluir entradas futuras.',
        ],
        'arquivos': {nome: sha256(destino / nome) for nome in ('descricao_amostras.csv', 'populacoes_operacionais.csv')},
        'recortes_preditivos': len(linhas), 'recortes_operacionais': len(operacionais),
        'execucoes_conferidas': conferidos,
    })
    print(f'{len(linhas)} recortes preditivos e {len(operacionais)} operacionais descritos; dataset verificado.')


if __name__ == '__main__':
    main()
