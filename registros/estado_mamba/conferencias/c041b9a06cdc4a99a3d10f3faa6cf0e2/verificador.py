"""Auditoria posterior das duas rodadas OHLCV; não chama executores nem ajusta pesos."""
from pathlib import Path
import argparse
import math
import shutil
from uuid import uuid4
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,agora,ler_json,salvar_json,sha256,conferir_arquivos
from treinamento.preservacao import conferir
from avaliacao.publicacao import conferir_previsoes,contraste_temporal
from avaliacao.mercado import carregar_minutos


def proximo(a,b):
    if a is None or b is None:
        assert a is b
    else:
        assert math.isclose(float(a),float(b),rel_tol=1e-11,abs_tol=1e-14),(a,b)


def conferir_pesos(tentativa,estado,consumo):
    import torch
    s=ler_json(tentativa/'selecao.json')
    conferir_arquivos(tentativa,{s['arquivo']:s['sha256']})
    p=torch.load(tentativa/s['arquivo'],map_location='cpu',weights_only=True)
    m=p['modelo']
    assert m['familia']=='mamba' and m['configuracao']['mamba']['estado']==estado
    assert m['especificacao']['identidade']==consumo
    assert m['especificacao']['contexto']==168 and len(m['especificacao']['canais'])==5
    estados={k:list(v.shape) for k,v in m['pesos'].items() if k.endswith('A_log')}
    assert len(estados)==2 and all(v==[64,estado] for v in estados.values())
    parametros=sum(v.numel() for v in m['pesos'].values())
    assert parametros==(17185 if estado==8 else 20257)
    return {'checkpoint':s['arquivo'],'sha256':s['sha256'],'estado':estado,'formas_A_log':estados,'parametros':parametros,
            'epoca':s['epoca'],'contrato_dados':m['especificacao']}


