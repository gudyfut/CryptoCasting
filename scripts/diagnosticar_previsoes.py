"""Diagnóstico retrospectivo: não treina, não seleciona modelos e não altera o ciclo."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import platform
import sys

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from barreiras.particoes import separar
from barreiras.configuracao import FOLDS

CICLO = '4e232a796fcda0ea34c3'
BASE = RAIZ / f'dados/experimentos/barreiras_{CICLO}'
DADOS = RAIZ / 'dados/processados/barreiras_9341610dbb329a858784'
DESTINO = RAIZ / 'historico/analises/diagnostico_2026-10-19'

def ler(p):
    return json.loads(p.read_text(encoding='utf-8'))

def hash_arquivo(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def diagnosticar():
    DESTINO.mkdir(parents=True, exist_ok=True)
    inicio = datetime.now(timezone.utc).isoformat()
    resumo = ler(RAIZ / 'historico/analises/ciclo_001_completo/resumo.json')
    assert hash_arquivo(RAIZ / 'historico/analises/ciclo_001_completo/resumo.json') == '350a6b080ded621a8bf0f53f76a0a97f5168a6e580f361912f5dd88847f1e0c5'
    for p, h in resumo['fontes'].items():
        assert hash_arquivo(RAIZ / p) == h, p
    meta = ler(DADOS / 'dataset.json')
    comuns = np.load(DADOS / 'origens_comuns.npy')
    horas, amostras = {}, {}
    for par in ('BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT'):
        horas[par] = pd.read_parquet(DADOS / par / 'horas.parquet')
        for nome in ('horas.parquet', 'amostras_H1.parquet', 'amostras_H24.parquet', 'amostras_H168.parquet'):
            assert hash_arquivo(DADOS / par / nome) == meta['arquivos'][f'{par}/{nome}']
        for h in (1, 24, 168):
            amostras[par, h] = pd.read_parquet(DADOS / par / f'amostras_H{h}.parquet')
    linhas, ajustes, casos = [], [], []
    vistos = set()
    for registro in sorted((RAIZ / 'historico/execucoes').glob('*.json')):
        r = ler(registro)
        if r.get('id_ciclo') != CICLO:
            continue
        c = r['celula']; par, h, fold = c['par'], c['horizonte'], c['fold']
        pasta = BASE / r['id']
        integridade = ler(pasta / 'integridade.json')
        blocos = separar(amostras[par, h], comuns, fold)
        limites = FOLDS[fold].limites()
        assert blocos['treino'].expiracao_maxima_utc.max() < limites[1]
        assert blocos['validacao'].expiracao_maxima_utc.max() < limites[2]
        assert blocos['teste'].expiracao_maxima_utc.max() < limites[3]
        for modelo in ('lstm', 'mamba', 'ar1'):
            for nome in ('previsoes_teste.parquet', 'resultado_modelo.json'):
                assert hash_arquivo(pasta / modelo / nome) == integridade[f'{modelo}/{nome}']
            q = pd.read_parquet(pasta / modelo / 'previsoes_teste.parquet').set_index('origem_utc').sort_index()
            verdadeiro = blocos['teste'].set_index('origem_utc').sort_index()
            assert q.index.is_unique and q.index.equals(verdadeiro.index)
            assert np.array_equal(q.classe, verdadeiro.classe)
            p, y = q[['p0', 'p1', 'p2']].to_numpy(float), q.classe.to_numpy(int)
            assert np.isfinite(p).all() and np.all(p > 0) and np.all(p <= 1)
            assert np.allclose(p.sum(1), 1, atol=1e-6)
            matriz = np.zeros((3, 3), int)
            np.add.at(matriz, (y, p.argmax(1)), 1)
            erro = -np.log(np.maximum(p[np.arange(len(y)), y], 1e-7))
            m = ler(pasta / modelo / 'resultado_modelo.json')
            assert np.array_equal(matriz, m['metricas']['teste']['matriz_confusao'])
            assert abs(erro.mean() - m['metricas']['teste']['log_loss']) < 1e-10
            epoca = None
            if modelo != 'ar1':
                historico = ler(pasta / modelo / 'epocas.json')
                assert hash_arquivo(pasta / modelo / 'epocas.json') == integridade[f'{modelo}/epocas.json']
                epoca = min(historico, key=lambda e: e['validacao_log_loss'])['epoca']
                assert epoca == m['epoca_selecionada']
            linha = dict(id=r['id'], **c, modelo=modelo, n=len(y), log_loss=float(erro.mean()), epoca=epoca,
                         acuracia=float((y == p.argmax(1)).mean()), balanced_accuracy=float((matriz.diagonal()/matriz.sum(1)).mean()),
                         fracao_soma_fora_1e6=float((np.abs(p.sum(1)-1)>1e-6).mean()))
            # Sensibilidade descritiva de população; ausentes continuam contados.
            # Não transforma origens com futuro conhecido em regra de entrada.
            caminho_operacional = pasta / modelo / 'previsoes_operacional.parquet'
            assert hash_arquivo(caminho_operacional) == integridade[f'{modelo}/previsoes_operacional.parquet']
            operacional = pd.read_parquet(caminho_operacional)
            observavel = operacional.loc[operacional.classe >= 0]
            po = observavel[['p0','p1','p2']].to_numpy(float)
            yo = observavel.classe.to_numpy(int)
            linha.update(n_operacional=len(operacional), n_operacional_nao_observado=int((operacional.classe < 0).sum()),
                         log_loss_operacional_observavel=float(-np.log(np.maximum(po[np.arange(len(yo)),yo],1e-7)).mean()))
            for k in range(3):
                linha.update({f'reais_{k}':int((y == k).sum()), f'escolhidos_{k}':int((p.argmax(1) == k).sum()),
                              f'prob_media_{k}':float(p[:, k].mean()), f'prob_min_{k}':float(p[:, k].min()),
                              f'prob_max_{k}':float(p[:, k].max()), f'prob_std_{k}':float(p[:, k].std()),
                              f'recall_{k}':float(matriz[k, k]/matriz[k].sum()),
                              f'log_loss_condicional_{k}':float(erro[y == k].mean()),
                              f'treino_freq_{k}':float((blocos['treino'].classe == k).mean()),
                              f'validacao_freq_{k}':float((blocos['validacao'].classe == k).mean())})
            linhas.append(linha)
            if modelo != 'ar1' and (matriz.sum(0) == 0).any():
                i = int(np.argmax(p[:, 2]))
                casos.append({'id':r['id'], **c, 'modelo':modelo, 'origem':q.index[i].isoformat(),
                              'probabilidades':p[i].tolist(), 'classe_real':int(y[i]),
                              'classes_nunca_escolhidas':np.flatnonzero(matriz.sum(0) == 0).tolist()})
        if (par, fold) not in vistos:
            vistos.add((par, fold))
            ajuste = ler(pasta / 'ar1/ajuste.json')
            assert hash_arquivo(pasta / 'ar1/ajuste.json') == integridade['ar1/ajuste.json']
            t = pd.Timestamp(ajuste['ultima_origem_ajuste'])
            assert t == blocos['treino'].origem_utc.max()
            serie = horas[par].loc[horas[par].origem_utc <= t, 'retorno'].to_numpy(float)
            x, y = serie[:-1], serie[1:]; validos = np.isfinite(x) & np.isfinite(y)
            x, y = x[validos], y[validos]
            # Fórmulas escalares independentes do lstsq usado no ciclo.
            phi = float(((x-x.mean())*(y-y.mean())).sum()/((x-x.mean())**2).sum())
            intercepto = float(y.mean()-phi*x.mean())
            residuos = y-intercepto-phi*x
            sigma = float(np.sqrt(np.square(residuos).sum()/(len(x)-2)))
            assert np.allclose([intercepto, phi, sigma], [ajuste['intercepto'], ajuste['phi'], ajuste['sigma_residual']], atol=1e-12)
            q = blocos['teste']; razao = sigma/q.sigma.to_numpy()
            ajustes.append({'par':par, 'fold':fold, **ajuste,
                'sigma_local_mediana':float(q.sigma.median()), 'razao_mediana':float(np.median(razao)),
                'razao_q10':float(np.quantile(razao,.1)), 'razao_q90':float(np.quantile(razao,.9)),
                'fracao_sigma_simulada_maior_local':float((razao>1).mean()),
                'curtose_excesso_residuos':float(np.mean((residuos-residuos.mean())**4)/np.var(residuos)**2-3),
                'correlacao_quadrados_lag1':float(np.corrcoef(residuos[:-1]**2,residuos[1:]**2)[0,1])})
    tabela = pd.DataFrame(linhas)
    assert len(tabela) == 288 and len(ajustes) == 16
    tabela.to_csv(DESTINO / 'diagnostico_por_celula.csv',index=False)
    pd.DataFrame(ajustes).to_csv(DESTINO / 'volatilidade_ar1.csv',index=False)
    agregados = []
    for (modelo,h), grupo in tabela.groupby(['modelo','horizonte']):
        agregado = {'modelo':modelo,'horizonte':int(h),'celulas':len(grupo),'log_loss':float(grupo.log_loss.mean()),
                    'log_loss_operacional_observavel':float(grupo.log_loss_operacional_observavel.mean()),
                    'celulas_so_uma_classe':int(((grupo[[f'escolhidos_{k}' for k in range(3)]]>0).sum(axis=1)==1).sum())}
        for k in range(3):
            agregado.update({f'celulas_sem_escolher_{k}':int((grupo[f'escolhidos_{k}']==0).sum()),
                f'freq_real_{k}':float((grupo[f'reais_{k}']/grupo.n).mean()),
                f'prob_media_{k}':float(grupo[f'prob_media_{k}'].mean()),
                f'freq_treino_{k}':float(grupo[f'treino_freq_{k}'].mean()),
                f'freq_validacao_{k}':float(grupo[f'validacao_freq_{k}'].mean()),
                f'log_loss_condicional_{k}':float(grupo[f'log_loss_condicional_{k}'].mean())})
        agregados.append(agregado)
    saida={'tipo':'diagnostico_retrospectivo_sem_novo_treino','inicio_utc':inicio,'fim_utc':datetime.now(timezone.utc).isoformat(),
        'ciclo':CICLO,'script_sha256':hash_arquivo(Path(__file__)),
        'versoes':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__},
        'fontes_cientificas_verificadas':len(resumo['fontes']),'series_verificadas':len(linhas),
        'ajustes_ar1_recalculados':16,'selecao_epocas_conferida':192,'probabilidades_zero':0,
        'agregados_pesos_iguais_por_celula':agregados,'exemplos_classes_omitidas':casos,
        'arquivos':{p.name:hash_arquivo(p) for p in DESTINO.glob('*.csv')},
        'limites':['Desenvolvimento 2023; nenhuma leitura de B1-B4','Contagens de celulas nao sao replicas independentes',
                   'Verifica artefatos e contratos; nao demonstra ausencia de todo vies','Nao escolhe novas politicas ou checkpoints']}
    (DESTINO/'resumo.json').write_text(json.dumps(saida,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(tabela.groupby(['modelo','horizonte'])[['log_loss','acuracia','balanced_accuracy']].mean().to_string())
    print(pd.DataFrame(ajustes)[['par','fold','phi','sigma_residual','sigma_local_mediana','razao_mediana']].to_string(index=False))
    for a in agregados:
        print(a['modelo'],a['horizonte'],'sem escolher classes:',[a[f'celulas_sem_escolher_{k}'] for k in range(3)],'so uma:',a['celulas_so_uma_classe'])

if __name__ == '__main__':
    diagnosticar()
