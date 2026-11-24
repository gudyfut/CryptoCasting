"""Recalcula RMSE e acurácia balanceada das previsões LSTM preservadas."""
import numpy as np
from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256


def principal():
    reg=RAIZ/'registros/lstm_diaria';ptr=ler_json(reg/'execucao.json');p=RAIZ/ptr['pasta']
    assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    fecho=ler_json(reg/'fechamento.json');assert sha256(RAIZ/fecho['arquivo'])==fecho['sha256']
    publicacao=p/'publicacao/previsao.json';m=ler_json(publicacao);verificacoes=0;dif=0.
    for moeda in m:
        for ano in m[moeda]:
            for nome in ('LSTM_42','LSTM_17','LSTM_2026','LSTM_ensemble'):
                with np.load(p/'publicacao'/moeda/ano/f'{nome}.npz',allow_pickle=False) as q:
                    y=q['alvo_retorno'];previsao=q['previsoes_retorno']
                    assert (y>0).any() and (y<0).any()
                    valores={'acerto_balanceado':float(((previsao[y>0]>0).mean()+(previsao[y<0]<0).mean())/2),
                             'rmse_retorno':float(np.sqrt(np.mean((previsao-y)**2)))}
                    for chave,valor in valores.items():
                        erro=abs(valor-m[moeda][ano]['metricas'][nome][chave]);dif=max(dif,erro)
                        assert erro<1e-14;verificacoes+=1
    assert verificacoes==64
    destino=reg/'metricas_adicionais.json';assert not destino.exists()
    salvar_json(destino,dict(utc=agora(),situacao='aprovada',execucao=ptr,verificacoes=verificacoes,
        diferenca_maxima=dif,fonte_codigo_sha256=sha256(__file__),publicacao_sha256=sha256(publicacao),
        escopo='RMSE e média de recalls de alta/queda; não reexecuta rede ou backtest.'))
    print('METRICAS_ADICIONAIS_APROVADAS',verificacoes,flush=True)


if __name__=='__main__':principal()
