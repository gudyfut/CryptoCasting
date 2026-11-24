"""Gera tabelas editoriais de estudos conferidos, sem treinar ou simular."""
from pathlib import Path
import sys
from infraestrutura.artefatos import RAIZ, ler_json, sha256


def numero(v, casas=2):
    return f'{v:.{casas}f}'.replace('.',',')


def tabela_lstm():
    reg=RAIZ/'registros/lstm_diaria';ptr=ler_json(reg/'execucao.json');p=RAIZ/ptr['pasta']
    assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    fecho=ler_json(reg/'fechamento.json');assert sha256(RAIZ/fecho['arquivo'])==fecho['sha256']
    audit=ler_json(reg/'conferencia_posterior.json');assert audit['situacao']=='conferencia_posterior_aprovada'
    assert audit['execucao']==ptr and audit['carteiras']==96
    pred=ler_json(p/'publicacao/previsao.json');s=ler_json(reg/'estado.json')
    assert sha256(reg/'conferencia_posterior.json')==s['conferencia_posterior']['sha256']
    moedas=['BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT'];seeds=[42,17,2026]
    linhas=[r'\begin{tabular}{llrrrrrrr}',r'\toprule',
            r'& & \multicolumn{4}{c}{RMSE (pontos percentuais)} & \multicolumn{2}{c}{Retorno LSTM (\%)} & DD (\%) \\',
            r'\cmidrule(lr){3-6}\cmidrule(lr){7-8}',
            r'Ano & Ativo & LSTM média & LSTM ens. & A ens. & Naive & Média & Ensemble & LSTM ens. \\',r'\midrule']
    for ano in ('2025','2026'):
        for moeda in moedas:
            m=pred[moeda][ano]['metricas'];fin=audit['resultados'][moeda][ano]['financeiro']['1']['metricas']
            rmse=sum(m[f'LSTM_{k}']['rmse_retorno'] for k in seeds)/3*100
            ret=sum(fin[f'LSTM_{k}']['retorno_liquido'] for k in seeds)/3*100
            ensemble=fin['LSTM_ensemble']
            vals=[ano,moeda.removesuffix('USDT'),numero(rmse,4),numero(m['LSTM_ensemble']['rmse_retorno']*100,4),
                  numero(m['A_ensemble']['rmse_retorno']*100,4),numero(m['naive']['rmse_retorno']*100,4),
                  numero(ret),numero(ensemble['retorno_liquido']*100),numero(ensemble['drawdown_maximo']*100)]
            linhas.append(' & '.join(vals)+r' \\')
    linhas += [r'\bottomrule',r'\end{tabular}']
    destino=RAIZ/'escrita_tcc/latex/tabelas/lstm.tex'
    destino.write_text('\n'.join(linhas)+'\n',encoding='utf-8')
    print('TABELA_LSTM',destino,sha256(destino),flush=True)


def tabela_walkforward():
    reg=RAIZ/'registros/walkforward_diario';ptr=ler_json(reg/'execucao.json');p=RAIZ/ptr['pasta']
    assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    fecho=ler_json(reg/'fechamento.json');assert sha256(RAIZ/fecho['arquivo'])==fecho['sha256']
    audit=ler_json(reg/'conferencia_posterior.json');assert audit['situacao']=='conferencia_posterior_aprovada'
    assert audit['execucao']==ptr and audit['carteiras']==108
    estado=ler_json(reg/'estado.json')
    assert sha256(reg/'conferencia_posterior.json')==estado['conferencia_posterior']['sha256']
    prev=ler_json(p/'publicacao/previsao.json')
    linhas=[r'\begin{tabular}{llrrrrrrrrr}',r'\toprule',
            r'& & \multicolumn{5}{c}{MSE ($10^{-4}$)} & \multicolumn{2}{c}{Retorno ens. (\%)} & \multicolumn{2}{c}{DD ens. (\%)} \\',
            r'\cmidrule(lr){3-7}\cmidrule(lr){8-9}\cmidrule(lr){10-11}',
            r'Teste & $n$ & A média & L média & A ens. & L ens. & Naive & A & L & A & L \\',r'\midrule']
    for b in ('B1','B2','B3','B4'):
        r=audit['resumo'][b];a=r['A'];l=r['L']
        rotulo={'B1':'B1: jan--jun/2024','B2':'B2: jul--dez/2024','B3':'B3: jan--jun/2025','B4':'B4: jul--dez/2025'}[b]
        vals=[rotulo,str(r['origens']),numero(a['mse_medio']*1e4,4),numero(l['mse_medio']*1e4,4),
              numero(a['mse_ensemble']*1e4,4),numero(l['mse_ensemble']*1e4,4),
              numero(r['naive_mse']*1e4,4),numero(a['retorno_ensemble']*100),numero(l['retorno_ensemble']*100),
              numero(a['drawdown_ensemble']*100),numero(l['drawdown_ensemble']*100)]
        # A conferência independente e a publicação devem concordar para cada variante.
        for variante in ('A','L'):
            assert abs(r[variante]['mse_medio']-prev[b]['medias'][variante]['mse_retorno']['media'])<1e-14
            assert abs(r[variante]['mse_ensemble']-prev[b]['metricas'][f'{variante}_ensemble']['mse_retorno'])<1e-14
        assert r['origens']==prev[b]['populacao']
        assert abs(r['naive_mse']-prev[b]['metricas']['naive']['mse_retorno'])<1e-14
        linhas.append(' & '.join(vals)+r' \\')
    linhas += [r'\bottomrule',r'\end{tabular}']
    destino=RAIZ/'escrita_tcc/latex/tabelas/walkforward.tex'
    destino.write_text('\n'.join(linhas)+'\n',encoding='utf-8')
    print('TABELA_WALKFORWARD',destino,sha256(destino),flush=True)


if __name__=='__main__':
    if len(sys.argv)==1 or sys.argv[1]=='lstm':tabela_lstm()
    elif sys.argv[1]=='walkforward':tabela_walkforward()
    else:raise SystemExit('Uso: python -m analises.etapas.complemento_tcc [lstm|walkforward]')
