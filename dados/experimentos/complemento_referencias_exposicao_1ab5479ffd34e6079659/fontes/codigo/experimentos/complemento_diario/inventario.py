"""Inventário e preservação anteriores a resultados novos de mercado."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import platform
import shutil
import subprocess
import sys
import time

from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256

REG = RAIZ / 'registros/complemento_diario'
CFG = RAIZ / 'configuracoes/complemento_diario_001.json'
PROTOCOLO = RAIZ / 'docs/protocolo_complemento_diario.md'


def relativo(p):
    return Path(p).resolve().relative_to(RAIZ.resolve()).as_posix()


def iniciar(autorizacao):
    REG.mkdir(parents=True, exist_ok=True)
    origem = Path(autorizacao)
    if (REG / 'inicio.json').exists():
        assert sha256(origem) == ler_json(REG / 'inicio.json')['autorizacao_sha256']
        return ler_json(REG / 'inicio.json')
    shutil.copyfile(origem, REG / 'autorizacao.txt')
    instante = datetime.now(timezone.utc)
    protegidos = {}
    for p in sorted((RAIZ / 'escrita_tcc').rglob('*')):
        if p.is_file() and 'build' not in p.relative_to(RAIZ / 'escrita_tcc').parts:
            protegidos[relativo(p)] = sha256(p)
    salvar_json(REG / 'artigo_preservado.json', protegidos)
    documentos = ['plano.md', 'registros/catalogo_estudos.json', 'docs/andamento.md',
                  'docs/README.md', 'docs/resultados_lstm_diaria.md',
                  'docs/resultados_walkforward_diario.md', 'docs/resultados_ablacao_linear_diaria.md']
    preservados = {}
    for nome in documentos:
        origem_doc = RAIZ / nome
        destino = REG / 'documentos_anteriores' / nome
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(origem_doc, destino)
        preservados[nome] = sha256(destino)
    salvar_json(REG / 'documentos_anteriores/manifesto.json', preservados)
    dados = dict(utc=instante.isoformat(), host=platform.node(), python=sys.executable,
                 autorizacao_sha256=sha256(origem), configuracao_sha256=sha256(CFG),
                 protocolo_sha256=sha256(PROTOCOLO),
                 meta_desenvolvimento_utc=(instante + timedelta(days=4)).isoformat(),
                 limite_timestamp_auditado_utc=(instante + timedelta(days=5)).isoformat(),
                 horizonte_entrega_utc=(instante + timedelta(days=7)).isoformat(),
                 artigo_preservado_arquivos=len(protegidos),
                 disco=shutil.disk_usage(RAIZ)._asdict(), escopo='autorizacao.txt')
    salvar_json(REG / 'inicio.json', dados)
    salvar_json(REG / 'estado.json', dict(utc=agora(), situacao='inventariando',
                                        treinos_novos=0, artigo_alterado=False))
    return dados


def conferir_mapa(base, mapa, erros, conferidos):
    base = Path(base).resolve()
    for nome, esperado in mapa.items():
        p = (base / nome).resolve()
        if not p.is_relative_to(base):
            erros.append(dict(arquivo=str(p), motivo='fora_da_raiz'))
            continue
        if not p.is_file():
            erros.append(dict(arquivo=relativo(p), motivo='ausente', esperado=esperado))
            continue
        chave = relativo(p)
        anterior = conferidos.get(chave)
        if anterior is not None and anterior['sha256'] == esperado:
            continue
        observado = sha256(p)
        if observado != esperado:
            erros.append(dict(arquivo=chave, motivo='hash_divergente',
                              esperado=esperado, observado=observado))
        else:
            conferidos[chave] = dict(sha256=observado, bytes=p.stat().st_size)


def executar():
    assert (REG / 'inicio.json').exists()
    c = ler_json(CFG)
    erros, conferidos, pais = [], {}, {}
    inicio = time.monotonic()
    for nome, arquivo in c['referencias'].items():
        ptr = ler_json(RAIZ / arquivo)
        p = RAIZ / ptr['pasta']
        conferir_mapa(p, {'congelamento.json': ptr['congelamento_sha256']}, erros, conferidos)
        f = ler_json(p / 'congelamento.json')
        # O ciclo de continuidade publica o fechamento no registro, diferente
        # dos ciclos neurais. Isso é layout histórico, não artefato faltante.
        caminho_fecho = p / 'fechamento.json'
        if not caminho_fecho.exists() and nome == 'continuidade':
            caminho_fecho = (RAIZ / arquivo).parent / 'fechamento.json'
        fecho = ler_json(caminho_fecho)
        if nome == 'continuidade':
            conferir_mapa(RAIZ, fecho['evidencias'], erros, conferidos)
        if 'arquivos' in fecho:
            conferir_mapa(p, fecho['arquivos'], erros, conferidos)
        if (p / 'manifesto.json').exists():
            if 'manifesto_sha256' in fecho:
                conferir_mapa(p, {'manifesto.json': fecho['manifesto_sha256']}, erros, conferidos)
            conferir_mapa(p, ler_json(p / 'manifesto.json')['arquivos'], erros, conferidos)
        if 'fontes' in f and (p / 'fontes').is_dir():
            conferir_mapa(p / 'fontes', f['fontes'], erros, conferidos)
        auditorias = []
        pasta_reg = (RAIZ / arquivo).parent
        for q in sorted(pasta_reg.glob('conferencia*.json')):
            auditorias.append(dict(arquivo=relativo(q), sha256=sha256(q),
                                   chaves=list(ler_json(q))))
        pais[nome] = dict(ponteiro=ptr, fechamento_situacao=fecho.get('situacao'),
                         fechamento_arquivo=relativo(caminho_fecho),
                         fechamento_sha256=sha256(caminho_fecho), auditorias=auditorias,
                         chaves_congelamento=list(f))
        print('PAI_CONFERIDO', nome, 'arquivos', len(conferidos), 'erros', len(erros), flush=True)
    # Mercados e preparações que sustentam os cinco pais; seus hashes também
    # precisam estar disponíveis, não somente os ponteiros e a publicação.
    for nome in ('lstm', 'walkforward'):
        p = RAIZ / pais[nome]['ponteiro']['pasta']
        f = ler_json(p / 'congelamento.json')
        dependencias = f.get('dependencias', f.get('referencias', {}).get('arquivos', {}))
        conferir_mapa(RAIZ, dependencias, erros, conferidos)
    registros = subprocess.run(['git', 'status', '--short'], cwd=RAIZ,
                               capture_output=True, text=True, encoding='utf-8').stdout
    (REG / 'git_status_inicio.txt').write_text(registros, encoding='utf-8')
    salvar_json(REG / 'inventario.json', dict(utc=agora(), situacao='aprovado' if not erros else 'divergencias',
                 pais=pais, arquivos=conferidos, erros=erros, segundos=time.monotonic()-inicio,
                 bytes_conferidos=sum(v['bytes'] for v in conferidos.values()),
                 limite='Integridade local; qualificação CUDA e controles científicos ainda pendentes.'))
    print(json.dumps(dict(arquivos=len(conferidos), erros=len(erros),
                          segundos=time.monotonic()-inicio), ensure_ascii=False), flush=True)
    if erros:
        print(json.dumps(erros[:12], ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--autorizacao')
    args = p.parse_args()
    if args.autorizacao:
        print(json.dumps(iniciar(args.autorizacao), ensure_ascii=False), flush=True)
    executar()
