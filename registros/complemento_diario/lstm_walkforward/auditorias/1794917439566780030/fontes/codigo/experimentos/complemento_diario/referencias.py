"""Herança auditada das quatro referências operacionais, sem selecionar lados."""
from decimal import Decimal
import io
import json
import math
import zipfile
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, agora, conferir_arquivos, ler_json, salvar_json, sha256
from experimentos.generalizacao_moedas.avaliacao import carregar_mercado
from simulacao_operacoes.continuidade_diaria.auditoria_grade import conferir
from .comum import pais, carregar_npz, congelar, contexto, exclusividade, fechar, registrar_estado
from .inventario import REG, relativo
from .fontes_operacionais import casos_fixos, entradas
from .auditar import perto


def executar():
    etapa = 'referencias_exposicao'
    with exclusividade(etapa):
        refs = pais()
        rc = ler_json(RAIZ / 'registros/lstm_diaria/referencias_constantes_2026.json')
        pc = RAIZ / rc['execucao']['pasta']
        assert sha256(pc / 'congelamento.json') == rc['execucao']['congelamento_sha256']
        assert sha256(pc / 'fechamento.json') == rc['fechamento_sha256']
        conferir_arquivos(pc, ler_json(pc / 'fechamento.json')['arquivos'])
        conferir_arquivos(RAIZ, ler_json(pc / 'congelamento.json')['dependencias'])
        casos = [x for x in casos_fixos() if x['variante'] == 'A']
        itens = []
        for caso in casos:
            for nome in ('naive', 'comprar_manter', 'sempre_comprado', 'sempre_vendido'):
                if caso['populacao'] == 'fixa_2025':
                    pasta = refs['continuidade']
                    lista = ler_json(pasta / 'resultados.json')['resultados']
                    encontrados = [x for x in lista if x['moeda'] == caso['moeda'] and x['fase'] == 'teste'
                        and x['custo'] == 1 and x['unidade'] == nome and x['modo'] == ('passivo' if nome == 'comprar_manter' else 'liquida')]
                else:
                    pasta = pc if nome.startswith('sempre') else refs['extensao']
                    lista = ler_json(pasta / ('resultados.json' if pasta == pc else 'operacoes.json'))['carteiras']
                    encontrados = [x for x in lista if x['moeda'] == caso['moeda'] and x['custo'] == 1 and x['unidade'] == nome]
                assert len(encontrados) == 1, (caso['id'], nome, encontrados)
                itens.append(dict(caso=caso, referencia=nome, origem=relativo(pasta / 'carteiras.zip'), linha=encontrados[0]))
        deps = entradas(casos) + [RAIZ / x['origem'] for x in itens] + [pc / 'fechamento.json', pc / 'congelamento.json']
        qp = ler_json(REG / 'qualificacao_operacional.json')
        if not (REG / etapa / 'execucao.json').exists():
            congelar(etapa, deps, RAIZ / qp['arquivo'], dict(referencias=itens))
        ptr, p, f = contexto(etapa)
        assert itens == f['extras']['referencias']
        linhas, auditorias = [], []
        chave, mercado = None, None
        for item in itens:
            caso, nome, linha = item['caso'], item['referencia'], item['linha']
            if caso['mercado']['pasta'] != chave:
                del mercado
                mercado = carregar_mercado(caso['mercado'])
                chave = caso['mercado']['pasta']
            z = carregar_npz(RAIZ / caso['previsao'])
            with zipfile.ZipFile(RAIZ / item['origem']) as arq:
                r = json.loads(arq.read(linha['membro'] + '/resultado.json'))
                with np.load(io.BytesIO(arq.read(linha['membro'] + '/curva.npz'))) as q:
                    cv = {k: q[k].copy() for k in q.files}
            np.testing.assert_array_equal(cv['origens_ms'], z['origens_ms'])
            assert r['metricas'] == linha['metricas']
            regras = dict(caso['regras'], slippage_por_lado=.0001)
            lado = 1 if nome in ('sempre_comprado', 'comprar_manter') else -1 if nome == 'sempre_vendido' else None
            agenda, modo = None, 'liquida'
            if nome == 'comprar_manter':
                modo = 'agenda'
                indice = np.searchsorted(mercado['tempo'], z['origens_ms'][0]+regras['latencia_minutos']*60000)
                fill = math.ceil(mercado['negocio'][indice, 0]*1.0001/regras['tick_preco'])*regras['tick_preco']
                lotes = math.floor(regras['capital_inicial']*regras['fracao_nocional']/fill/regras['passo_quantidade'])
                agenda = np.full(len(z['origens_ms']), lotes)
            audit = conferir(r, cv, mercado, regras, modo, z['origens_ms'], z['ultimo_close'], z['ultimo_close'], lado, agenda)
            D = lambda x: Decimal(str(x))
            saldo = D(10000)-sum((D(o['delta'])*D(o['preenchimento'])+D(o['comissao']) for o in r['ordens']), D(0))+sum((D(e['valor']) for e in r['funding']), D(0))
            perto(float(saldo), cv['saldos_diarios'][-1], 1e-7)
            perto(linha['metricas']['retorno_liquido'], float(saldo)/10000-1)
            linhas.append(dict(populacao=caso['populacao'], moeda=caso['moeda'], referencia='caixa' if nome == 'naive' else nome,
                    origem=item['origem'], membro=linha['membro'], **linha['metricas']))
            auditorias.append(dict(populacao=caso['populacao'], moeda=caso['moeda'], referencia=nome, **audit))
        assert len(linhas) == 32
        pub = p / 'publicacao'
        pub.mkdir(exist_ok=False)
        pd.DataFrame(linhas).to_csv(pub / 'referencias.csv', index=False)
        salvar_json(pub / 'referencias.json', dict(utc=agora(), linhas=linhas, auditorias=auditorias,
            limite='Todas as quatro referências publicadas; nenhuma escolha retrospectiva de lado; exposições diferentes.'))
        fechar(etapa, dict(referencias_herdadas=32, conferidas_independentemente=32))
        salvar_json(REG / etapa / 'conferencia_posterior.json', dict(utc=agora(), situacao='aprovada',
            arquivo=relativo(pub / 'referencias.json'), sha256=sha256(pub / 'referencias.json'), execucao=ptr,
            metodo='Ledgers herdados recalculados por conta independente e Decimal; não houve nova simulação.'))
        registrar_estado(etapa, 'auditado', referencias=32)


if __name__ == '__main__':
    executar()
