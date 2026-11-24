"""Artefatos identificados por conteúdo, publicação completa e falhas preservadas."""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import traceback
from uuid import uuid4

RAIZ = Path(__file__).resolve().parents[1]


def agora():
    return datetime.now(timezone.utc).isoformat()


def identidade(valor):
    texto = json.dumps(valor, sort_keys=True, ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()


def sha256(caminho):
    h = hashlib.sha256()
    with Path(caminho).open('rb') as f:
        for bloco in iter(lambda: f.read(4*1024*1024), b''):
            h.update(bloco)
    return h.hexdigest()


def ler_json(caminho):
    return json.loads(Path(caminho).read_text(encoding='utf-8-sig'))


def salvar_json(caminho, valor):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_name(caminho.name + '.' + uuid4().hex + '.parcial')
    temporario.write_text(json.dumps(valor, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    os.replace(temporario, caminho)


def relativo(caminho):
    p = Path(caminho).resolve()
    return p.relative_to(RAIZ).as_posix() if p.is_relative_to(RAIZ) else str(p)


def conferir_arquivos(pasta, arquivos):
    pasta = Path(pasta).resolve()
    for nome, esperado in arquivos.items():
        p = (pasta / nome).resolve()
        if not p.is_relative_to(pasta) or not p.is_file() or sha256(p) != esperado:
            raise ValueError(f'Artefato ausente ou alterado: {nome}')


def fontes(*pacotes):
    return {p.relative_to(RAIZ).as_posix(): sha256(p)
            for pacote in pacotes for p in sorted((RAIZ / pacote).glob('*.py'))}


def abrir_artefato(pasta, tipo=None, _visitados=None):
    pasta = Path(pasta).resolve()
    visitados=set() if _visitados is None else _visitados
    if pasta in visitados:
        raise ValueError('Dependência circular entre artefatos.')
    visitados.add(pasta)
    m = ler_json(pasta / 'manifesto.json')
    if m['id'] != identidade(m['assinatura'])[:20] or (tipo and m['tipo'] != tipo):
        raise ValueError('Tipo ou identidade de artefato inválido.')
    conferir_arquivos(pasta, m['arquivos'])
    conferir_arquivos(pasta / 'fontes', m['assinatura']['fontes'])
    for nome,esperado in m['assinatura'].get('originais',{}).items():
        p=RAIZ/nome
        if not p.is_file() or sha256(p)!=esperado:
            raise ValueError(f'Fonte original ausente ou alterada: {nome}')
    for dep in m['assinatura'].get('dependencias',[]):
        p=(RAIZ/dep['pasta']).resolve()
        if sha256(p/'manifesto.json')!=dep['manifesto_sha256']:
            raise ValueError('Manifesto de origem foi alterado.')
        abrir_artefato(p,_visitados=visitados)
    visitados.remove(pasta)
    return m


@contextmanager
def tentativa(base, tipo, assinatura):
    """Nunca sobrescreve artefato publicado; tentativa interrompida permanece visível."""
    base = Path(base).resolve()
    codigo = identidade(assinatura)[:20]
    destino = base / codigo
    if destino.exists():
        m = abrir_artefato(destino, tipo)
        if m['assinatura'] != assinatura:
            raise ValueError('Colisão de identidade.')
        yield destino, True
        return
    trabalho = base / 'tentativas' / uuid4().hex
    trabalho.mkdir(parents=True)
    salvar_json(trabalho / 'tentativa.json', {'inicio': agora(), 'tipo': tipo, 'id_planejado': codigo, 'assinatura': assinatura})
    try:
        yield trabalho, False
        for nome, esperado in assinatura['fontes'].items():
            if sha256(RAIZ / nome) != esperado:
                raise ValueError('Fonte mudou durante a preparação.')
            copia = trabalho / 'fontes' / nome
            copia.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(RAIZ / nome, copia)
        arquivos = {p.relative_to(trabalho).as_posix(): sha256(p) for p in sorted(trabalho.rglob('*')) if p.is_file()}
        salvar_json(trabalho / 'manifesto.json', {'id': codigo, 'tipo': tipo, 'criado_utc': agora(),
                    'assinatura': assinatura, 'arquivos': arquivos})
        abrir_artefato(trabalho, tipo)
        if destino.exists():
            raise FileExistsError('Outra publicação criou a identidade; conferir ambas as tentativas.')
        trabalho.rename(destino)
    except BaseException:
        if trabalho.exists():
            salvar_json(trabalho / 'falha.json', {'utc': agora(), 'erro': traceback.format_exc()})
        raise


def destino_artefato(base, assinatura):
    return Path(base).resolve() / identidade(assinatura)[:20]
