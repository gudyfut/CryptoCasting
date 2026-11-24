"""Grade LSTM finita, com reprodução real anterior a qualquer novo teste."""
from pathlib import Path
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import numpy as np
from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256, conferir_arquivos
from .inventario import REG, relativo
from .comum import (carregar_npz, configuracao, contexto, congelar, exclusividade,
                    pais, registrar_estado, selar_unidade, conferir_unidade, fontes)
from .contratos import conferir_dados_reais, entradas_lstm

ETAPA = 'lstm_walkforward'


def conferir_ajustes(a, b):
    """Compara história, todos os pesos melhorados e validação; exclui relógio/ID."""
    import torch
    a, b = Path(a), Path(b)
    historias = []
    for p in (a, b):
        historias.append([{k: v for k, v in json.loads(linha).items() if k != 'segundos'}
                          for linha in (p / 'epocas.jsonl').read_text().splitlines()])
    assert historias[0] == historias[1], 'Trajetória de treinamento diferente.'
    sa, sb = ler_json(a / 'selecao.json'), ler_json(b / 'selecao.json')
    for k in ('epoca', 'rmse_validacao', 'checkpoint'):
        assert sa[k] == sb[k], f'Seleção diverge em {k}'
    arquivos = sorted(p.name for p in (a / 'checkpoints').glob('*.pt'))
    assert arquivos == sorted(p.name for p in (b / 'checkpoints').glob('*.pt'))
    for nome in arquivos:
        ca = torch.load(a / 'checkpoints' / nome, map_location='cpu', weights_only=True)
        cb = torch.load(b / 'checkpoints' / nome, map_location='cpu', weights_only=True)
        assert ca['epoca'] == cb['epoca'] and set(ca['pesos']) == set(cb['pesos'])
        for k in ca['pesos']:
            assert torch.equal(ca['pesos'][k], cb['pesos'][k]), (nome, k)
    va, vb = carregar_npz(a / 'validacao.npz'), carregar_npz(b / 'validacao.npz')
    assert set(va) == set(vb)
    for k in va:
        np.testing.assert_array_equal(va[k], vb[k], err_msg=k)
    return dict(aprovado=True, trajetoria_exata=True, epocas=len(historias[0]),
                selecao_exata=True, pesos_exatos_checkpoints=len(arquivos),
                validacao_exata=True, epoca_selecionada=sa['epoca'])


def verificar_ambiente():
    import torch
    assert sys.platform == 'linux' and torch.cuda.is_available()
    ativos = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name',
                                      '--format=csv,noheader'], text=True).strip()
    for linha in ativos.splitlines():
        pid, nome = [x.strip() for x in linha.split(',', 1)]
        # Aplicações gráficas WDDM do host não são ajustes científicos. Não
        # encerrar nenhum processo; recusar outro processo de cálculo Linux.
        grafico_host = '\\' in nome and any(s in nome.lower() for s in ('brave.exe', 'chrome.exe', 'chatgpt.exe', 'dwm.exe', 'msedge.exe'))
        assert pid == str(os.getpid()) or grafico_host, f'Outro processo GPU exige inspeção: {linha}'
    return dict(host=platform.node(), python=sys.version, torch=torch.__version__,
                cuda=torch.version.cuda, cudnn=torch.backends.cudnn.version(),
                gpu=torch.cuda.get_device_name(), processos_gpu=ativos,
                numpy=np.__version__, executavel=sys.executable)


def qualificar():
    import torch
    from experimentos.lstm_diaria.treinamento import ajustar
    from experimentos.lstm_diaria.modelo import LSTMDiaria
    with exclusividade(ETAPA, gpu=True):
        ambiente = verificar_ambiente()
        c = configuracao()
        destino = REG / ETAPA / 'qualificacoes' / str(time.time_ns())
        destino.mkdir(parents=True, exist_ok=False)
        ensaios = subprocess.run([sys.executable, '-B', '-m', 'unittest',
                    'testes.lstm_diaria.test_contratos', 'testes.complemento_diario.test_contratos',
                    'testes.simulacao_operacoes.test_auditoria_grade_continuidade.GradeInteira', '-v'],
                    cwd=RAIZ, text=True, capture_output=True)
        (destino / 'testes.log').write_text(ensaios.stdout + ensaios.stderr, encoding='utf-8')
        assert ensaios.returncode == 0, ensaios.stdout + ensaios.stderr
        dados = conferir_dados_reais()
        rng = np.random.default_rng(93)
        tr = dict(x=rng.normal(size=(65, 6, 14)).astype('float32'), y=rng.normal(size=65) * .02)
        val = dict(x=rng.normal(size=(31, 6, 14)).astype('float32'), y=rng.normal(size=31) * .02)
        for i in (1, 2):
            ajustar(tr, val, c['treinamento_lstm'], 42, destino / f'sintetico_{i}',
                    dict(tipo='sintetico'), epocas=4)
        exato = conferir_ajustes(destino / 'sintetico_1', destino / 'sintetico_2')
        assert sum(p.numel() for p in LSTMDiaria().parameters()) == 13601
        salvar_json(destino / 'qualificacao.json', dict(utc=agora(), situacao='aprovada',
                    ambiente=ambiente, fontes=fontes(), dados=dados, sintetico=exato,
                    testes_sem_skips=True, limite='Controles de mercado ainda obrigatórios.'))
        salvar_json(REG / ETAPA / 'qualificacao.json', dict(arquivo=relativo(destino / 'qualificacao.json'),
                    sha256=sha256(destino / 'qualificacao.json')))
        registrar_estado(ETAPA, 'qualificado', ambiente=ambiente)


