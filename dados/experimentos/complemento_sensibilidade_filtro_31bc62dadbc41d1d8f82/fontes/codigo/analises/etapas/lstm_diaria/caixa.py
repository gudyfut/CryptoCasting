"""Contraste retrospectivo das carteiras LSTM com permanecer em caixa."""
import io
import zipfile
import numpy as np
from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256


def intervalo(amostras):
    a=np.asarray(amostras,np.float64)
    if a.ndim==1:a=a[None,:];sortear=False
    else:sortear=True
    n=a.shape[1];rng=np.random.default_rng(20261113);medias=[]
    for _ in range(2000):
        dias=(rng.integers(0,n-13,int(np.ceil(n/14)))[:,None]+np.arange(14)).ravel()[:n]
        seeds=rng.integers(0,len(a),len(a)) if sortear else np.arange(len(a))
        medias.append(float(a[seeds][:,dias].mean()))
    return dict(media=float(a.mean()),ic95=np.quantile(medias,[.025,.975]).tolist(),
                bloco=14,replicas=2000,reamostra_seeds=sortear)


def principal():
    reg=RAIZ/'registros/lstm_diaria';ptr=ler_json(reg/'execucao.json');p=RAIZ/ptr['pasta']
    assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    fechamento=ler_json(reg/'fechamento.json');assert sha256(RAIZ/fechamento['arquivo'])==fechamento['sha256']
    audit=ler_json(reg/'conferencia_posterior.json');assert audit['situacao']=='conferencia_posterior_aprovada'
    operacoes=ler_json(p/'publicacao/operacoes.json');assert not operacoes['falhas']
    saida={};seeds=[42,17,2026]
    with zipfile.ZipFile(p/'publicacao/carteiras.zip') as z:
        assert z.testzip() is None
        for moeda in ('BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT'):
            saida[moeda]={}
            for ano in (2025,2026):
                saida[moeda][str(ano)]={}
                for custo in (1,2,3):
                    curvas={}
                    for s in (*seeds,'ensemble'):
                        nome=f'LSTM_{s}';r=next(x for x in operacoes['carteiras'] if x['moeda']==moeda and x['ano']==ano and x['custo']==custo and x['unidade']==nome)
                        with np.load(io.BytesIO(z.read(r['membro']+'/curva.npz')),allow_pickle=False) as arq:
                            saldo=arq['saldos_diarios'];assert (saldo>0).all()
                            np.testing.assert_allclose(saldo[-1]/saldo[0]-1,r['metricas']['retorno_liquido'],atol=1e-12)
                            curvas[nome]=np.diff(np.log(saldo))
                    saida[moeda][str(ano)][str(custo)]=dict(
                        media_seeds=intervalo(np.array([curvas[f'LSTM_{s}'] for s in seeds])),
                        ensemble=intervalo(curvas['LSTM_ensemble']))
    destino=reg/'contrastes_caixa.json';assert not destino.exists()
    salvar_json(destino,dict(utc=agora(),execucao=ptr,conferencia_sha256=sha256(reg/'conferencia_posterior.json'),
        natureza='Análise posterior dos 24 cenários, sem novo backtest.',resultados=saida,
        limite='Crescimento log diário contra caixa zero; intervalos exploratórios não corrigidos para múltiplos testes, seleção histórica nem regimes futuros.'))
    print('CONTRASTES_CAIXA',len(saida),flush=True)


if __name__=='__main__':principal()