def financeiro(q,publicacao,chave,mercado,primeiro,cfg):
    f,s=cfg['operacao']['taxa'],cfg['operacao']['slippage']
    limiar=math.log((1+s)*(1+f)/((1-s)*(1-f)))
    fim=int(pd.Timestamp(cfg['divisao']['teste'][1],tz='UTC').timestamp()//60)
    entradas={}
    for row in q.itertuples():
        t=pd.Timestamp(row.origem_utc)
        e=int(t.timestamp()//60)+1
        if t.hour==0 and t.minute==0 and e+1440<fim and row.previsao>limiar:
            entradas[t.isoformat()]=row
    recibos={}
    for nome,agravado in [('base',False),('agravado',True)]:
        taxa=cfg['operacao']['taxa_agravada'] if agravado else f
        slip=cfg['operacao']['slippage_agravado'] if agravado else s
        ops=ler_json(publicacao/chave/f'operacoes_{nome}.json')
        assert len(ops)==len(entradas)
        capital=float(cfg['operacao']['capital']);custos=0.
        for o in ops:
            assert o['origem_utc'] in entradas
            row=entradas[o['origem_utc']]
            e=int(pd.Timestamp(row.origem_utc).timestamp()//60)+1;v=e+1440
            assert (o['entrada_minuto'],o['saida_minuto'])==(e,v)
            a,b=mercado[[e-primeiro,v-primeiro],0]
            assert np.isfinite([a,b]).all() and (mercado[[e-primeiro,v-primeiro],5]>0).all()
            proximo(o['preco_entrada'],a);proximo(o['preco_saida'],b)
            quantidade=capital/(a*(1+slip)*(1+taxa))
            novo=quantidade*b*(1-slip)*(1-taxa)
            custo=quantidade*a*((1+slip)*(1+taxa)-1)+quantidade*b*(1-(1-slip)*(1-taxa))
            proximo(o['capital_entrada'],capital);proximo(o['quantidade'],quantidade);proximo(o['capital_saida'],novo)
            proximo(o['custos'],custo);proximo(o['retorno_liquido'],novo/capital-1)
            custos+=custo;capital=novo
        recibos[nome]={'operacoes':len(ops),'capital_final':capital,'custos':custos,'retorno_liquido':capital/10000-1}
    return recibos


def auditar(destino):
    destino.mkdir(parents=True,exist_ok=False)
    try:
        novo=ler_json(RAIZ/'registros/estado_mamba/execucao.json');antigo=ler_json(RAIZ/'registros/treinamento/execucao.json')
        assert novo['id']=='dcf4b0ed9012f7247bce' and antigo['id']=='ab5baf3eab3a2e66d8b2'
        assert novo['pasta']!=antigo['pasta']
        congelados={};pubs={}
        for rotulo,p in [('novo',novo),('anterior',antigo)]:
            pasta=RAIZ/p['pasta'];conferir_arquivos(pasta,{'congelamento.json':p['congelamento_sha256']})
            f=ler_json(pasta/'congelamento.json');c=f['contrato'];congelados[rotulo]=f
            conferir_arquivos(RAIZ,c['fontes']);conferir_arquivos(pasta/'fontes',c['fontes'])
            conferir_arquivos(pasta,{'protocolo.md':c['protocolo_sha256']})
            assert ler_json(pasta/'progresso.json')['status']=='concluido'
            assert not ler_json(pasta/'processo.json')['ativo']
            pp=ler_json(pasta/'publicacao.json');pub=pasta/pp['pasta'];pubs[rotulo]=pub
            conferir_arquivos(pub,{'manifesto.json':pp['manifesto_sha256']})
            conferir_arquivos(pub,ler_json(pub/'manifesto.json')['arquivos'])
        cfg=congelados['novo']['contrato']['configuracao'];antes=congelados['anterior']['contrato']['configuracao']
        diferentes={k:{'anterior':antes.get(k),'novo':cfg.get(k)} for k in set(cfg)|set(antes) if antes.get(k)!=cfg.get(k)}
        permitidas={'versao','ciclo','hipotese','mamba','modelos','seeds','controles_reproducao','configuracao_modelos','referencia_execucao','seeds_pareadas','controle'}
        assert set(diferentes)<=permitidas
        assert cfg['mamba']==dict(antes['mamba'],estado=8)
        arq_n=ler_json(RAIZ/cfg['configuracao_modelos']);arq_a=ler_json(RAIZ/antes['configuracao_modelos']);arq_a['mamba']['estado']=8
        assert arq_n==arq_a
        dados=RAIZ/cfg['entradas_pasta'];assert cfg['entradas_pasta']==antes['entradas_pasta']
        conferir_arquivos(dados,ler_json(dados/'manifesto.json')['arquivos'])
        partes={b:pd.read_parquet(dados/f'{b}.parquet') for b in ('validacao','teste','operacional')}
        ref=congelados['novo']['contrato']['referencias'];tentativas={};auditorias={};previsoes={}
        raiz=RAIZ/novo['pasta']/'celulas'
        assert {p.name for p in raiz.iterdir() if p.is_dir()}=={f'mamba_{s}' for s in cfg['seeds']}
        for seed in cfg['seeds']:
            ts=list((raiz/f'mamba_{seed}').glob('tentativa_*'));fechadas=[p for p in ts if (p/'conclusao.json').exists()]
            assert len(fechadas)==1
            tentativas[f'estado8_{seed}']=fechadas[0]
        for chave,d in ref.items():
            p=RAIZ/d['pasta'];conferir_arquivos(p,{'conclusao.json':d['conclusao_sha256']});tentativas[chave]=p
        resultado=ler_json(pubs['novo']/'resultados.json')
        assert set(resultado['por_ajuste'])==set(tentativas)
        m,primeiro=carregar_minutos(RAIZ/cfg['mercado_pasta'],cfg['par'])
        for chave,t in tentativas.items():
            conferir(t);r=ler_json(t/'resultado.json');assert r['recarga_exata']
            auditorias[chave]={'pasta':t.relative_to(RAIZ).as_posix(),'origem':'novo' if chave.startswith('estado8_') else 'herdado','metricas':{}}
            for b in partes:
                q=pd.read_parquet(t/f'previsoes_{b}.parquet');previsoes[chave,b]=q
                auditorias[chave]['metricas'][b]=conferir_previsoes(q,partes[b],r['metricas'].get(b))
                if b!='operacional':
                    assert r['metricas'][b]==resultado['por_ajuste'][chave]['metricas'][b]
            if chave.startswith(('estado8_','estado16_')):
                pesos=conferir_pesos(t,8 if chave.startswith('estado8_') else 16,congelados['novo']['contrato']['consumo'])
                hist=ler_json(t/'epocas.json');escolhida=min(hist,key=lambda e:(e['mse_validacao'],e['epoca']))
                assert pesos['epoca']==escolhida['epoca']==r['epoca_selecionada']
                proximo(escolhida['mse_validacao'],r['metricas']['validacao']['mse'])
                auditorias[chave]['pesos']=pesos
            financeiro_refeito=financeiro(previsoes[chave,'operacional'],pubs['novo'],chave,m,primeiro,cfg)
            for nome,v in financeiro_refeito.items():
                s=resultado['por_ajuste'][chave]['spot'][nome]
                for campo in ('capital_final','retorno_liquido'):proximo(v[campo],s[campo])
                proximo(v['custos'],s['custos_observados']);assert v['operacoes']==s['entradas_planejadas']
            auditorias[chave]['financeiro']=financeiro_refeito
        grupos={'estado8_pareadas':[f'estado8_{s}' for s in cfg['seeds_pareadas']],
                'estado16_pareadas':[f'estado16_{s}' for s in cfg['seeds_pareadas']],
                'estado8_seis':[f'estado8_{s}' for s in cfg['seeds']],
                'lstm_herdada':[f'lstm_{s}' for s in cfg['seeds_pareadas']], 'naive':['naive'],'arima':['arima']}
        for b in ('validacao','teste'):
            perdas={g:np.mean([(previsoes[k,b].previsao.to_numpy()-previsoes[k,b].alvo.to_numpy())**2 for k in ks],axis=0) for g,ks in grupos.items()}
            for g,v in perdas.items():proximo(v.mean(),resultado['medias'][b][g]['mse'])
            for a,z in [('estado8_pareadas','estado16_pareadas'),('estado8_seis','naive'),('estado8_pareadas','lstm_herdada')]:
                c=contraste_temporal(partes[b].origem_utc,perdas[a],perdas[z],cfg['bootstrap']);salvo=resultado['contrastes'][b][f'{a}_menos_{z}']
                proximo(c['diferenca_mse_a_menos_b'],salvo['diferenca_mse_a_menos_b'])
                for dias,v in c['ic95'].items():
                    for i in (0,1):proximo(v[i],salvo['ic95'][dias][i])
        shutil.copy2(Path(__file__),destino/'verificador.py')
        recibo={'utc':agora(),'status':'aprovado','execucao':novo['id'],'referencia':antigo['id'],
            'novos_ajustes':6,'herdados':len(ref),'diferencas_configuracao':diferentes,
            'mesmo_dataset':True,'mesmas_populacoes_escalas_e_alvo':True,
            'protocolos_fontes_pesos_publicacoes_separados':True,
            'auditorias':auditorias,'contrastes_bootstrap_refeitos':True,'simulacao_pontas_sinais_taxas_refeitos':True,
            'limites':['Pesos inspecionados em CPU; recarga preditiva CUDA atestada pelo executor, não repetida aqui.',
                       'Drawdown foi atestado pela publicação; esta conferência refaz sinais, pontas, quantidades, custos e capital.',
                       'Não verifica livro/fills, nem certifica backup externo ou aceite acadêmico.'],
            'estado_modelos_anterior':ler_json(RAIZ/'registros/estado_mamba/preservacao_r0_depois.json')}
        salvar_json(destino/'conclusao.json',recibo)
        salvar_json(destino/'manifesto.json',{'arquivos':{p.name:sha256(p) for p in destino.iterdir() if p.is_file()}})
        return recibo
    except BaseException:
        import traceback
        salvar_json(destino/'falha.json',{'utc':agora(),'erro':traceback.format_exc()});raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--destino',type=Path);a=p.parse_args()
    destino=a.destino or RAIZ/'registros/estado_mamba/conferencias'/uuid4().hex
    r=auditar(destino)
    print({'status':r['status'],'recibo':str(destino/'conclusao.json'),'novos':r['novos_ajustes'],'herdados':r['herdados']})
