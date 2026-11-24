"""Congelamentos por etapa e recibos sem sobrescrita de evidências científicas."""
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import platform
import shutil
import sys
import traceback
import numpy as np
from infraestrutura.artefatos import RAIZ, agora, conferir_arquivos, identidade, ler_json, salvar_json, sha256
from .inventario import REG, CFG, PROTOCOLO, relativo


def configuracao():
    inicio = ler_json(REG / 'inicio.json')
    assert sha256(CFG) == inicio['configuracao_sha256']
    assert sha256(PROTOCOLO) == inicio['protocolo_sha256']
    return ler_json(CFG)


def pais():
    inv = ler_json(REG / 'inventario.json')
    assert inv['situacao'] == 'aprovado' and not inv['erros']
    return {k: RAIZ / v['ponteiro']['pasta'] for k, v in inv['pais'].items()}


def carregar_npz(p):
    with np.load(p, allow_pickle=False) as z:
        return {k: z[k].copy() for k in z.files}


def fontes():
    arquivos = list((RAIZ / 'codigo').rglob('*.py'))
    arquivos += list((RAIZ / 'testes/complemento_diario').glob('*.py'))
    arquivos += [CFG, PROTOCOLO, REG / 'autorizacao.txt']
    return {relativo(p): sha256(p) for p in sorted(arquivos) if '__pycache__' not in p.parts}


def registrar_estado(etapa, situacao, **campos):
    s = dict(utc=agora(), etapa=etapa, situacao=situacao, **campos)
    salvar_json(REG / etapa / 'estado.json', s)
    print('ESTADO', etapa, situacao, json.dumps(campos, ensure_ascii=False), flush=True)
    return s


def congelar(etapa, entradas, qualificacao, extras=None):
    registro = REG / etapa
    assert not (registro / 'execucao.json').exists(), 'Etapa já identificada; inspecione seu estado.'
    q = Path(qualificacao)
    assert ler_json(q)['situacao'] == 'aprovada'
    dependencias = {relativo(p): sha256(p) for p in sorted(set(map(Path, entradas)))}
    f = dict(utc=agora(), etapa=etapa, configuracao=configuracao(), fontes=fontes(),
             dependencias=dependencias, qualificacao=dict(arquivo=relativo(q), sha256=sha256(q)),
             inventario=dict(arquivo=relativo(REG / 'inventario.json'), sha256=sha256(REG / 'inventario.json')),
             extras=extras or {}, ambiente=dict(host=platform.node(), plataforma=platform.platform(),
                                               python=sys.version, executavel=sys.executable))
    ident = identidade(f)[:20]
    p = RAIZ / 'dados/experimentos' / f'complemento_{etapa}_{ident}'
    p.mkdir(parents=True, exist_ok=False)
    for nome in f['fontes']:
        d = p / 'fontes' / nome
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(RAIZ / nome, d)
    salvar_json(p / 'congelamento.json', f)
    ptr = dict(id=ident, pasta=relativo(p), congelamento_sha256=sha256(p / 'congelamento.json'))
    salvar_json(registro / 'execucao.json', ptr)
    registrar_estado(etapa, 'preparado', execucao=ptr)
    return ptr, p, f


def contexto(etapa, conferir=True):
    ptr = ler_json(REG / etapa / 'execucao.json')
    p = RAIZ / ptr['pasta']
    assert sha256(p / 'congelamento.json') == ptr['congelamento_sha256']
    f = ler_json(p / 'congelamento.json')
    assert f['configuracao'] == configuracao()
    if conferir:
        conferir_arquivos(RAIZ, f['fontes'])
        conferir_arquivos(p / 'fontes', f['fontes'])
        conferir_arquivos(RAIZ, f['dependencias'])
        assert sha256(RAIZ / f['qualificacao']['arquivo']) == f['qualificacao']['sha256']
    return ptr, p, f


@contextmanager
def exclusividade(etapa, gpu=False):
    registro = REG / etapa
    registro.mkdir(parents=True, exist_ok=True)
    abertos = []
    try:
        caminhos = [registro / 'execucao.lock']
        if gpu:
            assert sys.platform == 'linux', 'Treinamento científico exige o ambiente WSL/CUDA qualificado.'
            caminhos.insert(0, RAIZ / 'registros/operacional_futuros/gpu.lock')
        for caminho in caminhos:
            f = caminho.open('a+b')
            abertos.append(f)
            if sys.platform == 'linux':
                import fcntl
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            else:
                import msvcrt
                if caminho.stat().st_size == 0:
                    f.write(b'0'); f.flush()
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        processo = dict(utc=agora(), pid=os.getpid(), host=platform.node(), ativo=True,
                        plataforma=sys.platform, executavel=sys.executable)
        if sys.platform == 'linux':
            processo.update(boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                            inicio_processo_ticks=Path('/proc/self/stat').read_text().split()[21])
        salvar_json(registro / 'processo.json', processo)
        try:
            yield
        except BaseException:
            incidente = registro / 'incidentes' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f') + '.json')
            salvar_json(incidente, dict(utc=agora(), erro=traceback.format_exc(), processo=processo))
            registrar_estado(etapa, 'interrompido_preservado', incidente=relativo(incidente))
            raise
        finally:
            processo.update(ativo=False, encerramento_utc=agora())
            salvar_json(registro / 'processo.json', processo)
    finally:
        for f in reversed(abertos):
            f.close()


def selar_unidade(pasta):
    pasta = Path(pasta)
    arquivo = pasta / 'manifesto_complemento.json'
    assert not arquivo.exists()
    arquivos = {p.relative_to(pasta).as_posix(): sha256(p) for p in sorted(pasta.rglob('*')) if p.is_file()}
    salvar_json(arquivo, dict(utc=agora(), arquivos=arquivos))


def conferir_unidade(pasta):
    conferir_arquivos(pasta, ler_json(Path(pasta) / 'manifesto_complemento.json')['arquivos'])


def fechar(etapa, resumo):
    ptr, p, f = contexto(etapa)
    assert not (p / 'fechamento.json').exists()
    arquivos = {q.relative_to(p).as_posix(): sha256(q) for q in sorted(p.rglob('*'))
                if q.is_file() and 'fontes' not in q.relative_to(p).parts}
    salvar_json(p / 'fechamento.json', dict(utc=agora(), situacao='executado_auditoria_posterior_pendente',
                execucao=ptr, resumo=resumo, arquivos=arquivos))
    salvar_json(REG / etapa / 'fechamento.json', dict(arquivo=relativo(p / 'fechamento.json'),
                                                   sha256=sha256(p / 'fechamento.json')))
    registrar_estado(etapa, 'executado_auditoria_posterior_pendente', execucao=ptr, **resumo)
