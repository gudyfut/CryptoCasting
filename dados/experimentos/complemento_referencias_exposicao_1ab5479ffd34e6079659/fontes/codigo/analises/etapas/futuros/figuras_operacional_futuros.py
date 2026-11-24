"""Figura posterior da rodada operacional; somente leitura de resultados publicados."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,sha256,agora


def gerar():
    ptr=ler_json(RAIZ/'registros/operacional_futuros/execucao.json');p=RAIZ/ptr['pasta']
    if not (p/'publicacao/manifesto.json').exists():raise ValueError('Publicação auditada necessária.')
    calibracao=RAIZ/'registros/operacional_futuros/conferencias/calibracao_final.json'
    c=ler_json(calibracao);carteiras=ler_json(p/'publicacao/carteiras.json')
    nomes=list(ler_json(p/'receitas.json'));cores=['#2465a8','#cc6b21','#229779']
    fig,axs=plt.subplots(1,2,figsize=(14,7),gridspec_kw={'width_ratios':[1.3,1]},layout='constrained')
    fig.patch.set_facecolor('#fafbfd')
    for ax in axs:
        ax.set_facecolor('#fafbfd');ax.spines[['top','right','left']].set_visible(False)
        ax.grid(axis='x',color='#dce2ea',linewidth=.7);ax.set_axisbelow(True)
        ax.axvline(0,color='#5b6878',linewidth=1)
    for i,n in enumerate(nomes):
        for k,b in enumerate(['D1','D2','D3']):
            rs=[x for x in c['coortes'] if x['receita']==n and x['recorte']==b and x['fase']=='exploracao']
            if len(rs)!=1:raise ValueError('Coorte de calibração incompleta.')
            retornos=[100*x['retorno_medio'] for x in rs[0]['politicas']]
            # Todos os 12 pontos, sem selecionar somente o melhor.
            axs[0].scatter(retornos,np.full(len(retornos),i)+(k-1)*.18,s=28,color=cores[k],alpha=.65,
                           label=b if i==0 else None,edgecolors='none')
    axs[0].set_yticks(range(len(nomes)),nomes);axs[0].invert_yaxis()
    axs[0].set_title('Calibração C: todas as políticas testadas',loc='left',fontsize=13,pad=15)
    axs[0].set_xlabel('Retorno líquido por recorte (%) — média das três seeds')
    axs[0].legend(title='Recorte',frameon=False,loc='lower right')
    baselines=['caixa','comprado','vendido','tendencia'];rotulos=['Caixa','Compra retida','Venda retida','EMA 24/168']
    for i,n in enumerate(baselines):
        for k,b in enumerate(['D1','D2','D3']):
            rs=[x for x in carteiras if x['vinculo'].get('baseline')==n and x['vinculo']['recorte']==b and x['vinculo']['custo']==1]
            if len(rs)!=1:raise ValueError('Baseline ausente/duplicada.')
            axs[1].barh(i+(k-1)*.22,100*rs[0]['metricas']['retorno_liquido'],height=.20,color=cores[k],label=b if i==0 else None)
    axs[1].set_yticks(range(4),rotulos);axs[1].invert_yaxis()
    axs[1].set_title('Comparação S: baselines sem treino',loc='left',fontsize=13,pad=15)
    axs[1].set_xlabel('Retorno líquido por recorte (%) — custo base')
    axs[1].legend(frameon=False,loc='lower right')
    fig.suptitle('Pesquisa operacional em futuros BTCUSDT — desenvolvimento retrospectivo de 2023',fontsize=15,fontweight='bold')
    fig.supxlabel('C não é teste independente. D1/D2/D3 são carteiras separadas; retornos não se somam.\nCada ponto à esquerda representa uma das 12 políticas, não uma estratégia aprovada.',fontsize=10,color='#4a5665')
    destino=RAIZ/'docs/figuras/operacional_futuros_001.png';destino.parent.mkdir(parents=True,exist_ok=True)
    if destino.exists():raise FileExistsError('Figura já publicada; não sobrescrever sem revisão identificada.')
    fig.savefig(destino,dpi=160);plt.close(fig)
    salvar_json(RAIZ/'registros/operacional_futuros/conferencias/figuras_final.json',{
        'utc':agora(),'execucao':ptr,'fonte_sha256':sha256(__file__),
        'calibracao_sha256':sha256(calibracao),'carteiras_sha256':sha256(p/'publicacao/carteiras.json'),
        'arquivo':destino.relative_to(RAIZ).as_posix(),'sha256':sha256(destino)})
    return str(destino)


if __name__=='__main__':print(gerar())
