"""Auditoria posterior da ablação cronológica e da intervenção nos ramos."""
import io
import shutil
import time
import zipfile
import numpy as np
from infraestrutura.artefatos import RAIZ, agora, conferir_arquivos, ler_json, salvar_json, sha256
from experimentos.generalizacao_moedas.avaliacao import carregar_mercado
from .comum import contexto, pais, carregar_npz, fontes, exclusividade, registrar_estado
from .inventario import REG, relativo
from .auditar import selecionar, metricas, medias, contrastes, contabilidade, perto
from .treinar import conferir_ajustes
from .operacoes import ler_carteira

ETAPA = 'ablacao_timestamp'
NOVOS = ('A_sem_timestamp', 'L_sem_timestamp')


def executar():
    with exclusividade(ETAPA):
        ptr, p, f = contexto(ETAPA)
        destino = REG / ETAPA / 'auditorias' / str(time.time_ns())
        destino.mkdir(parents=True)
        codigos = fontes()
        for nome in codigos:
            q = destino / 'fontes' / nome
            q.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(RAIZ / nome, q)
        salvar_json(destino / 'inicio.json', dict(utc=agora(), fontes=codigos, execucao=ptr))
        fecho = ler_json(REG / ETAPA / 'fechamento.json')
        assert sha256(RAIZ / fecho['arquivo']) == fecho['sha256']
        conferir_arquivos(p, ler_json(p / 'fechamento.json')['arquivos'])
        conferir_arquivos(RAIZ, ler_json(p / 'dados_preparados.json'))
        refs, c = pais(), f['configuracao']
        selecoes = {a.name: selecionar(a) for a in (p / 'ajustes').iterdir()}
        esperados = {f"{b['id']}_{v}_{s}" for b in c['blocos'] for v in ('A', 'L') for s in c['seeds']}
        esperados |= {f'controle_{tipo}_{v}_42' for tipo in ('original', 'zero') for v in ('A', 'L')}
        assert set(selecoes) == esperados
        for v in ('A', 'L'):
            conferir_ajustes(p / 'ajustes' / f'controle_original_{v}_42', refs['walkforward'] / 'B1/ajustes' / f'{v}_42')
            conferir_ajustes(p / 'ajustes' / f'controle_zero_{v}_42', p / 'ajustes' / f'B1_{v}_42')
        previsto = ler_json(p / 'publicacao/previsao.json')
        ramos = ler_json(p / 'publicacao/ramos.json')
        assert len(ramos['populacoes']) == 36 and ramos['pesos_e_rng_preservados']
        ic = 0
        for bloco in c['blocos']:
            b = bloco['id']
            for fase in ('treino', 'validacao', 'teste'):
                z = carregar_npz(p / b / 'dados' / (fase+'.npz'))
                original = carregar_npz(refs['walkforward'] / b / 'dados' / (fase+'.npz'))
                assert np.all(z['x'][:, 0, :] == 0)
                for k in z:
                    np.testing.assert_array_equal(z[k][:, 1:, :] if k == 'x' else z[k], original[k][:, 1:, :] if k == 'x' else original[k])
                for seed in c['seeds']:
                    info = ramos['populacoes'][f'{b}/{seed}/{fase}']
                    q = carregar_npz(p / info['arquivo'])
                    np.testing.assert_array_equal(q['origens_ms'], z['origens_ms'])
                    np.testing.assert_array_equal(q['alvo_retorno'], z['y'])
                    delta = q['completo']-q['sem_ramos']
                    perto(info['max_abs'], max(abs(delta)))
                    perto(info['rms'], np.linalg.norm(delta)/np.sqrt(len(delta)))
                    for qual in ('completo', 'sem_ramos'):
                        e = q[qual]-q['alvo_retorno']
                        perto(info['mse_'+qual], np.dot(e, e)/len(e))
                    np.testing.assert_allclose(q['sem_ramos'], q['afim'], atol=2e-6, rtol=1e-5)
                    # Reconstituir a decisão pelo preço codificado, inclusive
                    # arredondamento de float no limite do filtro.
                    lados = []
                    for qual in ('completo', 'sem_ramos'):
                        preco = z['ultimo_close']*(1+q[qual])
                        ret = preco/z['ultimo_close']-1
                        lados.append(np.where((preco > 0) & (abs(ret) > .002), np.sign(ret), 0))
                    perto(info['fracao_decisoes_alteradas'], np.mean(lados[0] != lados[1]))
            prev = {q.stem: carregar_npz(q) for q in (p / 'publicacao' / b / 'previsoes').glob('*.npz')}
            assert len(prev) == 17
            teste = carregar_npz(p / b / 'dados/teste.npz')
            for nome, q in prev.items():
                for k, alvo in [('origens_ms', 'origens_ms'), ('ultimo_close', 'ultimo_close'), ('alvo_retorno', 'y')]:
                    np.testing.assert_array_equal(q[k], teste[alvo])
                metricas(q, previsto[b]['metricas'][nome])
            for v in ('A', 'L', *NOVOS):
                np.testing.assert_array_equal(prev[v+'_ensemble']['previsoes'], np.mean([prev[f'{v}_{s}']['previsoes'] for s in c['seeds']], axis=0))
                medias([previsto[b]['metricas'][f'{v}_{s}'] for s in c['seeds']], previsto[b]['medias'][v])
            perdas = {k: (q['previsoes_retorno']-q['alvo_retorno'])**2 for k, q in prev.items()}
            for novo, original in zip(NOVOS, ('A', 'L')):
                ic += contrastes(perdas, previsto[b]['contrastes_mse'], c, novo, (original, 'naive'))
        wf = ler_json(refs['walkforward'] / 'congelamento.json')
        mercado = carregar_mercado(wf['referencias']['mercado'])
        ops = ler_json(p / 'publicacao/operacoes.json')
        assert len(ops['carteiras'])+len(ops['falhas']) == 96
        auditorias = []
        for linha in ops['carteiras']+ops['falhas']:
            z = carregar_npz(p / 'publicacao' / linha['bloco'] / 'previsoes' / (linha['unidade']+'.npz'))
            regras = dict(wf['configs_blocos'][linha['bloco']]['operacoes'], slippage_por_lado=c['slippage_cenarios'][linha['custo']-1])
            auditorias.append(contabilidade(p / 'carteiras' / linha['membro'], z, mercado, regras))
        antigas = ler_json(refs['walkforward'] / 'publicacao/operacoes.json')['carteiras']
        for bloco in c['blocos']:
            b = bloco['id']
            for custo in (1, 2, 3):
                locais = [x for x in ops['carteiras'] if x['bloco'] == b and x['custo'] == custo]
                if len(locais) != 8:
                    assert ops['contrastes_crescimento_log_diario'][f'{b}/custo_{custo}']['incompleto']
                    continue
                logs = {x['unidade']: np.diff(np.log(ler_carteira(p / 'carteiras' / x['membro'])[1]['saldos_diarios'])) for x in locais}
                with zipfile.ZipFile(refs['walkforward'] / 'publicacao/carteiras.zip') as arq:
                    for x in antigas:
                        if x['bloco'] == b and x['custo'] == custo and x['unidade'].split('_')[0] in ('A', 'L'):
                            with np.load(io.BytesIO(arq.read(x['membro']+'/curva.npz'))) as q:
                                logs[x['unidade']] = np.diff(np.log(q['saldos_diarios']))
                logs['naive'] = np.zeros(bloco['n_teste'])
                for novo, original in zip(NOVOS, ('A', 'L')):
                    ic += contrastes(logs, ops['contrastes_crescimento_log_diario'][f'{b}/custo_{custo}'], c, novo, (original, 'naive'))
                    medias([x['metricas'] for x in locais if x['unidade'].startswith(novo) and not x['unidade'].endswith('ensemble')], ops['medias_seeds'][f'{b}/{novo}/custo_{custo}'])
        assert ic == 384 or ops['falhas']
        conferir_arquivos(RAIZ, codigos)
        resultado = dict(utc=agora(), situacao='aprovada', selecoes=selecoes,
            ajustes_cientificos=24, controles_exatos=4, intervalos_recalculados=ic,
            carteiras=len(auditorias), diagnosticos_ramos=36, contabilidade=auditorias)
        salvar_json(destino / 'resultado.json', resultado)
        salvar_json(REG / ETAPA / 'conferencia_posterior.json', dict(utc=agora(), situacao='aprovada',
            arquivo=relativo(destino / 'resultado.json'), sha256=sha256(destino / 'resultado.json'),
            inicio=relativo(destino / 'inicio.json'), fechamento=fecho))
        registrar_estado(ETAPA, 'auditado', ajustes=24, controles=4, carteiras=96, intervalos=ic)


if __name__ == '__main__':
    executar()
