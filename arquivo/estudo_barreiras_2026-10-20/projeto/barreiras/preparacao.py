"""Gate anterior a qualquer treinamento real; não seleciona por desempenho."""
from pathlib import Path
import numpy as np
import pandas as pd

from .arquivos import RAIZ, agora, salvar_json, ler_json, sha256, identidade
from .dados import verificar_dataset
from .configuracao import PARES, HORIZONTES, FOLDS, COLUNAS
from .particoes import separar, ajustar_escalas
from .auditoria import rotulo_referencia


def auditar_preparacao(pasta: Path):
    meta=verificar_dataset(pasta)
    if meta['primeiro_minuto']!=int(pd.Timestamp('2021-01-01',tz='UTC').timestamp()//60) or meta['fim_minuto']!=int(pd.Timestamp('2024-01-01',tz='UTC').timestamp()//60):
        raise ValueError('Este ciclo exige desenvolvimento 2021–2023 e mantém o final fechado.')
    for nome,h in meta['assinatura']['codigo'].items():
        if sha256(pasta/'fontes'/nome)!=h or sha256(RAIZ/'barreiras'/nome)!=h:
            raise ValueError('Transformação vigente difere da identidade do dataset.')
    chave=identidade({'dataset':meta['id'],'auditoria':sha256(Path(__file__)),
          'rotulo_referencia':sha256(RAIZ/'barreiras/auditoria.py'),
          'particoes':sha256(RAIZ/'barreiras/particoes.py')})[:20]
    destino=RAIZ/'historico/qualificacoes'/f'dados_{chave}.json'
    if destino.exists():
        anterior=ler_json(destino)
        if anterior['status']=='aprovado':
            return anterior
    resultado={'id':chave,'dataset':meta['id'],'inicio_utc':agora(),'status':'em_execucao','recortes':[]}
    salvar_json(destino,resultado)
    try:
        comuns=np.load(pasta/'origens_comuns.npy')
        referencia={}
        for par in PARES:
            minutos=np.load(pasta/par/'minutos.npy',mmap_mode='r')
            horas=pd.read_parquet(pasta/par/'horas.parquet')
            for h in HORIZONTES:
                q=pd.read_parquet(pasta/par/f'amostras_H{h}.parquet')
                for r in q.itertuples(index=False):
                    y,s,p,amb=rotulo_referencia(minutos,r.entrada_indice,r.distancia,h)
                    if y!=r.classe or (y>=0 and (s!=r.saida_indice or amb!=r.ambiguo or not np.isclose(p,r.preco_saida,rtol=1e-12))):
                        raise ValueError(f'Rótulo independente divergiu: {par}/H{h}/{r.origem_utc}')
                for f in ('DB1','DB2','DB3','DB4'):
                    blocos=separar(q,comuns,f)
                    matriz,escalas=ajustar_escalas(horas,blocos['treino'])
                    for nome,parte in blocos.items():
                        if nome!='operacional':
                            ref=referencia.setdefault((f,nome),parte.origem_utc)
                            if not ref.equals(parte.origem_utc):
                                raise ValueError('Comparação não utiliza origens comuns entre moedas/horizontes.')
                        validos=parte.loc[parte.classe>=0]
                        toques=int(validos.classe.ne(1).sum());ambiguos=int(validos.ambiguo.sum())
                        if len(validos) and (ambiguos/len(validos)>.01 or (toques and ambiguos/toques>.05)):
                            raise ValueError('Ambiguidade operacional excedeu o gate de resolução.')
                        resultado['recortes'].append({'par':par,'horizonte':h,'fold':f,'particao':nome,
                            'n':len(parte),'nao_observados':int((parte.classe<0).sum()),
                            'ambiguos':ambiguos,'classes':[int((parte.classe==k).sum()) for k in range(3)],
                            'distancia_mediana':float(parte.distancia.median()),
                            'duracao_mediana_minutos':float((validos.saida_conhecida_indice-validos.entrada_indice).median())})
                        for i in np.unique(np.linspace(0,len(parte)-1,min(8,len(parte)),dtype=int)):
                            r=parte.iloc[i];j=int(r.indice_hora);fim=int(r.entrada_indice)-1
                            if not np.isfinite(matriz[j-167:j+1]).all():
                                raise ValueError('Input elegível contém valor não finito.')
                            closes=minutos[fim-169*60+59:fim:60,3]
                            if not np.isclose(np.std(np.diff(np.log(closes)),ddof=1),r.sigma,rtol=1e-8,atol=1e-12):
                                raise ValueError('Volatilidade não corresponde aos minutos passados.')
                            a=minutos[fim-60:fim];prev=minutos[fim-61,3]
                            x=[np.log(a[0,0]/prev),np.log(a[:,1].max()/prev),np.log(a[:,2].min()/prev),np.log(a[-1,3]/prev),np.log1p(a[:,4].sum())]
                            if not np.allclose(horas.loc[j,list(COLUNAS)].to_numpy(float),x,rtol=1e-12,atol=1e-12):
                                raise ValueError('Features divergentes dos minutos brutos.')
                    if pd.Timestamp(escalas['ultima_hora_ajuste'])>=FOLDS[f].limites()[1]:
                        raise ValueError('Scaler consultou validação.')
                print(f'Auditoria pré-treino: {par}/H{h}, {len(q)} rótulos recalculados.',flush=True)
        resultado.update(status='aprovado',fim_utc=agora(),recortes_verificados=len(resultado['recortes']))
        salvar_json(destino,resultado)
        return resultado
    except Exception as erro:
        resultado.update(status='falha',fim_utc=agora(),erro=f'{type(erro).__name__}: {erro}')
        salvar_json(destino,resultado)
        raise
