"""Preparação e execução explícitas; tentativas e fontes nunca sobrescritas."""
import contextlib
import importlib.metadata
import os
from pathlib import Path
import platform
import shutil
import traceback
import numpy as np
import pandas as pd
from previsao24.arquivos import RAIZ, agora, identidade, ler_json, salvar_json, sha256, verificar_arquivos
from .dados import CANAIS, preparar as preparar_matriz

CONFIG = 'configuracoes/ohlcv24_001.json'
REGISTROS = RAIZ / 'registros/ohlcv'


def fontes():
    caminhos = list((RAIZ / 'estudo_ohlcv').glob('*.py')) + list((RAIZ / 'tests_ohlcv').glob('*.py'))
    caminhos += [RAIZ / p for p in [CONFIG, 'run_ohlcv.py', 'previsao24/__init__.py',
                 'previsao24/arquivos.py', 'previsao24/metricas.py', 'previsao24/baselines.py',
                 'previsao24/financeiro.py', 'experimento_penalizacao/__init__.py',
                 'experimento_penalizacao/otimizador.py']]
    return {p.relative_to(RAIZ).as_posix(): sha256(p) for p in sorted(caminhos)}


def configuracao():
    c = ler_json(RAIZ / CONFIG)
    # Uma mudança científica requer implementação/testes próprios; não aceitar flags ignoradas.
    if (c['par'] != 'BTCUSDT' or c['contexto'] != 168 or c['horizonte'] != 24
            or c['candle_minutos'] != 60 or c['origem_minutos'] != 60
            or c['entradas'] != CANAIS or c['seeds'] != [17, 42, 2026]
            or c['normalizacao_bloco'] != 'pre_layernorm'
            or c['representacao'] != 'log_ohlc_relativo_close_anterior_e_log1p_volume_base'
            or c['normalizacao'] != 'padronizacao_estatica_por_canal_treino_horas_unicas'
            or c['modelos'] != ['mamba', 'lstm', 'naive', 'arima']
            or c['arima']['tendencia'] != 'n'
            or c['arima']['ordens'] != [[p, 1, q] for p in range(3) for q in range(3)]):
        raise ValueError('Configuração não corresponde ao contrato implementado.')
    if (c['operacao']['hora_utc'] != 0 or c['operacao']['latencia_minutos'] != 1
            or list(c['divisao']) != ['treino','validacao','teste']
            or c['controles_reproducao'] != [{'modelo':'mamba','seed':42},{'modelo':'lstm','seed':42}]
            or c['backend'] != 'oficial' or c['dispositivo'] != 'cuda'):
        raise ValueError('Grade, calendário ou backend incompatível.')
    limites=[pd.Timestamp(v,tz='UTC') for parte in c['divisao'].values() for v in parte]
    if not (limites[0]<limites[1]==limites[2]<limites[3]==limites[4]<limites[5]):
        raise ValueError('Divisões devem ser contíguas, ordenadas e sem sobreposição.')
    return c


def ambiente():
    import torch
    import inspect
    import importlib
    from mamba_ssm import Mamba
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA indisponível; proibido fallback.')
    instalados = {'mamba': Path(inspect.getfile(Mamba))}
    for modulo in ('mamba_ssm.ops.selective_scan_interface', 'selective_scan_cuda', 'causal_conv1d_cuda'):
        instalados[modulo] = Path(importlib.import_module(modulo).__file__)
    return {'python': platform.python_version(), 'torch': str(torch.__version__), 'cuda': torch.version.cuda,
            'gpu': torch.cuda.get_device_name(), 'host': platform.node(),
            'implementacao_instalada': {k: {'arquivo':str(p),'sha256':sha256(p)} for k,p in instalados.items()},
            'pacotes': {p: importlib.metadata.version(p) for p in
                        ['mamba_ssm', 'causal_conv1d', 'numpy', 'pandas', 'statsmodels', 'pyarrow']}}


