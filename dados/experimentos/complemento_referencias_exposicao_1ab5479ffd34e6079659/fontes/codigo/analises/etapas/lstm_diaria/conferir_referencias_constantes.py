"""Conferência e contraste ex-post da LSTM com posições constantes em 2026."""
import io
import zipfile
import numpy as np
from infraestrutura.artefatos import RAIZ, agora, conferir_arquivos, ler_json, salvar_json, sha256


def ic(diferenca):
    a=np.asarray(diferenca,np.float64);rng=np.random.default_rng(20261113);n=len(a);v=[]
    for _ in range(2000):
        ids=(rng.integers(0,n-13,int(np.ceil(n/14)))[:,None]+np.arange(14)).ravel()[:n]
        v.append(float(a[ids].mean()))
    return dict(media=float(a.mean()),ic95=np.quantile(v,[.025,.975]).tolist(),bloco=14,replicas=2000)


def principal():
    reg=RAIZ/'registros/lstm_diaria';ref=ler_json(reg/'referencias_constantes_2026.json');assert ref['situacao']=='concluido_conferido'
    ptr=ref['execucao'];p=RAIZ/ptr['pasta'];assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    assert sha256(p/'fechamento.json')==ref['fechamento_sha256'];fecho=ler_json(p/'fechamento.json')
    assert fecho['carteiras']==24 and fecho['controles']==4 and not fecho['falhas']
    conferir_arquivos(p,fecho['arquivos']);f=ler_json(p/'congelamento.json');conferir_arquivos(RAIZ,f['dependencias'])
    lstm=ler_json(reg/'execucao.json');lp=RAIZ/lstm['pasta'];assert sha256(lp/'congelamento.json')==lstm['congelamento_sha256']
    op=ler_json(lp/'publicacao/operacoes.json')['carteiras'];r=ler_json(p/'resultados.json');out={};desvios=[]
    with zipfile.ZipFile(p/'carteiras.zip') as zr,zipfile.ZipFile(lp/'publicacao/carteiras.zip') as zl:
        assert zr.testzip() is None and zl.testzip() is None
        for moeda in f['moedas']:
            out[moeda]={}
            for custo in (1,2,3):
                linha=next(q for q in op if q['moeda']==moeda and q['ano']==2026 and q['custo']==custo and q['unidade']=='LSTM_ensemble')
                with np.load(io.BytesIO(zl.read(linha['membro']+'/curva.npz')),allow_pickle=False) as q:
                    origens=q['origens_ms'].copy();saldo=q['saldos_diarios'].copy()
                referencias={}
                for nome in ('sempre_comprado','sempre_vendido'):
                    outra=next(q for q in r['carteiras'] if q['moeda']==moeda and q['custo']==custo and q['unidade']==nome)
                    m=outra['metricas'];calc=10000+m['pnl_movimento_contrato']+m['funding']-m['comissoes']-m['custo_slippage_ticks']
                    desvios.append(abs(calc-m['capital_final']))
                    with np.load(io.BytesIO(zr.read(outra['membro']+'/curva.npz')),allow_pickle=False) as q:
                        np.testing.assert_array_equal(q['origens_ms'],origens)
                        s=q['saldos_diarios'];np.testing.assert_allclose(s[-1]/s[0]-1,m['retorno_liquido'],atol=1e-12)
                        delta=np.diff(np.log(saldo))-np.diff(np.log(s))
                    referencias[nome]=dict(metricas=m,contraste_crescimento_log_diario=ic(delta))
                out[moeda][str(custo)]=dict(lstm_ensemble=linha['metricas'],referencias=referencias)
    assert len(desvios)==24 and max(desvios)<1e-6
    destino=reg/'conferencia_referencias_constantes_2026.json';assert not destino.exists()
    salvar_json(destino,dict(utc=agora(),situacao='aprovada',execucao=ptr,lstm=lstm,controles=4,carteiras=24,
        desvio_contabil_maximo_usdt=max(desvios),resultados=out,
        limite='Contraste ex-post no mesmo período conhecido, exposição diferente, IC exploratórios sem correção de multiplicidade ou seleção histórica.'))
    print('CONFERENCIA_REFERENCIAS_APROVADA',len(desvios),flush=True)


if __name__=='__main__':principal()
