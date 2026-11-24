"""Publicação de tentativas e exclusão mútua: Linux/WSL executor qualificado."""
from contextlib import contextmanager
from pathlib import Path
import os
import platform
from uuid import uuid4
from infraestrutura.artefatos import agora, ler_json, salvar_json, sha256, conferir_arquivos


def publicar(pasta):
    p = pasta / 'conclusao.json'
    if p.exists():
        raise FileExistsError('Tentativa já publicada.')
    arquivos = {q.relative_to(pasta).as_posix(): sha256(q) for q in sorted(pasta.rglob('*')) if q.is_file()}
    salvar_json(p, {'status': 'concluido', 'utc': agora(), 'arquivos': arquivos})


def conferir(pasta):
    r = ler_json(pasta / 'conclusao.json')
    if r['status'] != 'concluido':
        raise ValueError('Tentativa incompleta.')
    conferir_arquivos(pasta, r['arquivos'])


def inicio_processo(pid):
    p = Path(f'/proc/{pid}/stat')
    return p.read_text().rsplit(')', 1)[1].split()[19] if p.exists() else None


@contextmanager
def exclusividade(pasta, retomar=False):
    if platform.system() != 'Linux':
        raise RuntimeError('Executor qualificado exige Linux/WSL CUDA.')
    import fcntl
    p = pasta / 'processo.json'
    host = platform.node()
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    with (pasta / 'execucao.lock').open('a+b') as arquivo:
        try:
            fcntl.flock(arquivo, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as erro:
            raise RuntimeError('Execução já possui processo vivo; não duplicar.') from erro
        try:
            if p.exists():
                anterior = ler_json(p)
                if anterior.get('ativo'):
                    if anterior['host'] != host:
                        raise RuntimeError('Outro host indicado como ativo; verificar na máquina responsável.')
                    if (anterior['boot'] == boot and inicio_processo(anterior['pid']) == anterior['inicio_proc']):
                        raise RuntimeError('PID original ainda vivo.')
                    if not retomar:
                        raise RuntimeError('Processo encerrado sem fechamento: investigar e usar retomada explícita.')
                    salvar_json(pasta / 'incidentes' / f'{uuid4().hex}.json',
                                {'utc': agora(), 'processo_anterior': anterior, 'motivo': 'processo_ausente_confirmado',
                                 'acao': 'preservar tentativas; reiniciar somente ajuste incompleto da mesma seed'})
            atual = {'pid': os.getpid(), 'host': host, 'boot': boot, 'inicio_proc': inicio_processo(os.getpid()),
                     'inicio_utc': agora(), 'ativo': True}
            salvar_json(p, atual)
            try:
                yield
            finally:
                salvar_json(p, dict(atual, ativo=False, fim_utc=agora()))
        finally:
            fcntl.flock(arquivo, fcntl.LOCK_UN)
