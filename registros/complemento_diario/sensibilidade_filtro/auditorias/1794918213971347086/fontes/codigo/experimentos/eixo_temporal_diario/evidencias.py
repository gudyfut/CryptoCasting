"""Verificação das fontes e prova de seleção limitada ao prefixo200."""
import json
from pathlib import Path
import numpy as np
from infraestrutura.artefatos import RAIZ, ler_json, sha256, conferir_arquivos
from .contratos import conferir_configuracao, selecionar_prefixo

NOMES = {'A':'padronizacao_diaria', 'B':'sem_penalizacao_diaria'}


def historia(pasta):
    return [json.loads(l) for l in (pasta/'epocas.jsonl').read_text().splitlines()]


def inspecionar(c):
    referencias = {}; preservacao = {}
    indice = ler_json(RAIZ/c['referencia_indice'])
    preservacao[c['referencia_indice']] = sha256(RAIZ/c['referencia_indice'])
    for variante, nome in NOMES.items():
        ponteiro = ler_json(RAIZ/f'registros/{nome}/execucao.json')
        assert ponteiro['id'] == c['referencias'][variante]
        pasta = RAIZ/ponteiro['pasta']
        assert sha256(pasta/'congelamento.json') == ponteiro['congelamento_sha256']
        congelamento = ler_json(pasta/'congelamento.json')
        assert ler_json(pasta/'processo.json')['ativo'] is False
        assert ler_json(pasta/'controle.json')['aprovado']
        fecho = ler_json(RAIZ/f'registros/{nome}/fechamento.json')
        assert sha256(RAIZ/fecho['arquivo']) == fecho['sha256']
        conferir_arquivos(pasta, ler_json(pasta/'fechamento.json')['arquivos'])
        conferir_arquivos(pasta/'fontes', congelamento['fontes'])
        conferir_configuracao(c, congelamento['configuracao'])
        assert congelamento['configuracao']['treinamento']['weight_decay'] == c['variantes'][variante]['weight_decay']
        for arquivo in pasta.rglob('*'):
            if arquivo.is_file(): preservacao[arquivo.relative_to(RAIZ).as_posix()] = sha256(arquivo)
        provas = {}
        for seed in c['seeds']:
            ajuste = pasta/'ajustes'/f'seed_{seed}'
            historico = historia(ajuste)
            assert len(historico) == 1000
            escolhido = selecionar_prefixo(historico)
            selecao = ler_json(ajuste/'selecao.json')
            assert escolhido['epoca'] == selecao['epoca']
            assert escolhido['rmse_global_validacao_retorno'] == selecao['rmse_validacao']
            assert sha256(ajuste/selecao['checkpoint']) == selecao['sha256']
            inicio = ler_json(ajuste/'inicio.json')
            assert inicio['configuracao'] == congelamento['configuracao']['treinamento']
            assert inicio['seed'] == seed
            if variante == 'A':
                modelo = next(q for q in indice['modelos'] if q['simbolo']=='BTCUSDT' and q['seed']==seed)
                assert modelo['checkpoint_sha256'] == selecao['sha256']
                assert RAIZ/modelo['checkpoint'] == ajuste/selecao['checkpoint']
            provas[str(seed)] = {'pasta':ajuste.relative_to(RAIZ).as_posix(), 'epoca':escolhido['epoca'],
                                'rmse_validacao':selecao['rmse_validacao'], 'checkpoint':selecao,
                                'historico_sha256':sha256(ajuste/'epocas.jsonl'),
                                'primeiras200_epocas_completas':True, 'minimo_prefixo_igual_selecao':True}
        a = historia(pasta/'ajustes/seed_42')[:200]
        b = historia(pasta/'ajustes/controle_42')[:200]
        assert [{k:v for k,v in r.items() if k!='segundos'} for r in a] == [
                {k:v for k,v in r.items() if k!='segundos'} for r in b]
        np.testing.assert_array_equal(np.load(pasta/'ajustes/seed_42/validacao.npz')['previsoes'],
                                      np.load(pasta/'ajustes/controle_42/validacao.npz')['previsoes'])
        referencias[variante] = {'ponteiro':ponteiro, 'configuracao':congelamento['configuracao'],
            'escalas':congelamento['escalas'], 'diario':congelamento['diario'],
            'mercado_minuto':congelamento['mercado_minuto'], 'provas':provas,
            'controle_prefixo200_exato':True}
    assert referencias['A']['diario'] == referencias['B']['diario']
    assert referencias['A']['mercado_minuto'] == referencias['B']['mercado_minuto']
    assert referencias['A']['escalas'] == referencias['B']['escalas']
    for chave in ('diario','mercado_minuto'):
        ref = referencias['A'][chave]; pasta = RAIZ/ref['pasta']
        assert sha256(pasta/'manifesto.json') == ref['manifesto_sha256']
        conferir_arquivos(pasta, ler_json(pasta/'manifesto.json')['arquivos'])
    continuidade = ler_json(RAIZ/'registros/continuidade_moedas/execucao.json')
    assert continuidade['id'] == '945f0e52b1f85184c3e7'
    pasta = RAIZ/continuidade['pasta']
    assert sha256(pasta/'congelamento.json') == continuidade['congelamento_sha256']
    for nome in ('congelamento.json','resultados.json','carteiras.zip','manifesto.json'):
        preservacao[(pasta/nome).relative_to(RAIZ).as_posix()] = sha256(pasta/nome)
    conferir_arquivos(pasta, ler_json(pasta/'manifesto.json')['arquivos'])
    for nome in ('configuracoes/custos_vigentes_001.json','registros/continuidade_moedas/execucao.json',
                 'registros/eixo_temporal_diario/autorizacao.json'):
        preservacao[nome] = sha256(RAIZ/nome)
    return {'referencias':referencias,'preservacao':preservacao,'continuidade':continuidade,
            'heranca_aprovada':['A','B'], 'novos_ajustes_principais':6, 'novos_controles':2,
            'limite':'Equivalência de seleção no prefixo200; não são novos treinos, nem confirmação independente.'}


def conferir_pesos_controle(referencia):
    import torch
    pasta = RAIZ/referencia['ponteiro']['pasta']/'ajustes'
    arquivos = [q for q in (pasta/'seed_42/checkpoints').glob('*.pt') if int(q.stem.split('_')[1])<=200]
    controles = [q.name for q in (pasta/'controle_42/checkpoints').glob('*.pt') if int(q.stem.split('_')[1])<=200]
    assert sorted(q.name for q in arquivos) == sorted(controles)
    for arquivo in arquivos:
        a = torch.load(arquivo, map_location='cpu', weights_only=True)['pesos']
        b = torch.load(pasta/'controle_42/checkpoints'/arquivo.name, map_location='cpu', weights_only=True)['pesos']
        assert a.keys() == b.keys() and all(torch.equal(a[k],b[k]) for k in a)
    return len(arquivos)


if __name__ == '__main__':
    import argparse
    from infraestrutura.artefatos import salvar_json
    parser=argparse.ArgumentParser();parser.add_argument('destino');args=parser.parse_args()
    destino=Path(args.destino)
    assert not destino.exists()
    salvar_json(destino,inspecionar(ler_json(RAIZ/'configuracoes/eixo_temporal_diario_001.json')))
    print('HERANCA_E_DADOS_CONFERIDOS',flush=True)
