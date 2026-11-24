"""Auditoria do catalogo com localizacao explicita de fontes historicas arquivadas."""
import argparse
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from manutencao import auditar_catalogo as base
from manutencao.arquivo_fontes import ArquivoFontes
from infraestrutura.caminhos import RAIZ


class AuditorOrganizado(base.Auditor):
    def __init__(self, raiz, integridade=False):
        super().__init__(raiz, integridade)
        self.arquivo = ArquivoFontes(raiz)
        self.arquivados = set()

    def existe(self, relativo):
        if self.caminho(relativo).exists():
            return True
        if self.arquivo.contem(relativo):
            self.arquivados.add(str(relativo).replace('\\', '/'))
            return True
        self.ausentes.add(str(relativo))
        return False

    def ler(self, relativo):
        if not self.existe(relativo):
            return None
        if self.caminho(relativo).exists():
            return json.loads(self.caminho(relativo).read_text(encoding='utf-8-sig'))
        return json.loads(self.arquivo.ler(relativo))

    def conferir(self, relativo, esperado):
        if self.caminho(relativo).exists():
            return super().conferir(relativo, esperado)
        if not self.existe(relativo):
            return
        relativo = str(relativo)
        if relativo not in self.hashes:
            self.hashes[relativo] = hashlib.sha256(self.arquivo.ler(relativo)).hexdigest()
        if self.hashes[relativo] != esperado:
            self.erros.append(f'Hash divergente: {relativo}')


def auditar(raiz, integridade=False):
    original = base.Auditor
    try:
        base.Auditor = AuditorOrganizado
        return base.auditar(raiz, integridade=integridade)
    finally:
        base.Auditor = original


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--integridade', action='store_true')
    p.add_argument('--exigir-completo', action='store_true')
    a = p.parse_args()
    raiz = RAIZ
    instante = datetime.now(timezone.utc)
    destino = raiz / 'registros/revisoes' / instante.strftime('catalogo_organizado_%Y-%m-%dT%H%M%S.%fZ')
    destino.mkdir(parents=True, exist_ok=False)
    auditor, resultado = auditar(raiz, a.integridade)
    resultado.update(utc=instante.isoformat(), host=platform.node(),
                     integridade_artefatos=a.integridade, exigir_completo=a.exigir_completo,
                     fontes_localizadas_no_arquivo=sorted(auditor.arquivados),
                     catalogo_sha256=hashlib.sha256((raiz/'registros/catalogo_estudos.json').read_bytes()).hexdigest(),
                     limites='Mesmo criterio de hashes e cobertura do auditor original; fontes encerradas localizadas pelo indice explicito e bytes originais. Nao recalcula metricas, nao certifica brutos/legado integralmente nem backup externo.')
    resultado['git'] = base.situacao(raiz, auditor.fontes)
    for fonte in resultado['git']['fontes_no_commit']:
        if fonte['comparacao_checkout_HEAD'] == 'ausente_localmente' and auditor.arquivo.contem(fonte['caminho']):
            fonte['comparacao_checkout_HEAD'] = 'preservado_no_arquivo_historico'
    verificadores = [Path(__file__), Path(base.__file__), Path(__file__).with_name('arquivo_fontes.py'),
                     RAIZ/'codigo/infraestrutura/fontes_historicas.py', RAIZ/'codigo/infraestrutura/caminhos.py']
    with ZipFile(destino/'verificadores.zip', 'w', compression=ZIP_DEFLATED) as z:
        for fonte in verificadores:
            z.writestr(fonte.name, fonte.read_bytes())
    resultado['verificadores'] = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in verificadores}
    (destino/'catalogo.json').write_bytes((raiz/'registros/catalogo_estudos.json').read_bytes())
    (destino/'resumo.json').write_text(json.dumps(resultado,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':resultado['status'],'hashes':resultado['hashes_verificados'],
                      'arquivados':len(auditor.arquivados),'recibo':str(destino/'resumo.json')},ensure_ascii=False), flush=True)
    return int(bool(auditor.erros) or a.exigir_completo and bool(auditor.ausentes))


if __name__ == '__main__':
    raise SystemExit(main())
