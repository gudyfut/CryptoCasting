"""Verificação da proposta; não equivale a autorização ou qualificação integrada."""
from datetime import date
from itertools import product
from pathlib import Path
import math

from infraestrutura.artefatos import RAIZ, ler_json, sha256, conferir_arquivos

CONFIGURACAO = RAIZ / 'configuracoes/operacional_futuros_001_proposta.json'


def validar_proposta(c):
    if c['proposta'] != 'operacional_futuros_001' or c['versao'] != 2 or c['executavel']:
        raise ValueError('Esta ação confere somente a proposta2, não executa estudos.')
    if c['autorizacao']['treinamento'] or c['autorizacao']['conta_real'] or c['autorizacao']['api_paga']:
        raise ValueError('A proposta não pode incorporar autorização ainda não recebida.')
    if c['mercado']['candles_horas'] != 1 or c['mercado']['prazo_maximo_horas'] != 24:
        raise ValueError('Candle/horizonte fora desta rodada.')
    if c['criterio']['teto_drawdown_aprovado'] is not None:
        raise ValueError('O pesquisador não escolheu um teto de drawdown.')
    ss = c['seeds']
    if ss['exploracao'] != [42,17,2026] or ss['reforco_e_final'] != [42,17,2026,7,123,31415,271828,161803]:
        raise ValueError('Seeds/pareamento divergentes.')
    p = c['politicas_calibracao']
    politicas = list(product(p['margem_adicional_entrada'],p['risco_nominal_stop'],p['cadencia_horas_utc']))
    if len(politicas) != len(set(politicas)) or len(politicas) != p['total'] or p['total'] != 12:
        raise ValueError('Grade de políticas incompleta ou repetida.')
    if not all(math.isfinite(m) and m >= 0 and 0 < r <= .01 and h in [1,4] for m,r,h in politicas):
        raise ValueError('Política fora do escopo.')
    for f in c['calendario']['desenvolvimento']+c['calendario']['final_retrospectiva']:
        ns=['treino','validacao','calibracao','comparacao' if 'comparacao' in f else 'avaliacao']
        pares=[tuple(date.fromisoformat(v) for v in f[n]) for n in ns]
        if any(a>=b for a,b in pares) or any(pares[i][1] != pares[i+1][0] for i in range(3)):
            raise ValueError('T/V/C/S não estão em ordem temporal.')
    b = c['orcamento_proposto']
    if sum(b[k] for k in ['ajustes_exploracao','controles_iniciais','ajustes_reforco_novos','ajustes_finais','controles_finais']) != b['ajustes_novos_maximo'] or b['ajustes_novos_maximo'] != 185:
        raise ValueError('Orçamento de ajustes divergente.')
    if sum(b[k] for k in ['carteiras_logicas_exploracao','carteiras_logicas_reforco','carteiras_logicas_final','carteiras_baselines']) != b['carteiras_logicas_maximo'] or b['carteiras_logicas_maximo'] != 3620:
        raise ValueError('Orçamento de carteiras divergente.')
    if c['operacao_noturna']['ativado'] or c['operacao_noturna']['janela_horas_proposta'] != 12:
        raise ValueError('Prompt preparado não pode ser tratado como goal ativado.')
    e=c['execucao_proposta']
    if e['comissao_taker_por_lado'] != .0005 or e['deslizamentos_por_preenchimento'] != [.0005,.001,.0015]:
        raise ValueError('Custos de pesquisa alterados.')
    if c['calendario']['purga_minima_minutos'] < 1442 or c['rede_inicial']['familia'] != 'Mamba1_oficial_CUDA':
        raise ValueError('Purga/backend incompatíveis.')
    return {'proposta':c['proposta'],'versao':c['versao'],'politicas':len(politicas),'ajustes_maximos':185,'avaliacoes_logicas_maximas':3620}


def conferir(integridade=False):
    c=ler_json(CONFIGURACAO)
    resultado=validar_proposta(c)
    resultado.update({'configuracao_sha256':sha256(CONFIGURACAO),'executor_implementado':True,
                      'escopo_desta_checagem':'proposta e dados; consultar qualificação e autorização próprias'})
    p=RAIZ/'registros/operacional_futuros/dados/execucao.json'
    resultado['dados_desenvolvimento_publicados']=p.exists()
    if p.exists():
        ptr=ler_json(p);d=RAIZ/ptr['pasta']
        if sha256(d/'manifesto.json') != ptr['manifesto_sha256']:
            raise ValueError('Manifesto de mercado alterado.')
        m=ler_json(d/'manifesto.json')
        if integridade:
            conferir_arquivos(d,m['arquivos'])
        resultado['dados']=ptr
        resultado['marca_funding_ausente']=m['contrato']['precos_funding_ausentes']
    resultado['limite']='Checagem de proposta/dados não inicia mercado. Preparar exige qualificação vinculada às fontes; executar exige identidade e autorização próprias.'
    return resultado