def preparar():
    q = ler_json(REG / ETAPA / 'qualificacao.json')
    assert sha256(RAIZ / q['arquivo']) == q['sha256']
    assert ler_json(RAIZ / q['arquivo'])['fontes'] == fontes()
    refs = pais()
    wf = ler_json(refs['walkforward'] / 'congelamento.json')
    ptr, p, f = congelar(ETAPA, entradas_lstm(), RAIZ / q['arquivo'],
                         dict(configs_blocos=wf['configs_blocos'], escalas=wf['escalas'],
                              referencias={k: relativo(v) for k, v in refs.items()}))
    for b in configuracao()['blocos']:
        base = p / b['id']
        (base / 'dados').mkdir(parents=True)
        for fase in ('treino', 'validacao', 'teste'):
            shutil.copyfile(refs['walkforward'] / b['id'] / 'dados' / f'{fase}.npz', base / 'dados' / f'{fase}.npz')
        salvar_json(base / 'escalas.json', wf['escalas'][b['id']])
        salvar_json(base / 'configuracao_referencia.json', wf['configs_blocos'][b['id']])
    salvar_json(p / 'dados_preparados.json', {relativo(q): sha256(q) for q in sorted(p.rglob('*.npz'))
                                           if 'fontes' not in q.parts})


def executar(retomar=False):
    from experimentos.lstm_diaria.treinamento import ajustar
    with exclusividade(ETAPA, gpu=True):
        ambiente = verificar_ambiente()
        ptr, p, f = contexto(ETAPA)
        conferir_arquivos(RAIZ, ler_json(p / 'dados_preparados.json'))
        assert not (p / 'treinamentos_concluidos.json').exists(), 'Treinamentos já concluídos.'
        if (p / 'inicio_treinamento.json').exists():
            assert retomar, 'Inspecione o processo/estado antes de retomar explicitamente.'
        else:
            salvar_json(p / 'inicio_treinamento.json', dict(utc=agora(), ambiente=ambiente))
        refs, c = pais(), f['configuracao']
        feitos = []

        def rodar(nome, treino, validacao, seed, controle, origem=None):
            destino = p / 'ajustes' / nome
            if destino.exists():
                conferir_unidade(destino)
            else:
                registrar_estado(ETAPA, 'treinando', ajuste=nome, concluidos=len(feitos), total=14)
                ajustar(treino, validacao, c['treinamento_lstm'], seed, destino,
                        dict(execucao=ptr['id'], ajuste=nome, controle=controle))
                if origem is not None:
                    salvar_json(destino / 'controle.json', conferir_ajustes(origem, destino))
                selar_unidade(destino)
            feitos.append(dict(nome=nome, controle=controle, pasta=relativo(destino),
                               conclusao=ler_json(destino / 'conclusao.json')))
            return destino

        fixa = refs['fixa'] / 'BTCUSDT/dados'
        rodar('controle_fixa_42', carregar_npz(fixa / 'treino.npz'), carregar_npz(fixa / 'validacao.npz'),
              42, True, refs['lstm'] / 'BTCUSDT/ajustes/seed_42')
        for bloco in c['blocos']:
            b = bloco['id']
            treino = carregar_npz(p / b / 'dados/treino.npz')
            validacao = carregar_npz(p / b / 'dados/validacao.npz')
            primeiro = rodar(f'{b}_42', treino, validacao, 42, False)
            if b == 'B1':
                rodar('controle_B1_42', treino, validacao, 42, True, primeiro)
            for seed in (17, 2026):
                rodar(f'{b}_{seed}', treino, validacao, seed, False)
        assert len(feitos) == 14 and sum(x['controle'] for x in feitos) == 2
        contexto(ETAPA)
        salvar_json(p / 'treinamentos_concluidos.json', dict(utc=agora(), ajustes=feitos,
                    cientificos=12, controles=2, epocas_por_ajuste=200))
        registrar_estado(ETAPA, 'treinamentos_concluidos', cientificos=12, controles=2,
                          avaliacao='pendente')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('acao', choices=['qualificar', 'preparar', 'executar'])
    parser.add_argument('--retomar', action='store_true')
    args = parser.parse_args()
    if args.acao == 'executar':
        executar(args.retomar)
    else:
        globals()[args.acao]()
