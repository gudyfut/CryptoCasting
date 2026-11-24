"""Avaliação pareada e carteiras novas, preservando referências e falhas."""
from copy import deepcopy
import io
import json
import zipfile
import numpy as np
import torch
from infraestrutura.artefatos import RAIZ, ler_json, salvar_json, sha256
from experimentos.fechamento_ramos_diarios.avaliacao import medir, agregar, intervalo
from experimentos.generalizacao_moedas.avaliacao import carregar_mercado
from simulacao_operacoes.continuidade_diaria.simulador import simular
from simulacao_operacoes.continuidade_diaria.auditoria_grade import conferir
from .modelo import LSTMDiaria
from .treinamento import inferir


def ler_rede(pasta):
    selecao=ler_json(pasta/'selecao.json')
    assert sha256(pasta/selecao['checkpoint'])==selecao['sha256']
    ck=torch.load(pasta/selecao['checkpoint'],map_location='cpu',weights_only=True)
    rede=LSTMDiaria().to('cuda');rede.load_state_dict(ck['pesos'],strict=True)
    return rede.eval()


def previsoes_referencias(base,ano,z,c):
    nomes=[f'{v}_{s}' for v in ('A','L') for s in c['seeds']]+['A_ensemble','L_ensemble','naive','linear']
    resultado={}
    for nome in nomes:
        caminho=(base/'publicacao/previsoes'/f'teste_{nome}.npz') if ano==2025 else (base/f'{nome}.npz')
        with np.load(caminho,allow_pickle=False) as q:
            np.testing.assert_array_equal(z['origens_ms'],q['origens_ms'])
            np.testing.assert_array_equal(z['ultimo_close'],q['ultimo_close'])
            np.testing.assert_array_equal(z['alvo'],q['alvo_retorno'])
            resultado[nome]=q['previsoes_retorno'].copy()
    return resultado


