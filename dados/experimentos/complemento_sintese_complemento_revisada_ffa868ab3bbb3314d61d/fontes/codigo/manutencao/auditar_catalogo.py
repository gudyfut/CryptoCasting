"""Auditoria posterior de rastreabilidade. Não importa nem executa código de treino."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import platform
import subprocess


def identidade(valor):
    return hashlib.sha256(json.dumps(valor, sort_keys=True, ensure_ascii=False,
                                     allow_nan=False).encode()).hexdigest()


def chave(celula):
    return tuple(celula.get(k) for k in ('par', 'fold', 'contexto', 'seed', 'modelo'))


def grade(configuracao, modelos, baselines=()):
    blocos = configuracao['folds_desenvolvimento'] + configuracao['folds_avaliacao']
    saida = set(itertools.product(configuracao['pares'], blocos,
                                 configuracao['contextos'], configuracao['seeds'], modelos))
    saida.update((par, bloco, None, None, modelo) for par, bloco, modelo in
                 itertools.product(configuracao['pares'], blocos, baselines))
    return saida


def comparar_cobertura(esperadas, observadas):
    contagens = Counter(observadas)
    ordenar = lambda valores: sorted(valores, key=str)
    return {'esperadas': len(esperadas), 'auditadas': len(observadas),
            'faltantes': ordenar(esperadas - contagens.keys()),
            'inesperadas': ordenar(contagens.keys() - esperadas),
            'duplicadas': ordenar(k for k, n in contagens.items() if n > 1)}


class Auditor:
    def __init__(self, raiz, integridade=False):
        self.raiz = Path(raiz).resolve()
        self.integridade = integridade
        self.erros, self.ausentes, self.avisos = [], set(), []
        self.hashes, self.fontes = {}, {}

    def caminho(self, relativo):
        if Path(relativo).is_absolute() or ':' in str(relativo):
            raise ValueError(f'Caminho não relativo: {relativo}')
        caminho = (self.raiz / relativo).resolve()
        if not caminho.is_relative_to(self.raiz):
            raise ValueError(f'Caminho fora do projeto: {relativo}')
        return caminho

    def existe(self, relativo):
        existe = self.caminho(relativo).exists()
        if not existe:
            self.ausentes.add(str(relativo))
        return existe

    def ler(self, relativo):
        if not self.existe(relativo):
            return None
        return json.loads(self.caminho(relativo).read_text(encoding='utf-8-sig'))

    def conferir(self, relativo, esperado):
        if not self.existe(relativo):
            return
        relativo = str(relativo)
        if relativo not in self.hashes:
            resumo = hashlib.sha256()
            with self.caminho(relativo).open('rb') as arquivo:
                for trecho in iter(lambda: arquivo.read(1024 * 1024), b''):
                    resumo.update(trecho)
            self.hashes[relativo] = resumo.hexdigest()
        if self.hashes[relativo] != esperado:
            self.erros.append(f'Hash divergente: {relativo}')

    def manifesto(self, base, arquivos, verificar=True):
        for relativo, esperado in arquivos.items():
            caminho = str(Path(base) / relativo)
            if verificar:
                self.conferir(caminho, esperado)
            else:
                self.existe(caminho)

    def tentativas(self, base, esperadas):
        if not self.existe(base):
            return {'disponibilidade': 'ausente', 'auditadas': None,
                    'esperadas': len(esperadas)}
        observadas, estados = [], Counter()
        for arquivo in sorted(self.caminho(base).glob('*/tentativa_*/tentativa.json')):
            relativo = arquivo.relative_to(self.raiz)
            tentativa = self.ler(str(relativo))
            estados[tentativa['status']] += 1
            if tentativa['status'] != 'auditada':
                continue
            celula = chave(tentativa['celula'])
            observadas.append(celula)
            auditoria = self.ler(str(relativo.parent / 'auditoria.json'))
            if auditoria:
                if auditoria.get('status') != 'aprovado' or chave(auditoria['celula']) != celula:
                    self.erros.append(f'Auditoria incompatível: {relativo}')
                self.manifesto(relativo.parent, auditoria['arquivos'], self.integridade)
        cobertura = comparar_cobertura(esperadas, observadas)
        if cobertura['faltantes']:
            self.ausentes.add(f'{base}: {len(cobertura["faltantes"])} células auditadas ausentes')
        if cobertura['inesperadas'] or cobertura['duplicadas']:
            self.erros.append(f'Cobertura inesperada/duplicada: {base}')
        return {**cobertura, 'estados_tentativas': dict(estados)}

    def estudo(self, estudo):
        if estudo['tipo'] in ('busca_adaptativa_assistida_ia',
                              'comparacao_receitas_executor_comum',
                              'busca_local_adaptativa_T_V_S'):
            return self.registro_indexado(estudo)
        fontes = estudo['fontes']
        for caminho in fontes.values():
            self.existe(caminho)
        if estudo.get('decisao'):
            self.existe(estudo['decisao'])
        saida = {'chave': estudo['chave'], 'execucao': estudo['execucao'],
                 'situacao_historica_declarada': estudo['situacao_historica']}
        if estudo['tipo'] == 'historico_arquivado':
            saida['escopo'] = 'Links e presença de recibos; não reaudita os arquivos do legado.'
            return saida
        if estudo['tipo'] not in ('referencia', 'extensao_controlada'):
            raise ValueError(f'Layout sem adaptador: {estudo["tipo"]}')
        execucao = self.ler(fontes['execucao'])
        if execucao is None:
            return {**saida, 'disponibilidade': 'execucao_ausente', 'auditadas': None}
        assinatura = execucao['assinatura']
        codigo = identidade(assinatura)
        if codigo[:20] != estudo['execucao'] or execucao['id'] != estudo['execucao']:
            self.erros.append(f'Identidade de execução divergente: {estudo["chave"]}')
        if assinatura['dataset'] != estudo['dataset']:
            self.erros.append(f'Dataset divergente: {estudo["chave"]}')
        congelamento = self.ler(fontes['congelamento'])
        if congelamento and congelamento['assinatura'] != codigo:
            self.erros.append(f'Congelamento divergente: {estudo["chave"]}')
        base = estudo['raiz']
        self.manifesto(Path(base) / 'fontes', assinatura['fontes'])
        self.manifesto('', assinatura['fontes'])
        self.fontes.update(assinatura['fontes'])
        configuracao = self.ler(fontes['configuracao'])
        if configuracao is not None and configuracao != assinatura['configuracao']:
            self.erros.append(f'Configuração diferente da assinatura: {estudo["chave"]}')
        dataset = self.ler(fontes['dataset'])
        if dataset:
            if dataset['id'] != estudo['dataset'] or identidade(dataset['assinatura'])[:20] != dataset['id']:
                self.erros.append(f'Identidade do dataset divergente: {estudo["chave"]}')
            self.manifesto(Path(fontes['dataset']).parent, dataset['arquivos'], self.integridade)
        fechamento = self.ler(fontes['fechamento'])
        if fechamento and (fechamento['execucao'] != estudo['execucao'] or fechamento['status'] != 'aprovado'):
            self.erros.append(f'Fechamento incompatível: {estudo["chave"]}')
        if estudo['tipo'] == 'referencia':
            esperadas = grade(assinatura['configuracao'], ['mamba', 'lstm'], ['naive', 'arima'])
        else:
            esperadas = grade(assinatura['configuracao_treino'], ['mamba'])
            controles = {chave(c) for c in assinatura['configuracao']['controles_reexecutados']}
            saida['controles'] = self.tentativas(str(Path(base) / 'controles/celulas'), controles)
            self.conferir(fontes['dataset'], assinatura['dataset_manifesto_sha256'])
            self.conferir(str(Path(execucao['referencia_caminho']) / 'execucao.json'),
                          assinatura['referencia_execucao_sha256'])
            if assinatura['referencia'] != estudo['heranca']['execucao']:
                self.erros.append(f'Herança diferente da assinatura: {estudo["chave"]}')
        saida['cobertura'] = self.tentativas(str(Path(base) / 'celulas'), esperadas)
        saida['publicacoes'] = {}
        for fase, pasta in estudo['publicacoes'].items():
            caminho = str(Path(pasta) / 'publicacao.json')
            manifesto = self.ler(caminho)
            if manifesto:
                self.manifesto(pasta, manifesto['arquivos'])
                if fechamento:
                    esperado = (fechamento['publicacoes'][fase]['manifesto_sha256']
                                if estudo['tipo'] == 'referencia' else fechamento['publicacoes_sha256'][fase])
                    self.conferir(caminho, esperado)
                saida['publicacoes'][fase] = {'arquivos_manifestados': len(manifesto['arquivos'])}
        return saida

    def registro_indexado(self, registro):
        """Layouts recentes: vínculos e congelamento, sem fingir reauditoria de treinos."""
        chave = registro.get('chave') or registro.get('id') or 'etapa_atual'
        campos = ('protocolo', 'decisao', 'estado', 'ponteiro', 'fechamento', 'relatorio',
                  'desenho', 'qualificacao', 'configuracao', 'autorizacao',
                  'conferencia_posterior', 'publicacao', 'proposta', 'indice')
        for campo in campos:
            valor = registro.get(campo)
            if isinstance(valor, str) and valor.startswith(('docs/', 'registros/', 'dados/', 'arquivo/', 'configuracoes/')):
                self.existe(valor)
        ponteiro = self.ler(registro['ponteiro']) if registro.get('ponteiro') else None
        if ponteiro:
            if ponteiro.get('id') != registro.get('execucao'):
                self.erros.append(f'Ponteiro divergente do catálogo: {chave}')
            if 'pasta' not in ponteiro or 'congelamento_sha256' not in ponteiro:
                self.erros.append(f'Ponteiro sem vínculo de congelamento: {chave}')
            else:
                self.conferir(str(Path(ponteiro['pasta']) / 'congelamento.json'), ponteiro['congelamento_sha256'])
        return {'chave': chave, 'execucao': registro.get('execucao'),
                'escopo': 'Presença de vínculos e hash do congelamento. Cobertura/métricas exigem a conferência própria do ciclo.',
                'auditadas': None, 'situacao_historica_declarada': registro.get('situacao_historica', registro.get('situacao'))}


def validar_relacoes(catalogo):
    estudos = catalogo['estudos']
    for campo in ('chave', 'execucao'):
        valores = [e[campo] for e in estudos]
        if len(valores) != len(set(valores)):
            raise ValueError(f'{campo} duplicado no catálogo')
    indice = {e['chave']: e for e in estudos}
    for estudo in estudos:
        caminho, atual = set(), estudo
        while atual.get('antecessor'):
            if atual['chave'] in caminho:
                raise ValueError('Ciclo na relação de antecessores')
            caminho.add(atual['chave'])
            atual = indice[atual['antecessor']]
        if estudo.get('heranca') and estudo['heranca']['execucao'] != indice[estudo['antecessor']]['execucao']:
            raise ValueError('Herança não corresponde ao antecessor')


def situacao(raiz, fontes):
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=raiz, stderr=subprocess.DEVNULL)
    novos = [p.decode('utf-8') for p in git('ls-files', '--others', '--exclude-standard', '-z').split(b'\0') if p]
    volumes = [(p, (raiz / p).stat().st_size) for p in novos if (raiz / p).is_file()]
    arquivos = []
    for relativo in sorted(fontes):
        try:
            blob = git('show', f'HEAD:{relativo}')
        except subprocess.CalledProcessError:
            estado = 'ausente_no_commit'
        else:
            local = raiz / relativo
            if not local.exists():
                estado = 'ausente_localmente'
            else:
                dados = local.read_bytes()
                estado = ('identico' if dados == blob else 'somente_finais_de_linha'
                          if dados.replace(b'\r\n', b'\n') == blob.replace(b'\r\n', b'\n')
                          else 'conteudo_diferente')
        arquivos.append({'caminho': relativo, 'comparacao_checkout_HEAD': estado})
    return {'commit': git('rev-parse', 'HEAD').decode().strip(),
            'nao_rastreados_elegiveis': len(novos), 'bytes_nao_rastreados': sum(n for _, n in volumes),
            'maiores_nao_rastreados': sorted(volumes, key=lambda p: p[1], reverse=True)[:10],
            'fontes_no_commit': arquivos,
            'limite': 'Snapshot local, não verifica push, backup ou máquina remota. Diferenças LF/CRLF não são aceitas nos hashes científicos.'}


def auditar(raiz, catalogo='registros/catalogo_estudos.json', integridade=False):
    auditor = Auditor(raiz, integridade)
    resultados = []
    dados = auditor.ler(catalogo)
    if dados is not None:
        validar_relacoes(dados)
        for nome in ('cronologia', 'procedimento'):
            auditor.existe(dados[nome])
        for proposta in dados.get('propostas_historicas_nao_executadas', []):
            auditor.existe(proposta['fonte'])
            auditor.existe(proposta['configuracao'])
        for estudo in dados['estudos']:
            resultados.append(auditor.estudo(estudo))
        for linha in dados.get('linhas_pesquisa', []):
            if linha.get('ponteiro'):
                resultados.append(auditor.registro_indexado(linha))
    return auditor, {'estudos': resultados, 'erros': auditor.erros,
                     'ausentes': sorted(auditor.ausentes), 'hashes_verificados': len(auditor.hashes),
                     'status': 'divergente' if auditor.erros else 'parcial' if auditor.ausentes else 'conferido'}


def main():
    argumentos = argparse.ArgumentParser(description=__doc__)
    argumentos.add_argument('--integridade', action='store_true')
    argumentos.add_argument('--exigir-completo', action='store_true')
    opcoes = argumentos.parse_args()
    raiz = Path(__file__).resolve().parents[1]
    instante = datetime.now(timezone.utc)
    destino = raiz / 'registros/revisoes' / instante.strftime('catalogo_%Y-%m-%dT%H%M%S.%fZ')
    destino.mkdir(parents=True, exist_ok=False)
    resumo = {'utc': instante.isoformat(), 'host': platform.node(), 'python': platform.python_version(),
              'integridade_artefatos': opcoes.integridade,
              'exigir_completo': opcoes.exigir_completo,
              'limites': 'Não recalcula métricas, não recarrega modelos, não verifica brutos/legado integralmente nem comprova backup externo.'}
    try:
        auditor, conferencia = auditar(raiz, integridade=opcoes.integridade)
        resumo.update(conferencia)
        resumo['git'] = situacao(raiz, auditor.fontes)
        resumo['catalogo_sha256'] = hashlib.sha256((raiz / 'registros/catalogo_estudos.json').read_bytes()).hexdigest()
        codigo = int(bool(auditor.erros) or (opcoes.exigir_completo and bool(auditor.ausentes)))
    except Exception as erro:
        resumo.update(status='falha_do_verificador', erro=f'{type(erro).__name__}: {erro}')
        codigo = 1
    resumo['verificador_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (destino / 'verificador.py').write_bytes(Path(__file__).read_bytes())
    (destino / 'catalogo.json').write_bytes((raiz / 'registros/catalogo_estudos.json').read_bytes())
    (destino / 'resumo.json').write_text(json.dumps(resumo, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': resumo['status'], 'recibo': str(destino / 'resumo.json')}, ensure_ascii=False))
    return codigo


if __name__ == '__main__':
    raise SystemExit(main())
