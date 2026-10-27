"""Conferência final somente de leitura; recibo próprio, sem regenerar qualificação."""
from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from previsao24.arquivos import RAIZ, agora, identidade, ler_json, salvar_json, sha256, verificar_arquivos
from previsao24.configuracao import celulas
from previsao24.dados import verificar_dataset


def exigir(condicao, mensagem):
    if not condicao:
        raise ValueError(mensagem)


def main():
    ponteiro = ler_json(RAIZ/'registros/execucao_atual.json')
    pasta = RAIZ/ponteiro['caminho']
    execucao = ler_json(pasta/'execucao.json')
    assinatura = execucao['assinatura']
    exigir(identidade(assinatura)[:20] == ponteiro['id'] == execucao['id'], 'Identidade divergente.')
    exigir(ler_json(RAIZ/'configuracoes/retorno24_001.json') == assinatura['configuracao'], 'Configuração alterada.')
    verificar_arquivos(RAIZ, assinatura['fontes'])
    verificar_arquivos(pasta/'fontes', assinatura['fontes'])
    exigir(ler_json(RAIZ/'registros/qualificacao/testes_atual.json') == assinatura['testes'], 'Recibo de testes alterado.')
    verificar_arquivos(RAIZ, assinatura['testes']['fontes'])
    q = assinatura['qualificacao']
    exigir(sha256(RAIZ/q['caminho']) == q['sha256'], 'Qualificação alterada.')
    congelamento = ler_json(pasta/'congelamento.json')
    exigir(congelamento['assinatura'] == identidade(assinatura) and congelamento['status'] == 'congelado', 'Congelamento incompatível.')
    exigir(congelamento['exposicao'] == ler_json(RAIZ/'registros/exposicao_previa.json'), 'Declaração de exposição alterada.')
    print('Fontes, snapshot, configuração, qualificação, testes e congelamento conferidos.', flush=True)
    dataset = verificar_dataset(RAIZ/execucao['dataset_caminho'])
    exigir(dataset['id'] == assinatura['dataset'], 'Dataset divergente.')
    for chave, esperado in dataset['assinatura']['brutos'].items():
        par, mes = chave.split('/')
        exigir(sha256(RAIZ/'dados/brutos/binance_spot_1m'/par/f'{par}-1m-{mes}.zip') == esperado, 'Fonte bruta alterada.')
    exigir(len(dataset['assinatura']['brutos']) == 240, 'Coleta incompleta.')
    print('Dataset e 240 fontes brutas conferidos.', flush=True)
    c = assinatura['configuracao']
    esperadas = celulas(c, 'desenvolvimento') + celulas(c, 'avaliacao')
    esperadas += [{'par': p, 'fold': f, 'modelo': m}
                  for f in c['folds_desenvolvimento']+c['folds_avaliacao'] for p in c['pares'] for m in ('naive','arima')]
    esperadas = {identidade(x)[:20]: x for x in esperadas}
    encontradas, auditorias, tentativas = {}, {}, {}
    contagens, candidatos = Counter(), Counter()
    for p in sorted(pasta.glob('celulas/*/tentativa_*/tentativa.json')):
        t = ler_json(p)
        x = t['celula']
        chave = identidade(x)[:20]
        exigir(t['status'] == 'auditada', f'Tentativa não auditada: {p}')
        exigir(chave not in encontradas and p.parent.parent.name == chave, 'Duplicação ou identidade inválida.')
        a = ler_json(p.parent/'auditoria.json')
        exigir(a['status'] == 'aprovado' and a['celula'] == x, 'Auditoria incompatível.')
        verificar_arquivos(p.parent, a['arquivos'])
        encontradas[chave] = x
        relativo = p.parent.relative_to(pasta).as_posix()
        auditorias[relativo] = sha256(p.parent/'auditoria.json')
        tentativas[p.relative_to(pasta).as_posix()] = sha256(p)
        contagens[('desenvolvimento' if x['fold'] in c['folds_desenvolvimento'] else 'avaliacao')+'/'+x['modelo']] += 1
        if x['modelo'] == 'arima':
            itens = ler_json(p.parent/'candidatos.json')['candidatos']
            exigir(sorted(tuple(v['ordem']) for v in itens) == sorted(tuple(v) for v in c['arima']['ordens']), 'Grade ARIMA incompleta.')
            candidatos.update(v['status'] for v in itens)
        if len(encontradas) % 100 == 0:
            print(f'{len(encontradas)} tentativas e todos os artefatos vinculados conferidos.', flush=True)
    exigir(encontradas == esperadas and len(encontradas) == 832, 'Grade final incompleta.')
    for relativo, esperado in congelamento['auditorias_desenvolvimento'].items():
        exigir(auditorias.get(relativo) == esperado, 'Desenvolvimento alterado após congelamento.')
    publicacoes = {}
    for fase in ('desenvolvimento', 'avaliacao'):
        conclusao = ler_json(pasta/f'{fase}_concluido.json')
        exigir(conclusao['status'] == 'auditado' and conclusao['ajustes_neurais'] == 384 and conclusao['referencias'] == 32, 'Conclusão incompatível.')
        exigir(conclusao['utc'] < congelamento['utc'] if fase == 'desenvolvimento' else conclusao['utc'] > congelamento['utc'], 'Ordem temporal incompatível.')
        base = RAIZ/'registros/analises'/ponteiro['id']/fase
        a, p = ler_json(base/'auditoria_publicacao.json'), ler_json(base/'publicacao.json')
        exigir(a['status'] == 'aprovado' and a['execucao'] == ponteiro['id'] and a['publicacao_sha256'] == sha256(base/'publicacao.json'), 'Auditoria de publicação incompatível.')
        verificar_arquivos(base, p['arquivos'])
        resumo = ler_json(base/'resumo.json')
        exigir(len(resumo['ajustes']) == a['ajustes'] == 416 and a['candidatos_arima'] == 144 and a['cenarios_financeiros'] == 212, 'Inventário publicado incompatível.')
        for relativo, esperado in resumo['fontes'].items():
            exigir(sha256(RAIZ/relativo/'auditoria.json') == esperado, 'Fonte publicada alterada.')
        publicacoes[fase] = {'auditoria_sha256': sha256(base/'auditoria_publicacao.json'), 'manifesto_sha256': sha256(base/'publicacao.json'), 'ordens_conferidas': a['ordens_conferidas']}
    incidente = RAIZ/ler_json(RAIZ/'registros/continuacao_protocolo.json')['retomada_incidente']
    anterior = ler_json(incidente/'verificacao.json')
    verificar_arquivos(incidente, anterior['preservados'])
    for relativo, esperado in anterior['tentativas'].items():
        exigir(tentativas.get(relativo) == esperado, 'Tentativa anterior à retomada alterada.')
    for relativo, esperado in anterior['auditorias'].items():
        exigir(auditorias.get(relativo) == esperado, 'Auditoria anterior à retomada alterada.')
    exigir(sha256(pasta/'congelamento.json') == anterior['congelamento_sha256'], 'Congelamento alterado após incidente.')
    portal = ler_json(RAIZ/'dados/portal/resumo.json')
    exigir(portal['execucao'] == ponteiro['id'] and portal['dataset'] == dataset['id'], 'Portal incompatível.')
    exigir(portal['desenvolvimento_completo'] and portal['avaliacao_completa'] and len(portal['metricas']) == 832 and len(portal['series']) == 384, 'Portal incompleto.')
    for s in portal['series']:
        exigir(set(s['modelos']) == {'mamba','lstm','arima','naive'}, 'Série incompleta.')
        exigir(sha256(RAIZ/'dados/portal'/s['arquivo']) == s['sha256'], 'Série alterada.')
    for relativo, esperado in portal['fontes'].items():
        exigir(sha256(RAIZ/relativo/'auditoria.json') == esperado, 'Fonte do portal alterada.')
    print('Duas publicações, portal e continuidade do incidente conferidos.', flush=True)
    arquivo = RAIZ/'arquivo/estudo_barreiras_2026-10-20'
    manifesto = ler_json(arquivo/'manifesto_antes.json')
    for item in manifesto:
        destino = arquivo/'projeto'/item['caminho']
        exigir(destino.stat().st_size == item['bytes'] and sha256(destino) == item['sha256'], 'Arquivo histórico alterado.')
    exigir(len(manifesto) == 9790, 'Arquivo histórico incompleto.')
    recibo = {'status':'aprovado','utc':agora(),'execucao':ponteiro['id'],'dataset':dataset['id'],
              'fontes_cientificas':assinatura['fontes'],'congelamento_sha256':sha256(pasta/'congelamento.json'),
              'contagens':dict(contagens),'tentativas':len(tentativas),'candidatos_arima':dict(candidatos),
              'fontes_brutas':240,'arquivo_historico':len(manifesto),'publicacoes':publicacoes,
              'resumo_portal_sha256':sha256(RAIZ/'dados/portal/resumo.json'),
              'incidente_verificacao_sha256':sha256(incidente/'verificacao.json'),
              'tentativas_preservadas_incidente':len(anterior['tentativas']),
              'verificador_sha256':sha256(Path(__file__)),
              'limite':'Confere grade, hashes e vínculos dos recibos existentes. Não substitui os recálculos e recargas individuais nem a inspeção visual; não certifica exposição histórica universal.'}
    salvar_json(RAIZ/'registros/auditorias'/ponteiro['id']/'fechamento.json', recibo)
    print(f'Fechamento aprovado: {len(tentativas)} resultados; {sum(candidatos.values())} candidatos; {len(manifesto)} arquivos históricos.', flush=True)


if __name__ == '__main__':
    main()
