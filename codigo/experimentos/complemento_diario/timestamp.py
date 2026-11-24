"""Etapa condicional delimitada: zero no canal cronológico após padronizar."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import argparse
import json
import shutil
import time
import numpy as np
from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256, conferir_arquivos
from experimentos.fechamento_ramos_diarios.contratos import receita
from .inventario import REG, relativo
from .comum import (contexto, congelar, configuracao, pais, carregar_npz, fontes,
                    exclusividade, registrar_estado, selar_unidade, conferir_unidade)
from .contratos import retirar_timestamp
from .treinar import conferir_ajustes, verificar_ambiente

ETAPA = 'ablacao_timestamp'


def decidir():
    assert not (REG / ETAPA / 'decisao.json').exists()
    audits = {}
    for etapa in ('lstm_walkforward', 'sensibilidade_filtro', 'deslocamento_exposicao', 'referencias_exposicao'):
        arquivo = REG / etapa / 'conferencia_posterior.json'
        q = ler_json(arquivo)
        assert q['situacao'] == 'aprovada'
        assert sha256(RAIZ / q['arquivo']) == q['sha256']
        audits[relativo(arquivo)] = sha256(arquivo)
    refs = pais()
    c = configuracao()
    tempos = {}
    for b in c['blocos']:
        for v in ('A', 'L'):
            for seed in c['seeds']:
                q = ler_json(refs['walkforward'] / b['id'] / 'ajustes' / f'{v}_{seed}' / 'conclusao.json')
                tempos[f"{b['id']}/{v}_{seed}"] = q['segundos']
    extras = sum(tempos[f'B1/{v}_42']*2 for v in ('A', 'L'))
    # Reserva técnica explícita: dobrar todo tempo medido e somar seis horas
    # para qualificação, operações, diagnóstico completo e auditoria.
    estimativa = 2*(sum(tempos.values())+extras)+6*3600
    inicio = datetime.fromisoformat(ler_json(REG / 'inicio.json')['utc'])
    limite = inicio+timedelta(days=5)
    agora_dt = datetime.now(timezone.utc)
    executar = agora_dt+timedelta(seconds=estimativa) <= limite
    decisao = dict(utc=agora(), executar=executar, nucleo_auditado=audits,
        tempos_herdados_segundos=tempos, estimativa_conservadora_segundos=estimativa,
        limite_utc=limite.isoformat(), conclusao_estimada_utc=(agora_dt+timedelta(seconds=estimativa)).isoformat(),
        regra='2 × tempos dos 24 ajustes originais + quatro controles equivalentes, mais seis horas de avaliação/auditoria.',
        resultado_cientifico_nao_utilizado=True,
        justificativa='Validade e prazo permitem executar.' if executar else 'Estimativa excede o prazo pré-fixado; etapa dispensada.')
    salvar_json(REG / ETAPA / 'decisao.json', decisao)
    registrar_estado(ETAPA, 'autorizada_por_condicoes' if executar else 'dispensada_por_prazo', decisao=decisao)


def exigir_decisao():
    d = ler_json(REG / ETAPA / 'decisao.json')
    assert d['executar'] and d['resultado_cientifico_nao_utilizado']
    conferir_arquivos(RAIZ, d['nucleo_auditado'])


def qualificar():
    import torch
    from treinamento.otimizacao import fixar_seed
    from experimentos.ablacao_linear_diaria.modelo import construir
    from experimentos.ablacao_linear_diaria.treinamento import ajustar
    exigir_decisao()
    with exclusividade(ETAPA, gpu=True):
        ambiente = verificar_ambiente()
        refs = pais()
        wf = ler_json(refs['walkforward'] / 'congelamento.json')
        destino = REG / ETAPA / 'qualificacoes' / str(time.time_ns())
        destino.mkdir(parents=True)
        rng = np.random.default_rng(99)
        sintetico = {fase: dict(x=rng.normal(size=(n, 6, 14)).astype('float32'),
                      y=rng.normal(size=n)*.02, ultimo_close=np.ones(n)*100.)
                      for fase, n in [('treino', 65), ('validacao', 31)]}
        dados = {k: retirar_timestamp(z) for k, z in sintetico.items()}
        for variante, total in [('A', 136952), ('L', 824)]:
            cfg = receita(wf['configs_blocos']['B1'], variante)
            fixar_seed(42)
            original = construir(cfg)
            pesos = {k: v.detach().cpu().clone() for k, v in original.state_dict().items()}
            assert sum(v.numel() for v in original.parameters()) == total
            del original
            fixar_seed(42)
            intervencao = construir(cfg)
            assert all(torch.equal(pesos[k], v.cpu()) for k, v in intervencao.state_dict().items())
            del intervencao
            torch.cuda.empty_cache()
            for replica in (1, 2):
                ajustar(dados, cfg, 42, destino / f'{variante}_{replica}', dict(tipo='sintetico'), epocas=2)
            conferir_ajustes(destino / f'{variante}_1', destino / f'{variante}_2')
        for bloco in configuracao()['blocos']:
            for fase in ('treino', 'validacao', 'teste'):
                z = carregar_npz(refs['walkforward'] / bloco['id'] / 'dados' / (fase+'.npz'))
                r = retirar_timestamp(z)
                assert np.all(r['x'][:, 0, :] == 0)
                for k in z:
                    np.testing.assert_array_equal(z[k][:, 1:, :] if k == 'x' else z[k], r[k][:, 1:, :] if k == 'x' else r[k])
        salvar_json(destino / 'qualificacao.json', dict(utc=agora(), situacao='aprovada', ambiente=ambiente,
            fontes=fontes(), repeticoes_sinteticas_exatas=2, parametros_A=136952, parametros_L=824,
            inicializacao_preservada=True, transformacao_local_sem_rng=True, populacoes_verificadas=12))
        salvar_json(REG / ETAPA / 'qualificacao.json', dict(arquivo=relativo(destino / 'qualificacao.json'), sha256=sha256(destino / 'qualificacao.json')))
        registrar_estado(ETAPA, 'qualificado')


def preparar():
    exigir_decisao()
    q = ler_json(REG / ETAPA / 'qualificacao.json')
    assert sha256(RAIZ / q['arquivo']) == q['sha256']
    conferir_arquivos(RAIZ, ler_json(RAIZ / q['arquivo'])['fontes'])
    refs = pais()
    wf = ler_json(refs['walkforward'] / 'congelamento.json')
    deps = [REG / ETAPA / 'decisao.json', refs['walkforward'] / 'congelamento.json']
    for bloco in configuracao()['blocos']:
        b = bloco['id']
        deps += [refs['walkforward'] / b / 'dados' / (fase+'.npz') for fase in ('treino', 'validacao', 'teste')]
        deps += [x for x in (refs['walkforward'] / b / 'ajustes').rglob('*') if x.is_file()]
        deps += [x for x in (refs['walkforward'] / 'publicacao' / b).rglob('*') if x.is_file()]
    deps += [refs['walkforward'] / 'publicacao/carteiras.zip', refs['walkforward'] / 'publicacao/operacoes.json']
    ptr, p, f = congelar(ETAPA, deps, RAIZ / q['arquivo'], dict(configs_blocos=wf['configs_blocos'], escalas=wf['escalas']))
    for bloco in configuracao()['blocos']:
        b = bloco['id']
        pasta = p / b / 'dados'
        pasta.mkdir(parents=True)
        for fase in ('treino', 'validacao', 'teste'):
            z = carregar_npz(refs['walkforward'] / b / 'dados' / (fase+'.npz'))
            np.savez_compressed(pasta / (fase+'.npz'), **retirar_timestamp(z))
        salvar_json(p / b / 'escalas.json', wf['escalas'][b])
        salvar_json(p / b / 'configuracao_referencia.json', wf['configs_blocos'][b])
    salvar_json(p / 'dados_preparados.json', {relativo(q): sha256(q) for q in p.rglob('*.npz') if 'fontes' not in q.parts})


def executar(retomar=False):
    from experimentos.ablacao_linear_diaria.treinamento import ajustar
    exigir_decisao()
    with exclusividade(ETAPA, gpu=True):
        ambiente = verificar_ambiente()
        ptr, p, f = contexto(ETAPA)
        assert not (p / 'treinamentos_concluidos.json').exists()
        if (p / 'inicio_treinamento.json').exists():
            assert retomar, 'Inspecionar processo anterior antes de retomar.'
        else:
            salvar_json(p / 'inicio_treinamento.json', dict(utc=agora(), ambiente=ambiente))
        conferir_arquivos(RAIZ, ler_json(p / 'dados_preparados.json'))
        refs, c = pais(), configuracao()
        feitos = []

        def rodar(nome, b, variante, seed, dados, controle=False, origem=None):
            destino = p / 'ajustes' / nome
            if destino.exists():
                conferir_unidade(destino)
            else:
                registrar_estado(ETAPA, 'treinando', ajuste=nome, concluidos=len(feitos), total=28)
                cfg = receita(f['extras']['configs_blocos'][b], variante)
                ajustar(dados, cfg, seed, destino, dict(execucao=ptr['id'], ajuste=nome, controle=controle))
                if origem is not None:
                    salvar_json(destino / 'controle.json', conferir_ajustes(origem, destino))
                selar_unidade(destino)
            feitos.append(dict(nome=nome, controle=controle, pasta=relativo(destino)))
            contexto(ETAPA)
            return destino

        original = {fase: carregar_npz(refs['walkforward'] / 'B1/dados' / (fase+'.npz')) for fase in ('treino', 'validacao')}
        for v in ('A', 'L'):
            rodar(f'controle_original_{v}_42', 'B1', v, 42, original, True, refs['walkforward'] / 'B1/ajustes' / f'{v}_42')
        for bloco in c['blocos']:
            b = bloco['id']
            dados = {fase: carregar_npz(p / b / 'dados' / (fase+'.npz')) for fase in ('treino', 'validacao')}
            for v in ('A', 'L'):
                primeiro = rodar(f'{b}_{v}_42', b, v, 42, dados)
                if b == 'B1':
                    rodar(f'controle_zero_{v}_42', b, v, 42, dados, True, primeiro)
                for seed in (17, 2026):
                    rodar(f'{b}_{v}_{seed}', b, v, seed, dados)
        assert len(feitos) == 28 and sum(x['controle'] for x in feitos) == 4
        salvar_json(p / 'treinamentos_concluidos.json', dict(utc=agora(), cientificos=24, controles=4, ajustes=feitos))
        registrar_estado(ETAPA, 'treinamentos_concluidos', cientificos=24, controles=4, avaliacao='pendente')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('acao', choices=['decidir', 'qualificar', 'preparar', 'executar'])
    parser.add_argument('--retomar', action='store_true')
    args = parser.parse_args()
    if args.acao == 'executar':
        executar(args.retomar)
    else:
        globals()[args.acao]()
