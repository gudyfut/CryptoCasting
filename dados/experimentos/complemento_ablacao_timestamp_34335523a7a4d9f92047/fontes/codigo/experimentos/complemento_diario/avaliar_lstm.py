"""Inferência após seleção, contrastes pareados e 48 carteiras LSTM novas."""
from copy import deepcopy
from pathlib import Path
import argparse
import importlib.metadata
import io
import shutil
import zipfile
import numpy as np
from infraestrutura.artefatos import RAIZ, agora, conferir_arquivos, ler_json, salvar_json, sha256
from experimentos.fechamento_ramos_diarios.avaliacao import medir, agregar, intervalo
from experimentos.generalizacao_moedas.avaliacao import carregar_mercado
from .comum import (contexto, pais, carregar_npz, exclusividade, fontes,
                    registrar_estado, conferir_unidade, fechar)
from .inventario import REG, relativo
from .operacoes import executar_carteira, ler_carteira, agregar_pacotes

ETAPA = 'lstm_walkforward'


def congelar_avaliacao(p):
    caminho = p / 'avaliacao_congelamento.json'
    if caminho.exists():
        f = ler_json(caminho)
        conferir_arquivos(RAIZ, f['fontes'])
        conferir_arquivos(p / 'fontes_avaliacao', f['fontes'])
        conferir_arquivos(RAIZ, f['dependencias'])
        return f
    refs = pais()
    wf = ler_json(refs['walkforward'] / 'congelamento.json')
    dependencias = dict(wf['referencias']['arquivos'])
    dependencias[relativo(refs['walkforward'] / 'publicacao/carteiras.zip')] = sha256(refs['walkforward'] / 'publicacao/carteiras.zip')
    dependencias[relativo(refs['walkforward'] / 'publicacao/operacoes.json')] = sha256(refs['walkforward'] / 'publicacao/operacoes.json')
    conferir_arquivos(RAIZ, dependencias)
    codigos = fontes()
    for nome in codigos:
        d = p / 'fontes_avaliacao' / nome
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(RAIZ / nome, d)
    pacotes = {d.metadata['Name']: d.version for d in importlib.metadata.distributions() if d.metadata['Name']}
    f = dict(utc=agora(), fontes=codigos, dependencias=dependencias, pacotes=pacotes,
             natureza='Avaliador congelado antes da inferência e das operações; receita/contrastes previamente fixados.')
    salvar_json(caminho, f)
    return f


def contrastes(matrizes, c):
    resultado = {}
    for ref in ('A', 'L', 'naive'):
        for forma in ('individuais', 'ensemble'):
            if forma == 'individuais':
                esq = np.array([matrizes[f'LSTM_{s}'] for s in c['seeds']])
                direita = np.array([matrizes[f'{ref}_{s}'] for s in c['seeds']]) if ref != 'naive' else matrizes['naive']
            else:
                esq = matrizes['LSTM_ensemble']
                direita = matrizes[f'{ref}_ensemble'] if ref != 'naive' else matrizes['naive']
            resultado[f'LSTM_menos_{ref}_{forma}'] = {
                str(bl): intervalo(esq-direita, bl, c['bootstrap'], forma == 'individuais')
                for bl in c['bootstrap']['blocos']}
    return resultado


