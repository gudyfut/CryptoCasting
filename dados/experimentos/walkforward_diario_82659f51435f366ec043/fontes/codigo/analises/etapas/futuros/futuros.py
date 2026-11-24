"""Conferência posterior de leitura e relatório; nunca chama execução/treinamento."""
import math
from pathlib import Path
import pandas as pd
from infraestrutura.artefatos import RAIZ,agora,ler_json,salvar_json,sha256,conferir_arquivos

def analisar():
    ptr=ler_json(RAIZ/'registros/futuros/execucao.json');p=RAIZ/ptr['pasta'];fim=ler_json(p/'fechamento.json')
    assert fim['situacao']=='concluido_conferido' and fim['concluidas']==804
    pub=p/'publicacao';assert sha256(pub/'manifesto.json')==fim['publicacao_sha256']
    manifesto=ler_json(pub/'manifesto.json');conferir_arquivos(pub,manifesto['arquivos']);conferir_arquivos(p,manifesto['carteiras'])
    r=ler_json(pub/'resultados.json');linhas=[]
    for item in r['carteiras']:
        pasta=p/'carteiras'/item['chave'];conferir_arquivos(pasta,ler_json(pasta/'manifesto.json')['arquivos'])
        resumo=ler_json(pasta/'resumo.json');tr=ler_json(pasta/'operacoes.json');ev=ler_json(pasta/'funding.json')
        saldo=resumo['capital_inicial'];fees=0.;slip=0.;fund=0.;pnl=0.
        for t in tr:
            assert math.isclose(saldo,t['saldo_antes'],abs_tol=1e-8)
            taxas=t['taxa_entrada']+t['taxa_saida'];q=t['quantidade_btc']
            liquido=q*(t['saida']-t['entrada'])-taxas+t['funding_liquido'];saldo+=liquido
            assert math.isclose(saldo,t['saldo_depois'],abs_tol=1e-8)
            fees+=taxas;slip+=t['slippage_usdt'];fund+=t['funding_liquido'];pnl+=q*(t['preco_saida_meio']-t['preco_entrada_meio'])
        fluxo=sum(-x['quantidade_btc']*x['taxa']*x['mark_price'] for x in ev)
        assert math.isclose(fluxo,fund,abs_tol=1e-7)
        for nome,valor in [('capital_final',saldo),('retorno_liquido',saldo/resumo['capital_inicial']-1),('comissoes',fees),('slippage',slip),('funding_liquido',fund),('pnl_sem_custos_execucao',pnl)]:
            assert math.isclose(valor,resumo[nome],abs_tol=1e-7) and math.isclose(valor,item[nome],abs_tol=1e-7)
        linhas.append(item)
    q=pd.DataFrame(linhas);campos=['modelo','politica','modo','cenario']
    media=q.groupby(['bloco']+campos).retorno_liquido.mean().groupby(campos).mean()
    for x in r['medias_globais']:assert math.isclose(media.loc[tuple(x[k] for k in campos)],x['retorno_liquido'],abs_tol=1e-12)
    s=q[(q.seed.notna())&(q.politica=='sinal24')&(q.cenario=='base')]
    por_seed=s.groupby(['modelo','seed','modo']).retorno_liquido.mean().unstack('modo')
    contrastes={}
    for modelo in ['astra','crua']:
        z=por_seed.loc[modelo];delta=z.bilateral-z.comprada
        cel=s[s.modelo==modelo].pivot(index=['bloco','seed'],columns='modo',values='retorno_liquido')
        contrastes[modelo]={'delta_medio_pp':100*float(delta.mean()),'seeds_com_bilateral_melhor':int((delta>0).sum()),'pares_bloco_seed_bilateral_melhor':int((cel.bilateral>cel.comprada).sum()),
            'bilateral_media_retornos_por_seed_min':float(z.bilateral.min()),'bilateral_media_retornos_por_seed_max':float(z.bilateral.max()),'bilateral_dp_medias_seeds':float(z.bilateral.std(ddof=1))}
    destino=RAIZ/'registros/futuros/conferencias'/agora().replace(':','').replace('+','_');destino.mkdir(parents=True,exist_ok=False)
    recibo={'utc':agora(),'execucao':ptr,'carteiras':len(q),'status':'conferido','publicacao_sha256':sha256(pub/'manifesto.json'),'contrastes_descritivos':contrastes,'limite':'Recalculo independente de ledger/agregacoes; nao repete simulador nem certifica trajetoria de liquidacao real.'}
    salvar_json(destino/'conferencia.json',recibo)
    texto=['# Simulação posterior de futuros — resultados F01','',f'Execução `{ptr["id"]}` concluída e conferida: **804 carteiras, zero treinamentos novos**, 64 séries herdadas. [Método](protocolo_futuros.md), [arquitetura](arquitetura_operacoes.md), [estado](../registros/futuros/estado.json).','',
    'Resultados retrospectivos de quatro blocos independentes (181/183/180/183 dias), oito seeds por receita. As tabelas usam primeiro a média das seeds de cada bloco e depois peso igual entre blocos. **Não são retorno anual nem retorno acumulado de dois anos.** Cada carteira inicia com10.000USDT.','',
    '## Comparação principal: mesmo futuro, cenário base','',
    'Sinal diário: positivo compra, negativo abre venda quando permitido. Encerra/reabre após24h. Comissão0,05% e slippage0,05% por lado, além de funding histórico.','',
    '| Receita | Modalidade | Retorno líquido médio | Drawdown médio de mark close | Operações médias | Funding médio USDT |','|---|---|---:|---:|---:|---:|']
    for x in r['medias_globais']:
        if x['modelo'] in ['astra','crua'] and x['politica']=='sinal24' and x['cenario']=='base':
            texto.append(f'| {x["modelo"]} | {x["modo"]} | {100*x["retorno_liquido"]:.2f}% | {100*x["drawdown_mark_close"]:.2f}% | {x["operacoes"]:.1f} | {x["funding_liquido"]:.2f} |')
    texto+=['','## Variação entre blocos e seeds','','| Bloco | Astra comprada | Astra bilateral | Crua comprada | Crua bilateral |','|---|---:|---:|---:|---:|']
    for b in ['B1','B2','B3','B4']:
        valores=[]
        for v,m in [('astra','comprada'),('astra','bilateral'),('crua','comprada'),('crua','bilateral')]:
            x=next(x for x in r['medias_por_bloco'] if x['bloco']==b and x['modelo']==v and x['modo']==m and x['politica']=='sinal24' and x['cenario']=='base');valores.append(f'{100*x["retorno_liquido"]:.2f}%')
        texto.append('| '+b+' | '+' | '.join(valores)+' |')
    for v,x in contrastes.items():
        texto+=['',f'{v}: permitir shorts alterou a média em **{x["delta_medio_pp"]:+.2f} pontos percentuais**; melhorou {x["pares_bloco_seed_bilateral_melhor"]}/32 pares bloco/seed e {x["seeds_com_bilateral_melhor"]}/8 médias por seed. As médias bilaterais por seed vão de {100*x["bilateral_media_retornos_por_seed_min"]:.2f}% a {100*x["bilateral_media_retornos_por_seed_max"]:.2f}%; desvio-padrão dessas oito médias {100*x["bilateral_dp_medias_seeds"]:.2f}p.p. Isso é dispersão descritiva, não intervalo de confiança.']
    texto+=['','## Custos e política secundária','','O filtro usa limiar fixo aproximadamente0,20%, determinado pelo custo base, em todos os cenários. Não escolhemos o cenário com maior lucro. Ideal elimina comissão/slippage, mas mantém funding.','','| Receita | Política | Modalidade | Ideal | Base | Agravado |','|---|---|---|---:|---:|---:|']
    for v,pol,modo in [(v,pol,modo) for v in ['astra','crua'] for pol in ['sinal24','filtrada24'] for modo in ['comprada','bilateral']]:
        valores=[]
        for c in ['ideal','base','agravado']:
            x=next(x for x in r['medias_globais'] if x['modelo']==v and x['politica']==pol and x['modo']==modo and x['cenario']==c);valores.append(f'{100*x["retorno_liquido"]:.2f}%')
        texto.append('| '+v+' | '+pol+' | '+modo+' | '+' | '.join(valores)+' |')
    texto+=['','## Referências e limites','','| Referência diária, cenário base | Retorno médio | Drawdown médio |','|---|---:|---:|']
    for x in r['medias_globais']:
        if x['modelo'] in ['sempre_comprado','sempre_vendido','caixa'] and x['cenario']=='base':texto.append(f'| {x["modelo"]} | {100*x["retorno_liquido"]:.2f}% | {100*x["drawdown_mark_close"]:.2f}% |')
    texto+=['','Sempre comprado/vendido fecha e reabre diariamente, com mesmo dimensionamento; não é buy-and-hold puro. Caixa reproduz a ação do Naive de retorno zero. Previsões inalteradas: métricas MSE/MAE do estudo anterior continuam iguais.','',
        'Esta camada mede a combinação de sinal, política e mercado. Retorno positivo não comprova previsão superior nem lucro futuro; retorno negativo também é resultado válido. Não há teste confirmatório de significância. Mesmos períodos já consultados, sem novo holdout. Sinais treinados emSpot são transferidos a perpétuos, sujeitos à diferença entre mercados.','',
        'Exposição alvo95% do patrimônio conhecido e limite1× na abertura; quantidade fixa pode elevar a alavancagem efetiva com perdas. Buffer prudencial2% bloqueia trajetórias fora do escopo; não é liquidação oficial da Binance. Preços de minuto, custos fixos e filtros de pesquisa não reconstituem livro de ofertas, tiers históricos, conta VIP ou ADL. Nenhuma ordem real foi enviada.','',
        f'Conferência independente: [{destino.name}](../{destino.relative_to(RAIZ).as_posix()}/conferencia.json). Artefatos, operações, funding e curvas em `{ptr["pasta"]}/carteiras/`; publicações anteriores preservadas.']
    relatorio='\n'.join(texto)+'\n';(destino/'relatorio.md').write_text(relatorio,encoding='utf-8')
    (RAIZ/'docs/resultados_futuros.md').write_text(relatorio,encoding='utf-8')
    salvar_json(destino/'manifesto.json',{'arquivos':{x.name:sha256(x) for x in destino.iterdir() if x.is_file()},'fonte_analise_sha256':sha256(Path(__file__))})
    print(recibo)

if __name__=='__main__':analisar()