def preparar():
    c = configuracao()
    origem = RAIZ / c['dataset_origem']
    anterior = ler_json(origem / 'dataset.json')
    arquivos = {p: h for p, h in anterior['arquivos'].items() if p.startswith(c['par'] + '/')}
    verificar_arquivos(origem, arquivos)
    assinatura = {'configuracao_dados': {k: c[k] for k in
                  ['par', 'contexto', 'divisao', 'horizonte', 'entradas', 'representacao', 'normalizacao']},
                  'fontes_dados': arquivos, 'manifesto_origem': sha256(origem / 'dataset.json'),
                  'implementacao': sha256(Path(__file__).with_name('dados.py'))}
    codigo = identidade(assinatura)[:20]
    pasta = RAIZ / f'dados/processados/ohlcv24_{codigo}'
    if pasta.exists():
        manifesto = ler_json(pasta / 'dataset.json')
        if manifesto['assinatura'] != assinatura:
            raise ValueError('Identidade de dataset divergente.')
        verificar_arquivos(pasta, manifesto['arquivos'])
    else:
        pasta.mkdir(parents=True)
        h, matriz, blocos, escalas = preparar_matriz(pd.read_parquet(origem / c['par'] / 'horas.parquet'), c)
        h.to_parquet(pasta / 'horas.parquet', index=False)
        np.save(pasta / 'entradas.npy', matriz, allow_pickle=False)
        salvar_json(pasta / 'escalas.json', escalas)
        for nome, b in blocos.items():
            b.to_parquet(pasta / f'{nome}.parquet', index=False)
        contagens = {nome: {'n': len(b), 'primeira_origem': b['origem_utc'].min().isoformat(),
                           'ultima_origem': b['origem_utc'].max().isoformat(),
                           'ultimo_destino': b['destino_utc'].max().isoformat()}
                     for nome, b in blocos.items()}
        manifesto = {'id': codigo, 'criado_utc': agora(), 'assinatura': assinatura,
                     'origem': c['dataset_origem'], 'primeiro_minuto': anterior['primeiro_minuto'],
                     'minutos': (origem / c['par'] / 'minutos.npy').relative_to(RAIZ).as_posix(),
                     'minutos_sha256': arquivos[c['par'] + '/minutos.npy'], 'populacoes': contagens,
                     'horas_totais': len(h), 'horas_ohlcv_ausentes': int(h[['open','high','low','close','volume']].isna().any(axis=1).sum()),
                     'arquivos': {p.name: sha256(p) for p in sorted(pasta.iterdir()) if p.is_file()}}
        salvar_json(pasta / 'dataset.json', manifesto)
    salvar_json(REGISTROS / 'dataset.json', {'id': codigo, 'pasta': pasta.relative_to(RAIZ).as_posix(),
                                           'sha256': sha256(pasta / 'dataset.json')})
    return pasta, manifesto


def congelar():
    q = ler_json(REGISTROS / 'qualificacao.json')
    verificar_arquivos(RAIZ, {q['recibo']: q['sha256']})
    qual = ler_json(RAIZ / q['recibo'])
    verificar_arquivos((RAIZ / q['recibo']).parent, qual['artefatos'])
    if qual['status'] != 'aprovado' or qual['fontes'] != fontes() or qual['ambiente'] != ambiente():
        raise ValueError('Qualificação desatualizada, incompleta ou de outro ambiente.')
    pasta_dados, dados = preparar()
    contrato = {'configuracao': configuracao(), 'fontes': fontes(), 'dataset': dados['id'],
                'dataset_pasta': pasta_dados.relative_to(RAIZ).as_posix(),
                'dataset_sha256': sha256(pasta_dados / 'dataset.json'), 'ambiente': ambiente(),
                'qualificacao': q}
    codigo = identidade(contrato)[:20]
    pasta = RAIZ / f'dados/experimentos/ohlcv24_{codigo}'
    if pasta.exists():
        if ler_json(pasta / 'congelamento.json')['contrato'] != contrato:
            raise ValueError('Congelamento divergente.')
    else:
        pasta.mkdir(parents=True)
        for nome in contrato['fontes']:
            destino = pasta / 'fontes' / nome
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(RAIZ / nome, destino)
        # O documento de trabalho pode evoluir; esta cópia é o protocolo desta execução.
        shutil.copy2(RAIZ / 'docs/desenho_ohlcv24.md', pasta / 'protocolo.md')
        salvar_json(pasta / 'congelamento.json', {'id': codigo, 'utc': agora(), 'contrato': contrato,
                    'protocolo_sha256': sha256(pasta / 'protocolo.md')})
        salvar_json(pasta / 'progresso.json', {'status': 'preparado_sem_treinamento', 'concluidos': []})
    salvar_json(REGISTROS / 'execucao.json', {'id': codigo, 'pasta': pasta.relative_to(RAIZ).as_posix(),
                                            'congelamento_sha256': sha256(pasta / 'congelamento.json')})
    return pasta


