"""Retomada explícita após falha operacional, preservando a execução congelada.

Sem --retomar, apenas verifica os resultados existentes. Não repete células
auditadas: a retomada utiliza o executor científico original, sem modificá-lo.
"""
import argparse
import fcntl
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from previsao24.arquivos import RAIZ, agora, identidade, ler_json, salvar_json, sha256, verificar_arquivos
from previsao24.configuracao import celulas


def verificar(execucao):
    ponteiro = ler_json(RAIZ / 'registros/execucao_atual.json')
    if ponteiro['id'] != execucao:
        raise ValueError('A identidade ativa diverge da solicitada.')
    pasta = RAIZ / ponteiro['caminho']
    registro = ler_json(pasta / 'execucao.json')
    assinatura = registro['assinatura']
    verificar_arquivos(RAIZ, assinatura['fontes'])
    verificar_arquivos(pasta / 'fontes', assinatura['fontes'])
    congelamento = ler_json(pasta / 'congelamento.json')
    if congelamento['status'] != 'congelado' or congelamento['assinatura'] != identidade(assinatura):
        raise ValueError('Congelamento incompatível.')
    progresso = ler_json(pasta / 'progresso_avaliacao.json')
    coordenador = ler_json(RAIZ / 'registros/continuacao_protocolo.json')
    processo = ler_json(pasta / 'processo.json')
    if progresso['status'] != 'falha' or coordenador['status'] != 'falha':
        raise ValueError('A retomada exige falha terminal registrada, não timeout.')
    for anterior in (processo, coordenador):
        try:
            os.kill(anterior['pid'], 0)
        except ProcessLookupError:
            pass
        else:
            raise RuntimeError(f"PID {anterior['pid']} ainda existe; não retomar.")
    c = assinatura['configuracao']
    grade = celulas(c, 'avaliacao')
    esperadas = celulas(c, 'desenvolvimento') + grade
    esperadas += [{'par': p, 'fold': f, 'modelo': m}
                  for f in c['folds_desenvolvimento'] + c['folds_avaliacao']
                  for p in c['pares'] for m in ('naive', 'arima')]
    permitidas = {identidade(x)[:20]: x for x in esperadas}
    encontradas = {}
    auditorias = {}
    tentativas = {}
    for caminho in sorted(pasta.glob('celulas/*/tentativa_*/tentativa.json')):
        tentativa = ler_json(caminho)
        x = tentativa['celula']
        chave = identidade(x)[:20]
        if permitidas.get(chave) != x or caminho.parent.parent.name != chave:
            raise ValueError('Célula fora da grade ou identidade incorreta.')
        tentativas[caminho.relative_to(pasta).as_posix()] = sha256(caminho)
        if tentativa['status'] != 'auditada':
            raise ValueError(f'Tentativa exige investigação individual: {caminho}')
        if chave in encontradas:
            raise ValueError('Mais de uma tentativa auditada por célula.')
        auditoria = ler_json(caminho.parent / 'auditoria.json')
        if auditoria['status'] != 'aprovado' or auditoria['celula'] != x:
            raise ValueError('Auditoria incompatível.')
        verificar_arquivos(caminho.parent, auditoria['arquivos'])
        encontradas[chave] = x
        auditorias[caminho.parent.relative_to(pasta).as_posix()] = sha256(caminho.parent / 'auditoria.json')
    desenvolvimento = {identidade(x)[:20]: x for x in esperadas if x['fold'] in c['folds_desenvolvimento']}
    avaliacao = {k: x for k, x in encontradas.items() if x['fold'] in c['folds_avaliacao']}
    prefixo = {identidade(x)[:20]: x for x in grade[:progresso['concluidos']]}
    if avaliacao != prefixo or {k: x for k, x in encontradas.items() if x['fold'] in c['folds_desenvolvimento']} != desenvolvimento:
        raise ValueError('Cobertura não corresponde ao desenvolvimento completo e prefixo auditado da avaliação.')
    for relativo, esperado in congelamento['auditorias_desenvolvimento'].items():
        if auditorias.get(relativo) != esperado:
            raise ValueError('Auditoria do desenvolvimento difere do congelamento.')
    evidencia = {'status': 'integridade_verificada_para_retomada', 'utc': agora(), 'execucao': execucao,
                 'desenvolvimento': len(desenvolvimento), 'avaliacao_neurais': len(avaliacao),
                 'auditorias': auditorias, 'tentativas': tentativas,
                 'assinatura': identidade(assinatura), 'congelamento_sha256': sha256(pasta / 'congelamento.json'),
                 'verificador_sha256': sha256(Path(__file__))}
    return pasta, evidencia


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execucao', required=True)
    parser.add_argument('--retomar', action='store_true')
    args = parser.parse_args()
    with (RAIZ / 'registros/continuacao_protocolo.lock').open('a') as bloqueio:
        fcntl.flock(bloqueio, fcntl.LOCK_EX | fcntl.LOCK_NB)
        pasta, evidencia = verificar(args.execucao)
        print(f"Integridade: {evidencia['desenvolvimento']} resultados de desenvolvimento e {evidencia['avaliacao_neurais']} ajustes de avaliação; fontes e congelamento conferidos.", flush=True)
        if not args.retomar:
            return
        incidente = RAIZ / 'registros/incidentes' / f"retomada_{args.execucao}_{agora().replace(':', '').replace('+', '_')}"
        incidente.mkdir(parents=True)
        originais = [pasta / 'progresso_avaliacao.json', pasta / 'processo.json',
                     RAIZ / 'registros/continuacao_protocolo.json',
                     RAIZ / 'registros/logs' / f'avaliar_{args.execucao}.log',
                     RAIZ / 'registros/logs/continuacao_20261020.log']
        preservados = {}
        for origem in originais:
            destino = incidente / origem.name
            shutil.copyfile(origem, destino)
            if sha256(origem) != sha256(destino):
                raise ValueError('Cópia do incidente divergente.')
            preservados[destino.name] = sha256(destino)
        evidencia.update(preservados=preservados,
                         causa_observada='PermissionError no replace do progresso após auditoria da célula; processo encerrado.',
                         causa_provavel='Contenção transitória de arquivo no volume Windows/WSL; processo responsável não identificado.',
                         mitigacao='Monitorar arquivos de estado pelo WSL; não manter leitura Windows do arquivo durante substituição. Sem alteração científica.')
        salvar_json(incidente / 'verificacao.json', evidencia)
        print(f'Incidente preservado: {incidente}', flush=True)
        estado = {'execucao': args.execucao, 'pid': os.getpid(), 'inicio_utc': agora(),
                  'retomada_incidente': incidente.relative_to(RAIZ).as_posix(),
                  'ajustes_avaliacao_preservados': evidencia['avaliacao_neurais']}
        try:
            passos = [('avaliar', ['run_previsao.py', 'executar', '--fase', 'avaliacao']),
                      ('consolidar_avaliacao', ['manutencao/consolidar_resultados.py', '--fase', 'avaliacao']),
                      ('exportar', ['manutencao/exportar_portal.py'])]
            for nome, comando in passos:
                if ler_json(RAIZ / 'registros/execucao_atual.json')['id'] != args.execucao:
                    raise ValueError('Identidade ativa mudou.')
                verificar_arquivos(RAIZ, ler_json(pasta / 'execucao.json')['assinatura']['fontes'])
                estado.update(status=nome, atualizado_utc=agora())
                salvar_json(RAIZ / 'registros/continuacao_protocolo.json', estado)
                log = incidente / f'{nome}_retomada.log'
                print(f'{agora()} {nome}: {log}', flush=True)
                with log.open('x') as saida:
                    retorno = subprocess.run([sys.executable, '-u', *comando], cwd=RAIZ, stdout=saida, stderr=subprocess.STDOUT)
                if retorno.returncode:
                    raise RuntimeError(f'{nome} terminou com código {retorno.returncode}; sem reinício automático.')
            estado.update(status='execucao_e_publicacao_concluidas_aguardando_aceite', fim_utc=agora())
        except Exception as erro:
            estado.update(status='falha', erro=f'{type(erro).__name__}: {erro}', fim_utc=agora())
            raise
        finally:
            salvar_json(RAIZ / 'registros/continuacao_protocolo.json', estado)


if __name__ == '__main__':
    main()
