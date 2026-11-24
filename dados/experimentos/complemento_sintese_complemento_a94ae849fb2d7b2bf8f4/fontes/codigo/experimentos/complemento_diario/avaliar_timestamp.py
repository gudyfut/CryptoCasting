"""Avaliação da retirada do timestamp e intervenção completa nos ramos."""
from copy import deepcopy
import argparse
import io
import json
import zipfile
import numpy as np
from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256, conferir_arquivos
from experimentos.fechamento_ramos_diarios.avaliacao import medir, agregar, intervalo
from experimentos.fechamento_ramos_diarios.contratos import receita
from experimentos.generalizacao_moedas.avaliacao import carregar_mercado
from .comum import contexto, pais, carregar_npz, conferir_unidade, exclusividade, registrar_estado, fechar
from .avaliar_lstm import congelar_avaliacao
from .operacoes import executar_carteira, ler_carteira, agregar_pacotes
from .contratos import decisoes

ETAPA = 'ablacao_timestamp'
NOVOS = ('A_sem_timestamp', 'L_sem_timestamp')


def contrastes(matrizes, c):
    saida = {}
    for novo, original in zip(NOVOS, ('A', 'L')):
        for ref in (original, 'naive'):
            for forma in ('individuais', 'ensemble'):
                if forma == 'individuais':
                    a = np.array([matrizes[f'{novo}_{s}'] for s in c['seeds']])
                    b = np.array([matrizes[f'{ref}_{s}'] for s in c['seeds']]) if ref != 'naive' else matrizes['naive']
                else:
                    a = matrizes[novo+'_ensemble']
                    b = matrizes[ref+'_ensemble'] if ref != 'naive' else matrizes['naive']
                saida[f'{novo}_menos_{ref}_{forma}'] = {str(t): intervalo(a-b, t, c['bootstrap'], forma == 'individuais') for t in c['bootstrap']['blocos']}
    return saida