def executar(p,f,progresso):
    c=f['configuracao'];p25=RAIZ/f['referencias']['referencia_2025']['pasta'];p26=RAIZ/f['referencias']['referencia_2026']['pasta']
    f25=ler_json(p25/'congelamento.json');f26=ler_json(p26/'congelamento.json')
    periodo=RAIZ/f26['referencia_periodo']['pasta'];mercados26=ler_json(periodo/'mercados.json')
    pub=p/'publicacao';pub.mkdir(exist_ok=False)
    saida={};carteiras=[];auditorias=[];falhas=[]
    with zipfile.ZipFile(pub/'carteiras.zip','x',compression=zipfile.ZIP_DEFLATED) as zipout:
        for moeda in c['moedas']:
            base25=p25/moeda;base26=p26/moeda;config=ler_json(base25/'configuracao.json')
            val=dict(np.load(base25/'dados/validacao.npz',allow_pickle=False))
            redes={s:ler_rede(p/moeda/'ajustes'/f'seed_{s}') for s in c['seeds']}
            for s,rede in redes.items():
                with np.load(p/moeda/'ajustes'/f'seed_{s}'/'validacao.npz') as q:
                    np.testing.assert_array_equal(inferir(rede,val['x']),q['previsoes'])
            saida[moeda]={}
            for ano in (2025,2026):
                with np.load(base25/'dados/teste.npz' if ano==2025 else base26/'entradas.npz',allow_pickle=False) as q:
                    z={k:q[k].copy() for k in q.files}
                z['alvo']=z['y'] if ano==2025 else z['alvo_retorno']
                ref=previsoes_referencias(base25 if ano==2025 else base26,ano,z,c)
                if ano==2025:
                    arima=RAIZ/f['referencias']['referencia_continuidade']['pasta']/f'arima_{moeda}'/'teste.npz'
                    with np.load(arima,allow_pickle=False) as q:
                        np.testing.assert_array_equal(z['origens_ms'],q['origens_ms'])
                        ref['arima']=q['previsoes_retorno'].copy()
                prev={f'LSTM_{s}':inferir(redes[s],z['x']) for s in c['seeds']}
                precos={n:z['ultimo_close']*(1+v) for n,v in prev.items()}
                precos['LSTM_ensemble']=np.mean([precos[f'LSTM_{s}'] for s in c['seeds']],axis=0)
                prev['LSTM_ensemble']=precos['LSTM_ensemble']/z['ultimo_close']-1
                metricas={n:medir(z['alvo'],v) for n,v in {**ref,**prev}.items()}
                contrastes={}
                for referencia in (('A','L','naive','linear','arima') if ano==2025 else ('A','L','naive','linear')):
                    for forma in ('individuais','ensemble'):
                        if forma=='individuais':
                            esq=np.array([(prev[f'LSTM_{s}']-z['alvo'])**2 for s in c['seeds']])
                            dir=np.array([(ref[f'{referencia}_{s}']-z['alvo'])**2 for s in c['seeds']]) if referencia in ('A','L') else (ref[referencia]-z['alvo'])**2
                        else:
                            esq=(prev['LSTM_ensemble']-z['alvo'])**2
                            chave=f'{referencia}_ensemble' if referencia in ('A','L') else referencia
                            dir=(ref[chave]-z['alvo'])**2
                        contrastes[f'LSTM_menos_{referencia}_{forma}']={str(b):intervalo(esq-dir,b,c['bootstrap'],forma=='individuais') for b in c['bootstrap']['blocos']}
                d=pub/moeda/str(ano);d.mkdir(parents=True)
                for nome,ret in prev.items():
                    np.savez_compressed(d/f'{nome}.npz',previsoes_retorno=ret,previsoes=precos[nome],
                         alvo_retorno=z['alvo'],origens_ms=z['origens_ms'],ultimo_close=z['ultimo_close'])
                saida[moeda][str(ano)]=dict(metricas=metricas,media_lstm=agregar([metricas[f'LSTM_{s}'] for s in c['seeds']]),
                                             contrastes_mse=contrastes)
                mercado=carregar_mercado(f25['referencias']['moedas'][moeda]['mercado_minuto'] if ano==2025 else mercados26[moeda])
                for custo,slip in enumerate(c['slippage_cenarios'],1):
                    regras=deepcopy(config['operacoes']);regras['slippage_por_lado']=slip
                    for nome,preco in precos.items():
                        ident=f'{moeda}/{ano}/{nome}/custo_{custo}'
                        try:
                            resultado,curva=simular(z['origens_ms'],preco,z['ultimo_close'],mercado,regras,'liquida')
                            auditoria=conferir(resultado,curva,mercado,regras,'liquida',z['origens_ms'],preco,z['ultimo_close'],None)
                        except ValueError as erro:
                            if 'Violação prudencial' not in str(erro):raise
                            falhas.append(dict(identidade=ident,erro=str(erro)))
                            zipout.writestr(ident+'/falha.json',json.dumps(falhas[-1],ensure_ascii=False))
                            continue
                        zipout.writestr(ident+'/resultado.json',json.dumps(dict(regras=regras,**resultado),ensure_ascii=False,allow_nan=False))
                        b=io.BytesIO();np.savez_compressed(b,origens_ms=z['origens_ms'],**curva)
                        zipout.writestr(ident+'/curva.npz',b.getvalue())
                        carteiras.append(dict(moeda=moeda,ano=ano,unidade=nome,custo=custo,membro=ident,metricas=resultado['metricas']))
                        auditorias.append(dict(identidade=ident,**auditoria))
                        progresso(carteiras_concluidas=len(carteiras),falhas_prudenciais=len(falhas),carteiras_previstas=96)
                del mercado
            del redes;torch.cuda.empty_cache()
    assert len(carteiras)+len(falhas)==96
    with zipfile.ZipFile(pub/'carteiras.zip') as z:assert z.testzip() is None
    salvar_json(pub/'previsao.json',saida)
    salvar_json(pub/'operacoes.json',dict(carteiras=carteiras,falhas=falhas,limite='Carteiras independentes; slippage provisório; sem liquidação real.'))
    salvar_json(pub/'auditoria_operacoes.json',dict(auditorias=auditorias,total=len(auditorias),falhas=falhas))
    return dict(carteiras=len(carteiras),falhas_prudenciais=len(falhas),pares_previsao=8,
                limite='Contrastes preditivos retrospectivos; não demonstram equivalência nem lucro futuro.')
