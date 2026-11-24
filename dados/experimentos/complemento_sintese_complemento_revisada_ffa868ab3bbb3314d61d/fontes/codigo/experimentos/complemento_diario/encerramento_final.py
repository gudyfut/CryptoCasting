"""Encerramento com versão de apresentação explicitamente identificada."""
import argparse
import json
from types import FunctionType
from infraestrutura.artefatos import RAIZ, conferir_arquivos, ler_json, sha256
from . import encerrar as base
from .inventario import REG, relativo


def contexto_final(etapa):
    if etapa != 'sintese_complemento':
        return base.contexto(etapa)
    revisao = ler_json(REG / 'sintese_complemento/versao_final.json')
    original, anterior, _ = base.contexto(etapa)
    assert original == revisao['original']
    conferir_arquivos(anterior, ler_json(anterior / 'fechamento.json')['arquivos'])
    resultado = base.contexto(revisao['etapa'])
    assert resultado[0] == revisao['execucao']
    fecho = revisao['fechamento']
    assert sha256(RAIZ / fecho['arquivo']) == fecho['sha256']
    registro = ler_json(resultado[1] / 'revisao_apresentacao.json')
    assert registro['tabelas_identicas'] == 18
    conferir_arquivos(anterior / 'publicacao', registro['arquivos_copiados_identicos'])
    conferir_arquivos(resultado[1] / 'publicacao', registro['arquivos_copiados_identicos'])
    return resultado


def conferir():
    globais = dict(base.conferir.__globals__, contexto=contexto_final)
    funcao = FunctionType(base.conferir.__code__, globais, base.conferir.__name__)
    resultado = funcao()
    resultado['revisao_publicacao'] = ler_json(REG / 'sintese_complemento/versao_final.json')
    resultado['fontes_encerramento'] = {relativo(p): sha256(p) for p in (base.__file__, __file__)}
    return resultado


def encerrar():
    globais = dict(base.encerrar.__globals__, conferir=conferir)
    FunctionType(base.encerrar.__code__, globais, base.encerrar.__name__)()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('acao', choices=['conferir', 'encerrar'])
    if parser.parse_args().acao == 'encerrar':
        encerrar()
    else:
        print(json.dumps(conferir(), ensure_ascii=False, indent=2))