def inferencia():
    # Configuração anterior a qualquer chamada CUDA, igual à do treinamento.
    from treinamento.otimizacao import fixar_seed
    fixar_seed(42)
    import torch
    from mamba_ssm import Mamba
    from experimentos.ablacao_linear_diaria.treinamento import carregar_rede, inferir
    from experimentos.ablacao_linear_diaria.modelo import coeficientes_afins
    with exclusividade(ETAPA, gpu=True):
        ptr, p, f = contexto(ETAPA)
        t = ler_json(p / 'treinamentos_concluidos.json')
        assert t['cientificos'] == 24 and t['controles'] == 4
        assert not (p / 'previsoes_concluidas.json').exists()
        congelar_avaliacao(p)
        c, refs = f['configuracao'], pais()
        pub = p / 'publicacao'
        pub.mkdir(exist_ok=False)
        resultados, ramos = {}, {}
        for bloco in c['blocos']:
            b = bloco['id']
            dados = {fase: carregar_npz(p / b / 'dados' / (fase+'.npz')) for fase in ('treino', 'validacao', 'teste')}
            z = dados['teste']
            prev = {}
            for original in ('A', 'L'):
                for seed in (*c['seeds'], 'ensemble'):
                    nome = f'{original}_{seed}'
                    q = carregar_npz(refs['walkforward'] / 'publicacao' / b / 'previsoes' / (nome+'.npz'))
                    for campo, chave in [('origens_ms', 'origens_ms'), ('ultimo_close', 'ultimo_close'), ('alvo_retorno', 'y')]:
                        np.testing.assert_array_equal(q[campo], z[chave])
                    prev[nome] = q
                for seed in c['seeds']:
                    pasta = p / 'ajustes' / f'{b}_{original}_{seed}'
                    conferir_unidade(pasta)
                    rede = carregar_rede(pasta, receita(f['extras']['configs_blocos'][b], original))
                    val = inferir(rede, dados['validacao']['x'])
                    np.testing.assert_array_equal(val, carregar_npz(pasta / 'validacao.npz')['previsoes'])
                    teste = inferir(rede, z['x'])
                    np.testing.assert_array_equal(teste, inferir(rede, z['x']))
                    nome = f'{original}_sem_timestamp_{seed}'
                    prev[nome] = dict(previsoes_retorno=teste, previsoes=z['ultimo_close']*(1+teste),
                        alvo_retorno=z['y'], origens_ms=z['origens_ms'], ultimo_close=z['ultimo_close'])
                    if original == 'A':
                        pesos = {k: v.detach().clone() for k, v in rede.state_dict().items()}
                        cpu_rng, gpu_rng = torch.get_rng_state().clone(), torch.cuda.get_rng_state().clone()
                        coef, intercepto = coeficientes_afins(rede)
                        for fase, zz in dados.items():
                            completo = inferir(rede, zz['x'])
                            hooks = [m.register_forward_hook(lambda m, a, o: torch.zeros_like(o)) for m in rede.modules() if isinstance(m, Mamba)]
                            assert len(hooks) == 12
                            try:
                                sem = inferir(rede, zz['x'])
                            finally:
                                for h in hooks:
                                    h.remove()
                            afim = np.einsum('nct,ct->n', zz['x'].astype(float), coef)+intercepto
                            np.testing.assert_allclose(sem, afim, atol=2e-6, rtol=1e-5)
                            np.testing.assert_array_equal(completo, inferir(rede, zz['x']))
                            d = completo-sem
                            caminho = pub / b / 'ramos' / f'{fase}_{seed}.npz'
                            caminho.parent.mkdir(parents=True, exist_ok=True)
                            np.savez_compressed(caminho, origens_ms=zz['origens_ms'], alvo_retorno=zz['y'], completo=completo, sem_ramos=sem, afim=afim)
                            ramos[f'{b}/{seed}/{fase}'] = dict(n=len(completo), max_abs=float(abs(d).max()),
                                rms=float(np.sqrt(np.mean(d*d))), mse_completo=float(np.mean((completo-zz['y'])**2)),
                                mse_sem_ramos=float(np.mean((sem-zz['y'])**2)),
                                fracao_decisoes_alteradas=float(np.mean(decisoes(zz['ultimo_close']*(1+completo), zz['ultimo_close'], .002) != decisoes(zz['ultimo_close']*(1+sem), zz['ultimo_close'], .002))),
                                arquivo=caminho.relative_to(p).as_posix())
                        assert all(torch.equal(v, rede.state_dict()[k]) for k, v in pesos.items())
                        assert torch.equal(cpu_rng, torch.get_rng_state()) and torch.equal(gpu_rng, torch.cuda.get_rng_state())
                    del rede
                    torch.cuda.empty_cache()
                nome = original+'_sem_timestamp_ensemble'
                preco = np.mean([prev[f'{original}_sem_timestamp_{s}']['previsoes'] for s in c['seeds']], axis=0)
                prev[nome] = dict(previsoes=preco, previsoes_retorno=preco/z['ultimo_close']-1,
                    alvo_retorno=z['y'], origens_ms=z['origens_ms'], ultimo_close=z['ultimo_close'])
            prev['naive'] = dict(previsoes_retorno=np.zeros(len(z['y'])), previsoes=z['ultimo_close'],
                alvo_retorno=z['y'], origens_ms=z['origens_ms'], ultimo_close=z['ultimo_close'])
            metricas = {k: medir(q['alvo_retorno'], q['previsoes_retorno']) for k, q in prev.items()}
            perdas = {k: (q['previsoes_retorno']-q['alvo_retorno'])**2 for k, q in prev.items()}
            resultados[b] = dict(populacao=len(z['y']), metricas=metricas,
                medias={v: agregar([metricas[f'{v}_{s}'] for s in c['seeds']]) for v in ('A', 'L', *NOVOS)},
                contrastes_mse=contrastes(perdas, c))
            pasta = pub / b / 'previsoes'
            pasta.mkdir(parents=True)
            for nome, q in prev.items():
                np.savez_compressed(pasta / (nome+'.npz'), **q)
            registrar_estado(ETAPA, 'inferindo', bloco=b, modelos_novos=6, diagnosticos_ramos=len(ramos))
        salvar_json(pub / 'previsao.json', resultados)
        salvar_json(pub / 'ramos.json', dict(populacoes=ramos, checkpoints_A=12, pesos_e_rng_preservados=True,
            limite='Intervenção na inferência do checkpoint selecionado; não elimina influência dos ramos durante o aprendizado.'))
        congelar_avaliacao(p)
        salvar_json(p / 'previsoes_concluidas.json', dict(utc=agora(), recargas_exatas=24, diagnosticos_populacoes=36,
            arquivos={q.relative_to(p).as_posix(): sha256(q) for q in pub.rglob('*') if q.is_file()}))
        registrar_estado(ETAPA, 'previsoes_concluidas')


