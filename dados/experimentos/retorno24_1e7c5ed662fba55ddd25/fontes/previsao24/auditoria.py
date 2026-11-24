"""Auditoria independente dos escores, alinhamento, época e fronteiras."""
from pathlib import Path
import numpy as np
import pandas as pd
from .arquivos import ler_json,sha256,salvar_json,agora
from .metricas import calcular

def auditar_modelo(destino,blocos,celula):
    destino=Path(destino)
    resultado=ler_json(destino/'resultado.json')
    if celula['modelo'] in ('mamba','lstm'):
        epocas=ler_json(destino/'epocas.json')
        melhor=min(epocas,key=lambda e:e['mse_validacao'])
        if resultado['epoca_selecionada']!=melhor['epoca'] or not resultado['recarga_exata']:
            raise ValueError('Checkpoint não corresponde à melhor validação/recarga.')
    contagens={}
    for nome in ('validacao','teste','operacional'):
        salvo=pd.read_parquet(destino/f'previsoes_{nome}.parquet')
        esperado=blocos[nome]
        if len(salvo)!=len(esperado) or salvo['origem_utc'].duplicated().any():
            raise ValueError('População incompleta/duplicada.')
        for coluna in ('origem_utc','destino_utc','indice_hora','close','preco_destino','alvo'):
            if not salvo[coluna].reset_index(drop=True).equals(esperado[coluna].reset_index(drop=True)):
                raise ValueError(f'Alinhamento/valor divergente: {nome}/{coluna}')
        if not np.isfinite(salvo['previsao']).all():
            raise ValueError('Previsões inválidas.')
        if nome!='operacional':
            refeito=calcular(salvo['alvo'],salvo['previsao'])
            for k,v in refeito.items():
                original=resultado['metricas'][nome][k]
                if v is None:
                    if original is not None:
                        raise ValueError('Métrica indefinida adulterada.')
                elif not np.isclose(v,original,rtol=1e-12,atol=1e-14):
                    raise ValueError(f'Métrica divergente: {nome}/{k}')
            # Fórmula independente da função de métricas para o escore principal.
            diferencas=salvo['previsao'].to_numpy()-salvo['alvo'].to_numpy()
            mse=float(np.dot(diferencas,diferencas)/len(diferencas))
            if not np.isclose(mse,refeito['mse'],rtol=1e-12,atol=1e-14):
                raise ValueError('Recálculo independente de MSE divergiu.')
        contagens[nome]=len(salvo)
    arquivos={p.name:sha256(p) for p in sorted(destino.iterdir()) if p.is_file() and p.name not in ('auditoria.json','tentativa.json')}
    recibo={'status':'aprovado','utc':agora(),'celula':celula,'contagens':contagens,'arquivos':arquivos}
    salvar_json(destino/'auditoria.json',recibo)
    return recibo
