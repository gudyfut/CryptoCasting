"""Registra e verifica uma retomada operacional sem alterar fontes congeladas."""
import argparse
import fcntl
import json
import os
import shutil
from pathlib import Path
from experimento_penalizacao.ciclo import conferir_fontes, hashes, indice
from previsao24.arquivos import RAIZ, agora, ler_json, salvar_json, verificar_arquivos, sha256
from previsao24.dados import verificar_dataset

argumentos = argparse.ArgumentParser()
argumentos.add_argument('--evidencia', required=True)
opcoes = argumentos.parse_args()
destino = RAIZ / 'dados/experimentos/penalizacao_7868a4d847c1410fc681'
registro = RAIZ / 'registros/incidentes' / ('penalizacao_retomada_' + agora().replace(':', '').replace('+', '_'))
registro.mkdir(parents=True, exist_ok=False)
for nome in ('processo.json', 'progresso.json', 'piloto_aprovado.json'):
    shutil.copy2(destino / nome, registro / nome)
for caminho in destino.glob('celulas/*/tentativa_*/tentativa.json'):
    if ler_json(caminho)['status'] == 'em_andamento':
        copia = registro / 'tentativas_incompletas' / caminho.parent.parent.name / caminho.parent.name
        shutil.copytree(caminho.parent, copia)
recibo = {'utc': agora(), 'execucao': destino.name, 'status': 'verificando',
          'evidencia_windows': opcoes.evidencia,
          'verificador_sha256': sha256(Path(__file__)),
          'decisao': 'Reutilizar ajustes auditados, preservar tentativa interrompida e repetir somente a incompleta com a mesma seed e configuracao; nenhuma selecao por resultado.'}
salvar_json(registro / 'verificacao.json', recibo)
try:
    ativos = []
    for p in Path('/proc').glob('[0-9]*/cmdline'):
        try:
            comando = p.read_bytes().replace(b'\0', b' ')
            if b'run_penalizacao.py executar' in comando:
                ativos.append(str(p))
        except (OSError, PermissionError):
            pass
    if ativos:
        raise RuntimeError(f'Executor encontrado: {ativos}')
    with (destino / 'exclusao.lock').open('a') as bloqueio:
        fcntl.flock(bloqueio, fcntl.LOCK_EX | fcntl.LOCK_NB)
        conferir_fontes(destino)
        execucao = ler_json(destino / 'execucao.json')
        antes = ler_json(RAIZ / execucao['preparacao_caminho'] / 'preservacao_antes.json')['arquivos']
        if hashes([RAIZ / p for p in antes]) != antes:
            raise ValueError('Manifesto preservado divergiu.')
        dataset = verificar_dataset(RAIZ / execucao['dataset_caminho'])
        if dataset['id'] != execucao['assinatura']['dataset']:
            raise ValueError('Dataset divergente.')
        contagens = {}
        for nome, pasta in [('corrigidos', destino), ('controles', destino / 'controles')]:
            locais = indice(pasta)
            for local in locais.values():
                verificar_arquivos(local, ler_json(local / 'auditoria.json')['arquivos'])
            contagens[nome] = len(locais)
        recibo.update(status='aprovado', fim_utc=agora(), ajustes_integros=contagens,
                      arquivos_referencia_integros=len(antes), fontes='integras', dataset=dataset['id'], lock='livre antes da retomada')
except Exception as erro:
    recibo.update(status='falha', erro=repr(erro), fim_utc=agora())
    raise
finally:
    salvar_json(registro / 'verificacao.json', recibo)
    print(json.dumps({'registro': str(registro), **recibo}, ensure_ascii=False), flush=True)
