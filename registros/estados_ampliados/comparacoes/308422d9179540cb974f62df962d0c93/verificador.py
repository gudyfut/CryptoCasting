"""Médias por seed e contrastes pareados dos estados8/16/32/64; somente leitura."""
from itertools import combinations
from pathlib import Path
from uuid import uuid4
import math
import shutil
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,agora,ler_json,salvar_json,sha256,conferir_arquivos
from treinamento.preservacao import conferir
from avaliacao.publicacao import conferir_previsoes,contraste_temporal


def media(valores):
    return float(np.mean(valores))


def consolidar():
    destino=RAIZ/'registros/estados_ampliados/comparacoes'/uuid4().hex;destino.mkdir(parents=True)
    try:
        ponteiro=ler_json(RAIZ/'registros/estados_ampliados/estado64/execucao.json');pasta=RAIZ/ponteiro['pasta']
        conferir_arquivos(pasta,{'congelamento.json':ponteiro['congelamento_sha256']})
        congelado=ler_json(pasta/'congelamento.json');c=congelado['contrato']['configuracao']
        conferir_arquivos(RAIZ,congelado['contrato']['fontes'])
        pub=ler_json(pasta/'publicacao.json');base=pasta/pub['pasta']
        conferir_arquivos(base,{'manifesto.json':pub['manifesto_sha256']});conferir_arquivos(base,ler_json(base/'manifesto.json')['arquivos'])
        r=ler_json(base/'resultados.json')
        dados=RAIZ/c['entradas_pasta'];conferir_arquivos(dados,ler_json(dados/'manifesto.json')['arquivos'])
        partes={b:pd.read_parquet(dados/f'{b}.parquet') for b in ('validacao','teste','operacional')}
        pred={};ajustes={};fontes={}
        for estado,seeds in [(8,c['seeds']),(16,c['seeds_pareadas']),(32,c['seeds']),(64,c['seeds'])]:
            for s in seeds:
                k=f'estado{estado}_{s}';t=RAIZ/r['por_ajuste'][k]['tentativa_origem'];conferir(t)
                ajuste=ler_json(t/'resultado.json');assert ajuste['recarga_exata']
                for b in partes:
                    q=pd.read_parquet(t/f'previsoes_{b}.parquet');conferir_previsoes(q,partes[b],ajuste['metricas'].get(b));pred[k,b]=q
                assert ajuste['metricas']==r['por_ajuste'][k]['metricas']
                ajustes[k]=ajuste;fontes[k]={'tentativa':t.relative_to(RAIZ).as_posix(),'conclusao_sha256':sha256(t/'conclusao.json')}
        grupos={};perdas={}
        for nome,seeds,estados in [('tres_seeds',c['seeds_pareadas'],[8,16,32,64]),('seis_seeds',c['seeds'],[8,32,64])]:
            grupos[nome]={'seeds':seeds,'estados':{}}
            for estado in estados:
                ks=[f'estado{estado}_{s}' for s in seeds]
                g={'n_seeds':len(seeds),'predicao':{},'operacao':{},'treinamento':{},'trimestres':{}}
                for b in ('validacao','teste'):
                    metricas=[ajustes[k]['metricas'][b] for k in ks]
                    g['predicao'][b]={chave:media([m[chave] for m in metricas]) for chave in
                        ('mse','rmse','mae','habilidade_mse','acuracia_direcional','acerto_balanceado_direcional','vies')}
                    g['predicao'][b]['desvio_padrao_mse_seeds']=float(np.std([m['mse'] for m in metricas],ddof=1))
                    g['predicao'][b]['seeds_melhores_naive']=sum(m['habilidade_mse']>0 for m in metricas)
                    erros=np.mean([(pred[k,b].previsao.to_numpy()-pred[k,b].alvo.to_numpy())**2 for k in ks],axis=0)
                    perdas[nome,estado,b]=erros
                    publicado=r['medias'][b][f'estado{estado}_{"tres" if len(seeds)==3 else "seis"}']['mse']
                    assert math.isclose(g['predicao'][b]['mse'],publicado,rel_tol=1e-12)
                for perfil in ('base','agravado','bruto_mesmos_sinais'):
                    vs=[r['por_ajuste'][k]['spot'][perfil] for k in ks]
                    assert all(v['retorno_auditavel'] and v['risco_auditavel'] for v in vs)
                    g['operacao'][perfil]={chave:media([v[chave] for v in vs]) for chave in
                        ('retorno_liquido','drawdown','capital_final','entradas_planejadas','custos_observados')}
                    g['operacao'][perfil]['desvio_padrao_retorno_seeds']=float(np.std([v['retorno_liquido'] for v in vs],ddof=1))
                    g['operacao'][perfil]['seeds_lucrativas']=sum(v['retorno_liquido']>0 for v in vs)
                for chave in ('parametros','epoca_selecionada','epocas_executadas','segundos','memoria_cuda_maxima_bytes'):
                    g['treinamento'][chave]=media([ajustes[k][chave] for k in ks])
                for trimestre in ('1','2','3','4'):
                    mse=media([r['por_ajuste'][k]['trimestres'][trimestre]['mse'] for k in ks]);naive=r['por_ajuste']['naive']['trimestres'][trimestre]['mse']
                    g['trimestres'][trimestre]={'mse':mse,'habilidade_naive':1-mse/naive}
                grupos[nome]['estados'][str(estado)]=g
        contrastes={}
        for nome,dados_grupo in grupos.items():
            estados=[int(n) for n in dados_grupo['estados']];contrastes[nome]={}
            for b in ('validacao','teste'):
                contrastes[nome][b]={}
                for menor,maior in combinations(estados,2):
                    a,z=perdas[nome,maior,b],perdas[nome,menor,b]
                    q=contraste_temporal(partes[b].origem_utc,a,z,c['bootstrap'])
                    q['aumento_mse_percentual_observado']=float(100*(a.mean()/z.mean()-1))
                    q['ic14_inclui_zero']=bool(q['ic95']['14'][0]<=0<=q['ic95']['14'][1])
                    contrastes[nome][b][f'estado{maior}_menos_estado{menor}']=q
        resultado={'utc':agora(),'natureza':'consolidação posterior exploratória; nenhum treino ou nova seleção',
            'fonte_publicacao':base.relative_to(RAIZ).as_posix(),'fonte_manifesto_sha256':pub['manifesto_sha256'],
            'grupos':grupos,'contrastes':contrastes,'tentativas':fontes,
            'referencias':{k:r['por_ajuste'][k]['metricas'] for k in ('naive','arima','lstm_17','lstm_42','lstm_2026')},
            'metodo_medias':'média aritmética das métricas por seed, inclusive RMSE; não ensemble, carteira combinada ou raiz do MSE médio',
            'limites':['As comparações consolidadas incluem todos os pares solicitados; são exploratórias e sem correção global de multiplicidade.',
                       'Bootstrap temporal é condicional aos modelos ajustados; não trata seeds como séries de mercado independentes.',
                       'Média de drawdown não é drawdown de carteira média. Retorno médio não é retorno de ensemble.',
                       'Política e contabilidade R0 mantidas. Sensibilidades Binance e manutenção de posição permanecem separadas.',
                       'Os resultados de2024/2025 já eram conhecidos ao propor novas variantes; avaliação retrospectiva.']}
        shutil.copy2(Path(__file__),destino/'verificador.py');salvar_json(destino/'comparacao.json',resultado)
        salvar_json(destino/'manifesto.json',{'arquivos':{p.name:sha256(p) for p in destino.iterdir() if p.is_file()}})
        salvar_json(RAIZ/'registros/estados_ampliados/comparacao_atual.json',{'arquivo':(destino/'comparacao.json').relative_to(RAIZ).as_posix(),'sha256':sha256(destino/'comparacao.json')})
        return destino/'comparacao.json'
    except BaseException:
        import traceback
        salvar_json(destino/'falha.json',{'utc':agora(),'erro':traceback.format_exc()});raise


if __name__=='__main__':
    print(consolidar())
