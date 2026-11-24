"""Calibra C por coorte completa; só então abre S. Sem novos treinos."""
from dataclasses import asdict
from itertools import product
from pathlib import Path
import numpy as np
import pandas as pd
from infraestrutura.artefatos import salvar_json,ler_json,sha256
from simulacao_operacoes.operacional.motor import Politica,simular,volatilidade_horaria
from simulacao_operacoes.operacional.auditoria import conferir
from avaliacao.metricas_operacionais import resumo_pareado


def politicas():
    return [Politica(*v) for v in product((0.,.001,.002),(.005,.01),(1,4))]


def ms(data): return int(pd.Timestamp(data,tz='UTC').timestamp()*1000)


def guardar(p,r,m,inicio,fim,vinculo):
    p=Path(p);p.mkdir(parents=True,exist_ok=False)
    auditoria=conferir(r,m,inicio,fim)
    np.savez_compressed(p/'curva.npz',patrimonio=r.pop('patrimonio'),segundos_utc=r.pop('segundos_utc'))
    salvar_json(p/'resultado.json',r)
    salvar_json(p/'auditoria.json',auditoria)
    salvar_json(p/'manifesto.json',{'vinculo':vinculo,'arquivos':{n:sha256(p/n) for n in ['curva.npz','resultado.json','auditoria.json']}})
    return r['metricas']


def pontuar_c(linhas):
    if not linhas or any(v['insolvente'] or v['saida_prudencial'] or v['operacoes']<20 or v['calmar'] is None for v in linhas):
        return None
    g=np.mean([v['crescimento_log_diario'] for v in linhas])
    if g<=0: return None
    return (float(np.median([v['calmar'] for v in linhas])),float(g),-float(np.mean([v['giro'] for v in linhas])))


def melhor(pontuacoes):
    escolhida=None;score=None
    for chave,novo in pontuacoes.items():
        if novo is None: continue
        if score is None or novo[0]>score[0]+1e-10 or (abs(novo[0]-score[0])<=1e-10 and novo[1:]>score[1:]):
            escolhida,score=chave,novo
    return escolhida


def avaliar_coorte(destino,mercado,h,receita,recorte,jobs,seeds,receita_id,fase):
    if set(jobs)!=set(seeds): raise ValueError('Coorte incompleta; não calibrar média parcial.')
    d=Path(destino);d.mkdir(parents=True,exist_ok=False);sigma=volatilidade_horaria(h)
    pol=politicas();resultados_c={i:[] for i in range(len(pol))}
    inicio,fim=map(ms,recorte['calibracao']);k,razao=receita['barreiras_payoff']
    for seed in seeds:
        z=np.load(Path(jobs[seed])/'ajuste/calibracao.npz')
        for i,p in enumerate(pol):
            r=simular(mercado,z['origens_ms'],z['previsoes'],sigma[z['indices']],receita['familia_alvo'],p,inicio,fim,k,razao)
            met=guardar(d/'C'/str(seed)/str(i),r,mercado,inicio,fim,{'receita':receita_id,'recorte':recorte['id'],
                'seed':seed,'fase':fase,'papel':'calibracao','politica':asdict(p)})
            resultados_c[i].append(met)
    pontuacoes={i:pontuar_c(v) for i,v in resultados_c.items()};escolha=melhor(pontuacoes)
    salvar_json(d/'politica_escolhida.json',{'receita':receita_id,'recorte':recorte['id'],'seeds':seeds,
        'indice':escolha,'politica':asdict(pol[escolha]) if escolha is not None else None,
        'motivo':'Nenhuma política C elegível: permanecer caixa.' if escolha is None else 'Maior mediana Calmar em C; desempates fixos.',
        'pontuacoes':pontuacoes,'teste_consultado_antes_da_escolha':False})
    inicio,fim=map(ms,recorte.get('comparacao',recorte.get('avaliacao')))
    cenarios=[('base',.0005,0),('custo2x',.001,0),('custo3x',.0015,0),('comprado',.0005,1),('vendido',.0005,-1)]
    linhas=[]
    for seed in seeds:
        z=np.load(Path(jobs[seed])/'ajuste/comparacao.npz')
        for nome,slip,lado in cenarios:
            previsoes=z['previsoes'] if escolha is not None else np.zeros_like(z['previsoes'])
            familia=receita['familia_alvo']
            if escolha is None:
                familia='payoff';previsoes=np.zeros((len(z['origens_ms']),2))
            p=pol[escolha] if escolha is not None else pol[0]
            r=simular(mercado,z['origens_ms'],previsoes,sigma[z['indices']],familia,p,inicio,fim,k,razao,slip,lado)
            met=guardar(d/'S'/str(seed)/nome,r,mercado,inicio,fim,{'receita':receita_id,'recorte':recorte['id'],
                'seed':seed,'fase':fase,'papel':'comparacao','cenario':nome,'politica':asdict(p)})
            linhas.append({'receita':receita_id,'recorte':recorte['id'],'seed':seed,'cenario':nome,'metricas':met,
                           'pasta':str((d/'S'/str(seed)/nome).resolve())})
    salvar_json(d/'conclusao.json',{'seeds':seeds,'politica':escolha,'carteiras_logicas':len(seeds)*17,
        'carteiras_fisicas':len(seeds)*17,'linhas':linhas})
    return linhas


def elegibilidade(linhas,recortes,seeds,reforco=False):
    base=[v for v in linhas if v['cenario']=='base'];stress=[v for v in linhas if v['cenario']=='custo2x']
    resumo=resumo_pareado(base,recortes,seeds);resumo_stress=resumo_pareado(stress,recortes,seeds)
    motivos=[]
    if any(v['metricas']['insolvente'] or v['metricas']['saida_prudencial'] for v in linhas): motivos.append('insolvencia_ou_prudencial')
    if any(v['metricas']['operacoes']<20 for v in linhas): motivos.append('menos_20_operacoes_em_alguma_carteira_S')
    for nome,r in [('base',resumo),('custo2x',resumo_stress)]:
        if r['medias']['crescimento_log_diario'] is None or r['medias']['crescimento_log_diario']<=0: motivos.append('crescimento_nao_positivo_'+nome)
    if resumo['score_calmar'] is None or resumo['score_calmar']<=0: motivos.append('calmar_nao_positivo_ou_indefinido')
    positivos=sum(np.mean([v['metricas']['crescimento_log_diario'] or -np.inf for v in base if v['recorte']==b])>0 for b in recortes)
    if positivos<2: motivos.append('menos_dois_recortes_positivos')
    if reforco:
        if sum(np.mean([v['metricas']['crescimento_log_diario'] or -np.inf for v in base if v['seed']==s])>0 for s in seeds)<6:
            motivos.append('menos_seis_seeds_positivas')
    return {'elegivel':not motivos,'motivos':motivos,'resumo':resumo,'stress2x':resumo_stress,
        'giro_medio':float(np.mean([v['metricas']['giro'] for v in base]))}
