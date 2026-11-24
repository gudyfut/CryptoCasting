"""Consulta e recuperacao verificadas das fontes de desenvolvimento encerrado."""
import argparse
import json
from pathlib import Path
from infraestrutura.caminhos import RAIZ
from infraestrutura.fontes_historicas import ArquivoFontes


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('acao', choices=['listar', 'conferir', 'extrair'])
    p.add_argument('--prefixo', default='')
    p.add_argument('--destino', type=Path)
    a = p.parse_args()
    arquivo = ArquivoFontes(RAIZ)
    nomes = sorted(n for n in arquivo.entradas if n.startswith(a.prefixo))
    if a.acao == 'listar':
        print(json.dumps({n: arquivo.entradas[n] for n in nomes}, ensure_ascii=False, indent=2))
    elif a.acao == 'conferir':
        print(json.dumps({'status': 'conferido', 'fontes': arquivo.conferir()}))
    else:
        if a.destino is None:
            p.error('--destino e obrigatorio para extrair')
        print(json.dumps({'extraidos': arquivo.extrair(a.destino, a.prefixo)}))


if __name__ == '__main__':
    main()