def inferencia():
    import torch
    from experimentos.lstm_diaria.modelo import LSTMDiaria
    from experimentos.lstm_diaria.treinamento import inferir
    with exclusividade(ETAPA, gpu=True):
        ptr, p, f = contexto(ETAPA)
        treinos = ler_json(p / 'treinamentos_concluidos.json')
        assert treinos['cientificos'] == 12 and treinos['controles'] == 2
        assert not (p / 'previsoes_concluidas.json').exists()
        congelar_avaliacao(p)
        c, refs = f['configuracao'], pais()
        pub = p / 'publicacao'
        pub.mkdir(exist_ok=False)
        resultados = {}
        for bloco in c['blocos']:
            b = bloco['id']
            z = carregar_npz(p / b / 'dados/teste.npz')
            val = carregar_npz(p / b / 'dados/validacao.npz')
            prev, precos = {}, {}
            for variante in ('A', 'L'):
                for seed in (*c['seeds'], 'ensemble'):
                    nome = f'{variante}_{seed}'
                    q = carregar_npz(refs['walkforward'] / 'publicacao' / b / 'previsoes' / f'{nome}.npz')
                    for campo, chave in (('origens_ms', 'origens_ms'), ('ultimo_close', 'ultimo_close'), ('alvo_retorno', 'y')):
                        np.testing.assert_array_equal(q[campo], z[chave])
                    prev[nome] = q['previsoes_retorno']
                    precos[nome] = q['previsoes']
            for seed in c['seeds']:
                ajuste = p / 'ajustes' / f'{b}_{seed}'
                conferir_unidade(ajuste)
                sel = ler_json(ajuste / 'selecao.json')
                assert sha256(ajuste / sel['checkpoint']) == sel['sha256']
                ck = torch.load(ajuste / sel['checkpoint'], map_location='cpu', weights_only=True)
                rede = LSTMDiaria().to('cuda')
                rede.load_state_dict(ck['pesos'], strict=True)
                np.testing.assert_array_equal(inferir(rede, val['x']), carregar_npz(ajuste / 'validacao.npz')['previsoes'])
                nome = f'LSTM_{seed}'
                prev[nome] = inferir(rede, z['x'])
                np.testing.assert_array_equal(prev[nome], inferir(rede, z['x']))
                precos[nome] = z['ultimo_close'] * (1+prev[nome])
                del rede
                torch.cuda.empty_cache()
            precos['LSTM_ensemble'] = np.mean([precos[f'LSTM_{s}'] for s in c['seeds']], axis=0)
            prev['LSTM_ensemble'] = precos['LSTM_ensemble']/z['ultimo_close']-1
            prev['naive'] = np.zeros(len(z['y']))
            precos['naive'] = z['ultimo_close'].copy()
            m = {k: medir(z['y'], v) for k, v in prev.items()}
            erro_naive = float(np.mean(z['y']**2))
            for nome in m:
                m[nome]['habilidade_mse_naive'] = 1-float(np.mean((prev[nome]-z['y'])**2))/erro_naive
            perdas = {k: (v-z['y'])**2 for k, v in prev.items()}
            resultados[b] = dict(populacao=len(z['y']), metricas=m,
                 medias={v: agregar([m[f'{v}_{s}'] for s in c['seeds']]) for v in c['variantes']},
                 contrastes_mse=contrastes(perdas, c), selecao='validação; teste após os 14 ajustes')
            pasta = pub / b / 'previsoes'
            pasta.mkdir(parents=True)
            for nome, ret in prev.items():
                np.savez_compressed(pasta / f'{nome}.npz', previsoes_retorno=ret, previsoes=precos[nome],
                    alvo_retorno=z['y'], origens_ms=z['origens_ms'], ultimo_close=z['ultimo_close'])
            registrar_estado(ETAPA, 'inferindo', bloco=b, previsoes=len(prev))
        salvar_json(pub / 'previsao.json', resultados)
        congelar_avaliacao(p)
        arquivos = {q.relative_to(p).as_posix(): sha256(q) for q in pub.rglob('*') if q.is_file()}
        salvar_json(p / 'previsoes_concluidas.json', dict(utc=agora(), recargas_exatas=12,
                    inferencias_repetidas_exatas=12, arquivos=arquivos))
        registrar_estado(ETAPA, 'previsoes_concluidas', blocos=4, ajustes=12)


