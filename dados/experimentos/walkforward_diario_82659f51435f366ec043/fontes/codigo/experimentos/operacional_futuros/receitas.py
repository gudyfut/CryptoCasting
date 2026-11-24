"""Espaço fechado de receitas e pareamentos; sem acesso a resultados finais."""
from copy import deepcopy
from infraestrutura.artefatos import RAIZ,ler_json,identidade


def proposta():
    return ler_json(RAIZ/'configuracoes/operacional_futuros_001_proposta.json')


def iniciais():
    r={'representacao':'crua','contexto_horas':168,'momentum':False,'volatilidade':False,
       'volume_relativo':False,'d_state':16,'taxa':.0002,'barreiras_payoff':[1.,1.5],
       'familia_alvo':'terminal'}
    p=deepcopy(r);p['familia_alvo']='payoff'
    return {'R0':r,'P0':p}


def validar(r):
    esp=proposta()['espaco_receitas']
    if set(r)!=set(esp)|{'familia_alvo'} or r['familia_alvo'] not in ('terminal','payoff'):
        raise ValueError('Receita contém fatores não autorizados.')
    for k,dominio in esp.items():
        if r[k] not in dominio or type(r[k]) is not type(dominio[0]):
            raise ValueError('Valor fora do espaço: '+k)
    if r['familia_alvo']=='terminal' and r['barreiras_payoff']!=[1.,1.5]:
        raise ValueError('Barreiras R0 fixas.')
    return identidade(r)


def propor(pai,campo,valor,existentes):
    if pai not in existentes or campo not in proposta()['espaco_receitas']:
        raise ValueError('Pai ou campo inválido.')
    r=deepcopy(existentes[pai]);r[campo]=valor;h=validar(r)
    if sum(r[k]!=existentes[pai][k] for k in r)!=1:
        raise ValueError('Proposta deve alterar exatamente um fator.')
    if any(identidade(v)==h for v in existentes.values()):
        raise ValueError('Receita já executada/proposta.')
    return r