def carregar_execucao():
    p = ler_json(REGISTROS / 'execucao.json')
    pasta = RAIZ / p['pasta']
    verificar_arquivos(pasta, {'congelamento.json': p['congelamento_sha256']})
    congelado = ler_json(pasta / 'congelamento.json')
    c = congelado['contrato']
    verificar_arquivos(RAIZ, c['fontes'])
    verificar_arquivos(pasta / 'fontes', c['fontes'])
    verificar_arquivos(pasta, {'protocolo.md': congelado['protocolo_sha256']})
    dados = RAIZ / c['dataset_pasta']
    verificar_arquivos(dados, {'dataset.json': c['dataset_sha256']})
    d = ler_json(dados / 'dataset.json')
    verificar_arquivos(dados, d['arquivos'])
    verificar_arquivos(RAIZ, {d['minutos']: d['minutos_sha256']})
    return pasta, c, dados, d


def grade(c):
    principais = [{'chave': f'{m}_{s}', 'modelo': m, 'seed': s, 'contexto': c['contexto'], 'controle': False}
                  for m in ('mamba', 'lstm') for s in c['seeds']]
    controles = [dict(chave=f"controle_{q['modelo']}_{q['seed']}", contexto=c['contexto'], controle=True, **q)
                 for q in c['controles_reproducao']]
    # Aprovar reprodução antes de liberar as demais seeds.
    ordem = [p for p in principais if p['seed'] == 42] + controles
    return ordem + [p for p in principais if p['seed'] != 42] + [{'chave': m, 'modelo': m} for m in ('naive', 'arima')]


def publicar_tentativa(tentativa):
    salvar_json(tentativa / 'conclusao.json', {'utc': agora(), 'status': 'concluido',
                'arquivos': {p.relative_to(tentativa).as_posix(): sha256(p) for p in sorted(tentativa.rglob('*'))
                             if p.is_file() and p.name != 'conclusao.json'}})


def verificar_tentativa(tentativa):
    r = ler_json(tentativa / 'conclusao.json')
    if r['status'] != 'concluido':
        raise ValueError('Tentativa não concluída.')
    verificar_arquivos(tentativa, r['arquivos'])


def conferir_reproducao(referencia, repeticao, c):
    a = ler_json(referencia / 'resultado.json')
    b = ler_json(repeticao / 'resultado.json')
    diferencas = {}
    for nome in ('validacao', 'teste', 'operacional'):
        x = pd.read_parquet(referencia / f'previsoes_{nome}.parquet')
        y = pd.read_parquet(repeticao / f'previsoes_{nome}.parquet')
        pd.testing.assert_frame_equal(x.drop(columns='previsao'), y.drop(columns='previsao'), check_exact=True)
        delta = np.abs(x['previsao'].to_numpy() - y['previsao'].to_numpy())
        if not np.isfinite(delta).all():
            raise ValueError('Reprodução com valores não finitos.')
        diferencas[nome] = float(delta.max())
    relativa = abs(a['metricas']['validacao']['mse']-b['metricas']['validacao']['mse'])/max(a['metricas']['validacao']['mse'],1e-15)
    recibo = {'maxima_diferenca_previsoes': diferencas, 'diferenca_relativa_mse_validacao': relativa,
              'mesma_epoca': a['epoca_selecionada']==b['epoca_selecionada'], 'limites':c['reproducao']}
    salvar_json(repeticao / 'reproducao.json', recibo)
    if (not recibo['mesma_epoca'] or max(diferencas.values())>c['reproducao']['diferenca_absoluta_previsao']
            or relativa>c['reproducao']['diferenca_relativa_mse']):
        raise ValueError('Reprodução excedeu limites predefinidos; investigar, não selecionar tentativa.')
    return recibo


