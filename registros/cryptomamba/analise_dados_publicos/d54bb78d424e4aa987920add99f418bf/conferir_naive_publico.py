"""Persistência nos splits públicos, usando as classes originais sem seus imports/CLI."""
import ast
import math
import torch
import pandas as pd
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,sha256,agora,conferir_arquivos

dest=RAIZ/'registros/cryptomamba/analise_dados_publicos/d54bb78d424e4aa987920add99f418bf'
orig=RAIZ/'registros/cryptomamba/fontes_externas/fef42727861a9c3a32241283ab981ef21a49e291'
prov=ler_json(dest/'proveniencia.json')
conferir_arquivos(dest,{n:r['sha256'] for n,r in prov['arquivos'].items()})
globais={'torch':torch}
fontes={}
for nome,classe in [('data_utils/dataset.py','CMambaDataset'),('data_utils/data_transforms.py','DataTransform')]:
    caminho=orig/nome
    arvore=ast.parse(caminho.read_text(encoding='utf-8-sig'))
    definicao=next(x for x in arvore.body if isinstance(x,ast.ClassDef) and x.name==classe)
    # As duas classes foram lidas; não executar imports, conversor, downloads ou CLI externos.
    exec(compile(ast.Module(body=[definicao],type_ignores=[]),str(caminho),'exec'),globais)
    fontes[nome]=sha256(caminho)
metricas={}
for parte in ('train','val','test'):
    q=pd.read_csv(dest/(parte+'.csv'))
    d=globais['CMambaDataset'](q,parte,14,globais['DataTransform'](False,True))
    erros=[];reais=[]
    for i in range(len(d)):
        s=d[i]
        assert tuple(s['features'].shape)==(6,14)
        assert s['features'][4,-1].item()==s['Close_old'].item()
        erros.append(float(s['Close_old']-s['Close']));reais.append(float(s['Close']))
    mse=math.fsum(e*e for e in erros)/len(d)
    metricas[parte]={'n':len(d),'rmse_usd':math.sqrt(mse),'mae_usd':math.fsum(abs(e) for e in erros)/len(d),
        'mape_percentual':100*math.fsum(abs(e/y) for e,y in zip(erros,reais))/len(d),'dtype':'float32 das classes originais'}
    a=ler_json(dest/'analise_naive.json')['metricas_globais'][parte]['naive']
    for k in ('rmse_usd','mae_usd','mape_percentual'):
        assert math.isclose(a[k],metricas[parte][k],rel_tol=1e-5,abs_tol=.001)
r={'utc':agora(),'status':'conferido','classes_origem_sha256':fontes,'verificador_sha256':sha256(__file__),
    'metricas_pelas_classes_originais':metricas,'natureza':'Somente baseline de persistência sem treino/uso de GPU; não reproduz as previsões do artigo.',
    'limite':'População exata e checkpoints da tabela do artigo não certificados; não declarar refutação a partir deste diagnóstico.'}
p=dest/'conferencia_classes_publicas.json'
if p.exists():raise FileExistsError('Recibo existente; preservar.')
salvar_json(p,r)
print(r)
