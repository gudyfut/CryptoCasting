"""Figuras científicas derivadas exclusivamente da extensão concluída."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from previsao24.arquivos import RAIZ,ler_json,salvar_json,sha256,agora,verificar_arquivos


def main():
    p=ler_json(RAIZ/'registros/penalizacao/execucao.json'); pasta=RAIZ/p['caminho']
    if ler_json(pasta/'progresso.json')['status']!='concluido': raise ValueError('Aguardar conclusão e preservação antes/depois.')
    fases=('desenvolvimento','avaliacao'); dados={}; fontes={}
    for fase in fases:
        local=pasta/'analises'/fase
        verificar_arquivos(local,ler_json(local/'publicacao.json')['arquivos'])
        if ler_json(local/'auditoria.json')['status']!='aprovado': raise ValueError('Publicação não auditada.')
        dados[fase]=ler_json(local/'resumo.json')
        fontes[fase]=sha256(local/'publicacao.json')
    destino=RAIZ/'docs/figuras'/('penalizacao_'+p['id']); destino.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.bbox':'tight'})
    titulos={'desenvolvimento':'Desenvolvimento · 2023','avaliacao':'Avaliação retrospectiva · 2024–2025'}
    rotulos={'mamba_original':'Mamba original','mamba_corrigido':'Mamba corrigido','lstm':'LSTM','arima':'ARIMA','naive':'Naive'}
    arquivos=[]
    def salvar(fig,nome):
        for extensao in ('png','pdf'):
            arquivo=destino/f'{nome}.{extensao}'; fig.savefig(arquivo,dpi=200); arquivos.append(arquivo)
        plt.close(fig)
    fig,eixos=plt.subplots(1,2,figsize=(11,4.7),layout='constrained')
    for eixo,fase in zip(eixos,fases):
        r=dados[fase]['contrastes']
        for i,item in enumerate(r):
            ic=next(v for v in item['intervalos'] if v['dias']==14); centro=item['diferenca_mse']*1e6
            eixo.plot([ic['inferior']*1e6,ic['superior']*1e6],[i,i],color='#2b607c',linewidth=2)
            eixo.plot(centro,i,'o',color='#2b607c')
        eixo.axvline(0,color='#555555',linewidth=.9)
        eixo.set_yticks(range(len(r)),[rotulos[v['referencia']] for v in r]); eixo.invert_yaxis()
        eixo.set_title(titulos[fase]); eixo.set_xlabel('MSE corrigido − MSE da referência (×10⁻⁶)')
        eixo.grid(axis='x',alpha=.2)
    fig.suptitle('Diferenças pareadas e intervalos de 95% · blocos de 14 dias')
    salvar(fig,'diferencas_pareadas')
    fig,eixos=plt.subplots(1,2,figsize=(11,4.7),layout='constrained')
    estilos={'mamba_original':('#666666','o','--'),'mamba_corrigido':('#2b607c','s','-'),'lstm':('#8b4f13','^','-'),'naive':('#222222','D',':')}
    for eixo,fase in zip(eixos,fases):
        q=pd.DataFrame(dados[fase]['grupos']['contexto'])
        for modelo,(cor,marca,linha) in estilos.items():
            x=q[q.modelo==modelo].sort_values('contexto')
            eixo.plot(x.contexto/24,x.mse*1e3,label=rotulos[modelo],color=cor,marker=marca,linestyle=linha)
        eixo.set_xticks([1,3,7,14]); eixo.set_xlabel('Contexto (dias)'); eixo.set_ylabel('MSE médio (×10⁻³)'); eixo.set_title(titulos[fase]); eixo.grid(alpha=.2)
    eixos[0].legend(frameon=False)
    fig.suptitle('Erro por contexto · médias de escores, sem seleção de seed')
    salvar(fig,'contextos')
    fig,eixos=plt.subplots(1,2,figsize=(11,4.7),layout='constrained')
    for eixo,fase in zip(eixos,fases):
        q=pd.DataFrame(dados[fase]['pares'])
        medias=q.groupby(['par','contexto']).agg(original=('mse_original','mean'),corrigido=('mse_corrigido','mean')).reset_index()
        for moeda,marca in zip(('BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT'),('o','s','^','D')):
            x=medias[medias.par==moeda].sort_values('contexto')
            eixo.plot(x.contexto/24,100*(x.corrigido/x.original-1),marker=marca,label=moeda)
        eixo.axhline(0,color='#555555',linewidth=.9); eixo.set_xticks([1,3,7,14]); eixo.set_xlabel('Contexto (dias)')
        eixo.set_ylabel('Variação relativa do MSE (%)'); eixo.set_title(titulos[fase]); eixo.grid(alpha=.2)
    eixos[0].legend(frameon=False)
    fig.suptitle('Efeito descritivo por moeda · negativo favorece a correção')
    salvar(fig,'efeito_por_moeda')
    salvar_json(destino/'manifesto.json',{'execucao':p['id'],'utc':agora(),'fontes_publicacao':fontes,'codigo_sha256':sha256(Path(__file__)),
                'matplotlib':matplotlib.__version__,'arquivos':{a.name:sha256(a) for a in arquivos},
                'limites':'Contraste principal corrigido−original; demais comparações e decomposições exploratórias. Contextos mostram médias, não intervalos. Períodos já expostos.'})
    print(destino,flush=True)


if __name__=='__main__': main()