def executar(retomar=False):
    from .treino import treinar
    from previsao24.baselines import ajustar
    from previsao24.metricas import calcular
    from .avaliacao import concluir
    pasta, contrato, dados, manifesto = carregar_execucao()
    if contrato['ambiente'] != ambiente():
        raise ValueError('Ambiente mudou: investigar antes de retomar.')
    estado = ler_json(pasta / 'progresso.json')
    if estado['status'] == 'concluido':
        raise ValueError('Execução concluída: não reexecutar para regenerar publicações.')
    if estado['status'] != 'preparado_sem_treinamento' and not retomar:
        raise ValueError('Investigar interrupção e usar --retomar explicitamente, sem descartar tentativas.')
    c = contrato['configuracao']
    salvar_json(pasta / 'processo.json', {'pid': os.getpid(), 'host': platform.node(), 'inicio_utc': agora()})
    blocos = {b: pd.read_parquet(dados / f'{b}.parquet') for b in ('treino', 'validacao', 'teste', 'operacional')}
    matriz = np.load(dados / 'entradas.npy', allow_pickle=False)
    escalas = ler_json(dados / 'escalas.json')
    horas = pd.read_parquet(dados / 'horas.parquet')
    concluidos = {}
    try:
        for celula in grade(c):
            chave = celula['chave']
            raiz = pasta / 'celulas' / chave
            anteriores = sorted(raiz.glob('tentativa_*'))
            prontas = [p for p in anteriores if (p / 'conclusao.json').exists()]
            if len(prontas) > 1:
                raise ValueError('Mais de uma tentativa concluída: não selecionar resultado.')
            if prontas:
                tentativa = prontas[0]
                verificar_tentativa(tentativa)
            else:
                tentativa = raiz / f'tentativa_{len(anteriores)+1:03d}'
                tentativa.mkdir(parents=True)
                salvar_json(tentativa / 'inicio.json', {'celula': celula, 'utc': agora(),
                            'anteriores_preservadas': [p.name for p in anteriores]})
                salvar_json(pasta / 'progresso.json', {'status': 'executando', 'atual': chave,
                            'concluidos': list(concluidos), 'utc': agora()})
                try:
                    with (tentativa / 'treinamento.log').open('w', encoding='utf-8', buffering=1) as log:
                        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                            if celula['modelo'] in ('mamba', 'lstm'):
                                treinar(c, celula, matriz, blocos, escalas, tentativa)
                            elif celula['modelo'] == 'arima':
                                ajustar(horas, blocos, c, tentativa)
                            else:
                                resultado = {'modelo': 'naive', 'metricas': {}}
                                for b in ('validacao', 'teste', 'operacional'):
                                    q = blocos[b][['origem_utc','destino_utc','indice_hora','close','preco_destino','alvo']].copy()
                                    q['previsao'] = 0.
                                    q.to_parquet(tentativa / f'previsoes_{b}.parquet', index=False)
                                    if b != 'operacional':
                                        resultado['metricas'][b] = calcular(q['alvo'], q['previsao'])
                                salvar_json(tentativa / 'resultado.json', resultado)
                    if celula.get('controle'):
                        referencia = concluidos[f"{celula['modelo']}_{celula['seed']}"]
                        conferir_reproducao(referencia, tentativa, c)
                    publicar_tentativa(tentativa)
                except BaseException:
                    salvar_json(tentativa / 'falha.json', {'utc': agora(), 'erro': traceback.format_exc()})
                    raise
            concluidos[chave] = tentativa
        concluir(pasta, c, manifesto, blocos, concluidos)
        salvar_json(pasta / 'progresso.json', {'status': 'concluido', 'utc': agora(), 'concluidos': list(concluidos)})
    except BaseException:
        salvar_json(pasta / 'progresso.json', {'status': 'interrompido', 'utc': agora(),
                    'concluidos': list(concluidos), 'erro': traceback.format_exc()})
        raise
    finally:
        salvar_json(pasta / 'processo.json', {'pid': os.getpid(), 'host': platform.node(), 'fim_utc': agora(), 'ativo': False})