def operacoes():
    with exclusividade(ETAPA):
        ptr, p, f = contexto(ETAPA)
        assert not (p / 'operacoes_concluidas.json').exists()
        conferir_arquivos(p, ler_json(p / 'previsoes_concluidas.json')['arquivos'])
        congelar_avaliacao(p)
        c, refs = f['configuracao'], pais()
        wf = ler_json(refs['walkforward'] / 'congelamento.json')
        mercado = carregar_mercado(wf['referencias']['mercado'])
        antigas = ler_json(refs['walkforward'] / 'publicacao/operacoes.json')['carteiras']
        carteiras, falhas, pacotes, medias, ic = [], [], [], {}, {}
        for bloco in c['blocos']:
            b = bloco['id']
            for custo, slip in enumerate(c['slippage_cenarios'], 1):
                regras = dict(wf['configs_blocos'][b]['operacoes'], slippage_por_lado=slip)
                logs = {}
                for novo in NOVOS:
                    individuais = []
                    for seed in (*c['seeds'], 'ensemble'):
                        nome = f'{novo}_{seed}'
                        ident = f'{b}/{nome}/custo_{custo}'
                        z = carregar_npz(p / 'publicacao' / b / 'previsoes' / (nome+'.npz'))
                        destino = p / 'carteiras' / ident
                        recibo = executar_carteira(destino, z, mercado, regras, identidade=ident)
                        pacotes.append((ident, destino))
                        linha = dict(bloco=b, unidade=nome, custo=custo, membro=ident, metricas=recibo['metricas'])
                        if recibo['situacao'] == 'falha_prudencial':
                            falhas.append(linha)
                        else:
                            carteiras.append(linha)
                            logs[nome] = np.diff(np.log(ler_carteira(destino)[1]['saldos_diarios']))
                            if seed != 'ensemble':
                                individuais.append(recibo['metricas'])
                        registrar_estado(ETAPA, 'simulando', concluidas=len(carteiras)+len(falhas), previstas=96)
                    medias[f'{b}/{novo}/custo_{custo}'] = agregar(individuais) if len(individuais) == 3 else dict(incompleto=True)
                if len(logs) == 8:
                    with zipfile.ZipFile(refs['walkforward'] / 'publicacao/carteiras.zip') as arq:
                        for x in antigas:
                            if x['bloco'] == b and x['custo'] == custo and x['unidade'].split('_')[0] in ('A', 'L'):
                                with np.load(io.BytesIO(arq.read(x['membro']+'/curva.npz'))) as q:
                                    logs[x['unidade']] = np.diff(np.log(q['saldos_diarios']))
                    logs['naive'] = np.zeros(bloco['n_teste'])
                    ic[f'{b}/custo_{custo}'] = contrastes(logs, c)
                else:
                    ic[f'{b}/custo_{custo}'] = dict(incompleto=True, motivo='Falhas preservadas.')
        assert len(carteiras)+len(falhas) == 96
        agregar_pacotes(p / 'publicacao/carteiras.zip', pacotes)
        salvar_json(p / 'publicacao/operacoes.json', dict(carteiras=carteiras, falhas=falhas,
            medias_seeds=medias, contrastes_crescimento_log_diario=ic))
        congelar_avaliacao(p)
        salvar_json(p / 'operacoes_concluidas.json', dict(utc=agora(), carteiras=len(carteiras), falhas=len(falhas)))
        fechar(ETAPA, dict(ajustes_cientificos=24, controles=4, carteiras=len(carteiras), falhas=len(falhas), diagnosticos_ramos=36))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('acao', choices=['inferencia', 'operacoes'])
    globals()[parser.parse_args().acao]()
