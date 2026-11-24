"""Leitura posterior de F02: reconciliar totais/médias e publicar interpretação."""
import math
from pathlib import Path
import pandas as pd
from infraestrutura.artefatos import RAIZ,agora,ler_json,salvar_json,sha256,conferir_arquivos


def analisar():
    ptr=ler_json(RAIZ/'registros/smart_mercados/execucao.json');p=RAIZ/ptr['pasta']
    fim=ler_json(p/'fechamento.json');assert fim['situacao']=='concluido_conferido' and fim['concluidas']==1632
    pub=p/'publicacao';assert sha256(pub/'manifesto.json')==fim['publicacao_sha256']
    m=ler_json(pub/'manifesto.json');conferir_arquivos(pub,m['arquivos']);conferir_arquivos(p,m['carteiras'])
    r=ler_json(pub/'resultados.json');linhas=[]
    for item in r['carteiras']:
        d=p/'carteiras'/item['chave'];conferir_arquivos(d,ler_json(d/'manifesto.json')['arquivos'])
        o=ler_json(d/'ordens.json');ev=ler_json(d/'funding.json');diarios=ler_json(d/'diarios.json');s=ler_json(d/'resumo.json')
        caixa=s['capital_inicial'];q=0.;taxas=0.;slippage=0.;giro=0.;contagem=0
        for t in o:
            dq=t['delta_executado'];caixa-=dq*t['preco_execucao']+t['comissao'];q+=dq
            taxas+=t['comissao'];slippage+=t['slippage'];giro+=abs(dq)*t['preco_execucao'];contagem+=t['status']=='executada'
        funding=sum(-v['btc']*v['taxa']*v['mark'] for v in ev)
        caixa+=funding;final=caixa+q*o[-1]['preco_mark']
        valores={'capital_final':final,'retorno_liquido':final/s['capital_inicial']-1,'comissoes':taxas,'slippage':slippage,'funding':funding,'giro':giro/s['capital_inicial'],'ordens':contagem}
        for k,v in valores.items():
            assert math.isclose(v,s[k],abs_tol=1e-7) and math.isclose(v,item[k],abs_tol=1e-7)
        assert math.isclose(sum(x['retorno_log'] for x in diarios),math.log(final/s['capital_inicial']),abs_tol=1e-9)
        linhas.append(item)
    q=pd.DataFrame(linhas);grupos=['modelo','politica','braco','cenario']
    medias=q.groupby(['bloco']+grupos).retorno_liquido.mean().groupby(grupos).mean()
    for x in r['medias_globais']:assert math.isclose(medias.loc[tuple(x[k] for k in grupos)],x['retorno_liquido'],abs_tol=1e-12)
    destino=RAIZ/'registros/smart_mercados/conferencias'/agora().replace(':','').replace('+','_');destino.mkdir(parents=True,exist_ok=False)
    ativas=[]
    for (modelo,pol,braco),g in q[(q.seed.notna())&(q.cenario=='iguais')].groupby(['modelo','politica','braco']):
        ativas.append({'modelo':modelo,'politica':pol,'braco':braco,'carteiras_com_ordens':int((g.ordens>0).sum()),'total':len(g)})
    recibo={'utc':agora(),'status':'conferido','execucao':ptr,'carteiras':1632,'totais_reconciliados':True,'medias_recalculadas':True,'atividade':ativas,'publicacao_sha256':sha256(pub/'manifesto.json')}
    salvar_json(destino/'conferencia.json',recibo)

    def media(modelo,politica,braco,cenario='iguais'):
        return next(x for x in r['medias_globais'] if all(x[k]==v for k,v in [('modelo',modelo),('politica',politica),('braco',braco),('cenario',cenario)]))

    texto=['# Smart retida: comparação Spot/futuros e filtro — F02','',
        f'Execução `{ptr["id"]}` concluída e conferida: **1.632 carteiras, zero novos treinamentos**, 64 séries herdadas. [Método congelado](protocolo_smart_mercados.md), [decisão](adr/0025-smart-spot-futuros.md), [estado](../registros/smart_mercados/estado.json).','',
        'Quatro blocos independentes de2024–2025,727datas, oito seeds por receita. Primeiro média de seeds por bloco, depois peso igual entre os quatro blocos. Percentuais não são retorno acumulado de dois anos nem retorno anual.','',
        'A Smart ajusta parcialmente e mantém posição: não liquida diariamente. Mesma reserva5%, quantidade causal, mínimo100USDT, passo0,001BTC e cobrança equivalenteUSDT nos mercados. Essa Smart95 comum não é reprodução exata da Smart histórica; usar comparações dentro desta rodada.','',
        '## Resultado principal, custos iguais','',
        'Comissão0,05% e slippage0,05% por ajuste em ambos os mercados. Funding histórico nos braços designados.','',
        '| Receita | Política | Spot comprado | Futuro comprado sem funding | Futuro comprado com funding | Futuro bilateral com funding |',
        '|---|---|---:|---:|---:|---:|']
    for v in ['astra','crua']:
        for pol in ['smart','smart_filtrada']:
            vals=[f'{100*media(v,pol,b)["retorno_liquido"]:+.2f}%' for b in ['spot','futuro_sem_funding','futuro','futuro_bilateral']]
            texto.append('| '+v+' | '+pol+' | '+' | '.join(vals)+' |')
    texto+=['','## Diferenças pareadas','',
        'Cada diferença usa os mesmos32pares bloco/seed. Pontos percentuais positivos favorecem o primeiro termo. Contagens não equivalem a teste de significância; não foi calculado intervalo confirmatório.','',
        '| Receita | Política | Contraste | Diferença média p.p. | Pares com ganho |','|---|---|---|---:|---:|']
    for x in r['contrastes_descritivos']:
        texto.append(f'| {x["modelo"]} | {x.get("politica",x.get("braco"))} | {x["contraste"]} | {x["media_pp"]:+.2f} | {x["pares_melhores"]}/32 |')
    texto+=['','## Blocos: Smart sem filtro, custos iguais','','| Bloco | Receita | Spot | Futuro comprado | Futuro bilateral |','|---|---|---:|---:|---:|']
    for b in ['B1','B2','B3','B4']:
        for v in ['astra','crua']:
            vals=[]
            for a in ['spot','futuro','futuro_bilateral']:
                x=next(x for x in r['medias_por_bloco'] if x['bloco']==b and x['modelo']==v and x['braco']==a and x['politica']=='smart' and x['cenario']=='iguais')
                vals.append(f'{100*x["retorno_liquido"]:+.2f}%')
            texto.append('| '+b+' | '+v+' | '+' | '.join(vals)+' |')
    texto+=['','## Risco, exposição e frequência — custos iguais','','| Receita | Política | Braço | Drawdown médio | Exposição média absoluta | Ordens médias | Carteiras ativas |','|---|---|---|---:|---:|---:|---:|']
    for x in ativas:
        d=media(x['modelo'],x['politica'],x['braco'])
        texto.append(f'| {x["modelo"]} | {x["politica"]} | {x["braco"]} | {100*d["drawdown"]:.2f}% | {100*d["exposicao_media"]:.2f}% | {d["ordens"]:.1f} | {x["carteiras_com_ordens"]}/32 |')
    texto+=['','## Sensibilidade de custos e referências','','Ideal zera execução, mas preserva funding. Por mercado: Spot0,10% e futuro0,05% de comissão; slippage0,05% nos dois. Política/filtro não mudam entre cenários.','','| Receita | Política | Braço | Ideal | Custos iguais | Custos por mercado |','|---|---|---|---:|---:|---:|']
    for v in ['astra','crua','comprar_manter','caixa']:
        for pol in (['smart','smart_filtrada'] if v in ['astra','crua'] else ['smart']):
            for a in ['spot','futuro','futuro_bilateral']:
                vals=[f'{100*media(v,pol,a,c)["retorno_liquido"]:+.2f}%' for c in ['ideal','iguais','por_mercado']]
                texto.append('| '+v+' | '+pol+' | '+a+' | '+' | '.join(vals)+' |')
    texto+=['','## Como interpretar','','O filtro usa magnitude fixa≈0,30%, baseada nos custos Spot anteriores, igual em todos os mercados. Abaixo disso mantém a posição já aberta. Pode reduzir giro e prejuízos, mas também exposição a altas e velocidade de saída; não mede confiança do modelo e não garante lucro. Carteira em caixa não comprova acerto preditivo.','',
        'O braço futuro sem funding é contrafactual, não uma modalidade negociável. Sua diferença para Spot inclui preços negociados, marcação e efeito desses preços no dimensionamento. Funding também altera patrimônio e operações posteriores: a diferença entre braços não é apenas a soma dos pagamentos.','',
        'Mesmos modelos e previsões: MSE/MAE não mudaram. Resultados retrospectivos, sem novo holdout e sem promoção automática por lucro. Mais carteiras não são amostras independentes. As médias por seed/bloco e os contrastes completos estão na publicação.','',
        'Exposição controlada na abertura/aumento; perdas podem elevar exposição efetiva. Buffer prudencial2% não é fórmula integral de liquidação Binance; violação interromperia a rodada. Custos/filtros são hipóteses, sem livro de ofertas ou certificação de conta real. Sem ordens reais ou novos treinamentos.','',
        f'Auditoria posterior: [recibo](../{destino.relative_to(RAIZ).as_posix()}/conferencia.json). Dados completos em `{ptr["pasta"]}/publicacao/resultados.json`; ordens, funding, diários e curvas preservados por carteira. Ledgers/curvas volumosos locais, resumos/fontes/manifestos elegíveis ao Git. Estudos anteriores intactos.']
    relatorio='\n'.join(texto)+'\n'
    (destino/'relatorio.md').write_text(relatorio,encoding='utf-8')
    (RAIZ/'docs/resultados_smart_mercados.md').write_text(relatorio,encoding='utf-8',newline='\n')
    salvar_json(destino/'manifesto.json',{'arquivos':{x.name:sha256(x) for x in destino.iterdir() if x.is_file()},'fonte_sha256':sha256(Path(__file__))})
    print(recibo)

if __name__=='__main__':analisar()
