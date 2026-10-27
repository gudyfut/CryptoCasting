"""Consulta curta pelo WSL, sem abrir arquivos mutáveis por leitores Windows."""
from collections import deque
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from previsao24.arquivos import RAIZ, ler_json


def main():
    coordenador = ler_json(RAIZ / 'registros/continuacao_protocolo.json')
    ponteiro = ler_json(RAIZ / 'registros/execucao_atual.json')
    pasta = RAIZ / ponteiro['caminho']
    progresso = ler_json(pasta / 'progresso_avaliacao.json')
    processo = ler_json(pasta / 'processo.json')
    processos = []
    for nome, estado in [('coordenador', coordenador), ('executor', processo)]:
        pid = estado['pid']
        try:
            os.kill(pid, 0)
            comando = Path(f'/proc/{pid}/cmdline').read_bytes().replace(b'\0', b' ').decode()
            processos.append({'papel': nome, 'pid': pid, 'vivo': True, 'comando': comando.strip()})
        except ProcessLookupError:
            processos.append({'papel': nome, 'pid': pid, 'vivo': False})
        except FileNotFoundError:
            processos.append({'papel': nome, 'pid': pid, 'vivo': False})
    log = (RAIZ / coordenador['retomada_incidente'] / 'avaliar_retomada.log'
           if 'retomada_incidente' in coordenador
           else RAIZ / 'registros/logs' / f"avaliar_{ponteiro['id']}.log")
    ultima = None
    if log.exists():
        with log.open() as arquivo:
            ultima = next(iter(deque(arquivo, maxlen=1)), '').strip()
    print(json.dumps({'processos': processos, 'etapa': coordenador['status'],
                      'progresso': progresso, 'ultimo_log_avaliacao': ultima}, ensure_ascii=False))


if __name__ == '__main__':
    main()