def operacoes():
    with exclusividade(ETAPA):
        ptr, p, f = contexto(ETAPA)
        assert not (p / 'operacoes_concluidas.json').exists()
        conferir_arquivos(p, ler_json(p / 'previsoes_concluidas.json')['arquivos'])
        congelar_avaliacao(p)
        c, refs = f['configuracao'], pais()
        wf = ler_json(refs['walkforward'] / 'congelamento.json')
        mercado = carregar_mercado(wf['referencias']['mercado'])
        carteiras, falhas, auditorias, pacotes = [], [], [], []
        crescimentos, medias = {}, {}
        indice_pai = ler_json(refs['walkforward'] / 'publicacao/operacoes.json')['carteiras']
        for bloco in c['blocos']:
            b = bloco['id']
            for custo, slip in enumerate(c['slippage_cenarios'], 1):
                regras = deepcopy(wf['configs_blocos'][b]['operacoes'])
                regras['slippage_por_lado'] = slip
                logs = {}
                linhas = []
                for seed in (*c['seeds'], 'ensemble'):
                    nome = f'LSTM_{seed}'
                    ident = f'{b}/{nome}/custo_{custo}'
                    z = carregar_npz(p / 'publicacao' / b / 'previsoes' / f'{nome}.npz')
                    destino = p / 'carteiras' / ident
                    r = executar_carteira(destino, z, mercado, regras, identidade=ident)
                    pacotes.append((ident, destino))
                    if r['situacao'] == 'falha_prudencial':
                        falhas.append(dict(bloco=b, unidade=nome, custo=custo, membro=ident))
                    else:
                        carteiras.append(dict(bloco=b, unidade=nome, custo=custo, membro=ident, metricas=r['metricas']))
                        auditorias.append(dict(identidade=ident, **r['auditoria']))
                        logs[nome] = np.diff(np.log(ler_carteira(destino)[1]['saldos_diarios']))
                        if seed != 'ensemble':
                            linhas.append(r['metricas'])
                    registrar_estado(ETAPA, 'simulando', concluidas=len(carteiras), falhas=len(falhas), previstas=48)
                medias[f'{b}/custo_{custo}'] = agregar(linhas) if len(linhas) == 3 else dict(incompleto=True)
                if len(logs) == 4:
                    with zipfile.ZipFile(refs['walkforward'] / 'publicacao/carteiras.zip') as arquivo:
                        for v in ('A', 'L'):
                            for seed in (*c['seeds'], 'ensemble'):
                                nome = f'{v}_{seed}'
                                linha = next(x for x in indice_pai if x['bloco'] == b and x['unidade'] == nome and x['custo'] == custo)
                                with np.load(io.BytesIO(arquivo.read(linha['membro'] + '/curva.npz'))) as q:
                                    logs[nome] = np.diff(np.log(q['saldos_diarios']))
                    logs['naive'] = np.zeros(bloco['n_teste'])
                    crescimentos[f'{b}/custo_{custo}'] = contrastes(logs, c)
                else:
                    crescimentos[f'{b}/custo_{custo}'] = dict(incompleto=True, motivo='Falhas não excluídas.')
        assert len(carteiras) + len(falhas) == 48
        agregar_pacotes(p / 'publicacao/carteiras.zip', pacotes)
        salvar_json(p / 'publicacao/operacoes.json', dict(carteiras=carteiras, falhas=falhas,
                    medias_seeds=medias, contrastes_crescimento_log_diario=crescimentos,
                    limite='Carteiras independentes por bloco; IC não é de retorno acumulado; retrospectivo.'))
        salvar_json(p / 'publicacao/auditoria_operacoes.json', dict(auditorias=auditorias, falhas=falhas))
        congelar_avaliacao(p)
        salvar_json(p / 'operacoes_concluidas.json', dict(utc=agora(), carteiras=len(carteiras), falhas=len(falhas)))
        fechar(ETAPA, dict(ajustes_cientificos=12, controles=2, carteiras=len(carteiras), falhas_prudenciais=len(falhas)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('acao', choices=['inferencia', 'operacoes'])
    globals()[parser.parse_args().acao]()
