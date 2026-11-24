"""Intervenção diagnóstica pós-treino nos ramos A do walk-forward diário."""
import fcntl
import os
import shutil
import subprocess
import traceback
from pathlib import Path

os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')

import numpy as np
import torch
from mamba_ssm import Mamba

from infraestrutura.artefatos import RAIZ, agora, conferir_arquivos, identidade, ler_json, salvar_json, sha256
from experimentos.fechamento_ramos_diarios.contratos import receita
from experimentos.walkforward_diario.treinamento import carregar_rede, inferir


def executar():
    reg = RAIZ / 'registros/walkforward_diario'
    ponteiro = reg / 'diagnostico_ramos_tentativa_002.json'
    assert not ponteiro.exists(), 'Já existe uma execução; confira o seu estado.'
    with (RAIZ / 'registros/operacional_futuros/gpu.lock').open('a+b') as gpu:
        fcntl.flock(gpu, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert not subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader'],
                                           text=True).strip()
        ptr = ler_json(reg / 'execucao.json')
        p = RAIZ / ptr['pasta']
        assert sha256(p / 'congelamento.json') == ptr['congelamento_sha256']
        f = ler_json(p / 'congelamento.json')
        fecho = ler_json(p / 'fechamento.json')
        assert fecho['situacao'] == 'concluido_controles_aprovados'
        conferir_arquivos(p, fecho['arquivos'])
        conferir_arquivos(RAIZ, f['fontes'])
        original = Path(__file__)
        spec = dict(utc=agora(), natureza='Sondagem retrospectiva posterior sem retreinamento',
                    execucao=ptr, fechamento_sha256=sha256(p / 'fechamento.json'),
                    fonte_sha256=sha256(original), versoes=dict(torch=torch.__version__, cuda=torch.version.cuda),
                    regra='Desligar simultaneamente os ramos Mamba nos checkpoints A e comparar previsões nas mesmas origens.',
                    limite='Intervenção final por bloco e seed; não mede contribuição durante aprendizado nem estabelece equivalência.')
        ident = identidade(spec)[:20]
        destino = RAIZ / 'dados/reavaliacoes' / f'sondagem_walkforward_diario_{ident}'
        destino.mkdir(parents=True, exist_ok=False)
        shutil.copyfile(original, destino / 'sondar_ramos.py')
        salvar_json(destino / 'congelamento.json', spec)
        referencia = dict(id=ident, pasta=destino.relative_to(RAIZ).as_posix(),
                          congelamento_sha256=sha256(destino / 'congelamento.json'))
        salvar_json(ponteiro, dict(situacao='executando', utc=agora(), pid=os.getpid(), execucao=referencia))
        resultados = []
        try:
            for bloco in f['configuracao']['blocos']:
                b = bloco['id']
                with np.load(p / b / 'dados/teste.npz', allow_pickle=False) as q:
                    x, alvo, origens = q['x'].copy(), q['y'].copy(), q['origens_ms'].copy()
                for seed in f['configuracao']['seeds']:
                    rede = carregar_rede(p / b / 'ajustes' / f'A_{seed}', receita(f['configs_blocos'][b], 'A'))
                    pesos = {k: v.detach().cpu().clone() for k, v in rede.state_dict().items()}
                    normal = inferir(rede, x)
                    with np.load(p / 'publicacao' / b / 'previsoes' / f'A_{seed}.npz', allow_pickle=False) as q:
                        np.testing.assert_array_equal(normal, q['previsoes_retorno'])
                        np.testing.assert_array_equal(origens, q['origens_ms'])
                    hooks = [m.register_forward_hook(lambda mod, args, saida: torch.zeros_like(saida))
                             for m in rede.modules() if isinstance(m, Mamba)]
                    assert len(hooks) == 12
                    try:
                        sem_ramos = inferir(rede, x)
                    finally:
                        for hook in hooks:
                            hook.remove()
                    assert all(torch.equal(v, rede.state_dict()[k].detach().cpu()) for k, v in pesos.items())
                    delta = normal.astype(np.float64) - sem_ramos.astype(np.float64)
                    limite = f['configs_blocos'][b]['operacoes']['filtro_retorno_absoluto']
                    decisao = lambda v: np.where(v > limite, 1, np.where(v < -limite, -1, 0))
                    linha = dict(bloco=b, seed=seed, populacao=len(alvo), ramos=len(hooks),
                                 max_diferenca=float(abs(delta).max()), rms_diferenca=float(np.sqrt(np.mean(delta**2))),
                                 mse_normal=float(np.mean((normal-alvo)**2)), mse_sem_ramos=float(np.mean((sem_ramos-alvo)**2)),
                                 decisoes_diferentes=int(np.sum(decisao(normal) != decisao(sem_ramos))))
                    np.savez_compressed(destino / f'{b}_A_{seed}.npz', origens_ms=origens,
                                        previsao=normal, previsao_sem_ramos=sem_ramos)
                    resultados.append(linha)
                    print('SONDADO', b, seed, flush=True)
                    del rede
                    torch.cuda.empty_cache()
            assert len(resultados) == 12
            conferir_arquivos(p, fecho['arquivos'])
            conferir_arquivos(RAIZ, f['fontes'])
            salvar_json(destino / 'resultado.json', dict(resultados=resultados, limite=spec['limite']))
            arquivos = {q.relative_to(destino).as_posix(): sha256(q) for q in destino.iterdir()
                        if q.is_file() and q.name != 'fechamento.json'}
            salvar_json(destino / 'fechamento.json', dict(utc=agora(), situacao='concluido_conferido',
                        execucao=referencia, checkpoints=12, arquivos=arquivos))
            salvar_json(ponteiro, dict(utc=agora(), situacao='concluido_conferido', execucao=referencia,
                                      fechamento_sha256=sha256(destino / 'fechamento.json')))
            print('SONDAGEM_CONCLUIDA', len(resultados), flush=True)
        except BaseException:
            salvar_json(destino / 'incidente.json', dict(utc=agora(), erro=traceback.format_exc()))
            salvar_json(ponteiro, dict(utc=agora(), situacao='interrompido_preservado', execucao=referencia))
            raise


if __name__ == '__main__':
    executar()
