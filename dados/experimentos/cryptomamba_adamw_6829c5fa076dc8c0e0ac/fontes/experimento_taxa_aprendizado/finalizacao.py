"""Pós-processamento de leitura após24ajustes; não inicia/repete treinamento."""
import shutil
import traceback
from uuid import uuid4
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,agora,ler_json,salvar_json,sha256,conferir_arquivos
from treinamento.preservacao import conferir
from avaliacao.publicacao import conferir_previsoes
from .publicacao import contraste,resumo_grupo


def posprocessar():
    from .ciclo import REGISTROS,ESTADOS,SEEDS,conferir_conclusao
    rp=ler_json(REGISTROS/'execucao.json');p=RAIZ/rp['pasta']
    if ler_json(p/'progresso.json')['status']!='concluido' or ler_json(p/'processo.json')['ativo']:raise ValueError('Treinamento ainda não encerrado.')
    if (REGISTROS/'fechamento.json').exists():raise ValueError('Pós-processamento já encerrado; usar leitura, sem sobrescrever recibos.')
    try:
        auditoria=conferir_conclusao()
        pubinfo=ler_json(p/'publicacao.json');pub=p/pubinfo['pasta'];r=ler_json(pub/'resultados.json');f=ler_json(p/'congelamento.json');cfg=f['contrato']['configuracoes']['8']
        partes={b:pd.read_parquet(RAIZ/cfg['entradas_pasta']/f'{b}.parquet') for b in ('validacao','teste','operacional')}
        prev={};tentativas={}
        for k,d in r['por_ajuste'].items():
            t=RAIZ/d['tentativa_origem'];conferir(t);rr=ler_json(t/'resultado.json');assert rr['metricas']==d['metricas']
            for b in partes:
                q=pd.read_parquet(t/f'previsoes_{b}.parquet');conferir_previsoes(q,partes[b],rr['metricas'].get(b));prev[k,b]=q
            tentativas[k]={'pasta':d['tentativa_origem'],'conclusao_sha256':sha256(t/'conclusao.json')}
        for b in ('validacao','teste'):
            for n in ESTADOS:
                ks=[f'taxa0001_estado{n}_{s}' for s in SEEDS];refs=[f'estado{n}_{s}' for s in SEEDS]
                for nome,chaves in [('candidata',ks),('referencia',refs)]:
                    recalculado=resumo_grupo(chaves,r['por_ajuste'],prev,b)
                    if recalculado!=r['medias'][b][f'{nome}_estado{n}']:raise ValueError('Média divergente.')
                a=np.mean([(prev[k,b].previsao-prev[k,b].alvo).to_numpy()**2 for k in ks],axis=0);z=np.mean([(prev[k,b].previsao-prev[k,b].alvo).to_numpy()**2 for k in refs],axis=0)
                refeito=contraste(partes[b].origem_utc,a,z,cfg['bootstrap']);publicado=r['contrastes'][b][str(n)]
                for campo,v in refeito.items():
                    if v!=publicado[campo]:raise ValueError('Contraste divergente.')
        antes=ler_json(REGISTROS/'preservacao_antes.json');conferir_arquivos(RAIZ,antes['arquivos'])
        d=REGISTROS/'analises'/uuid4().hex;d.mkdir(parents=True)
        salvar_json(d/'comparacao.json',{'utc':agora(),'execucao':rp['id'],'publicacao':pub.relative_to(RAIZ).as_posix(),'manifesto_sha256':pubinfo['manifesto_sha256'],'medias':r['medias'],'contrastes':r['contrastes'],'criterio_validacao':r['criterio_validacao'],'tentativas':tentativas,'metodo_medias':r['metodo_medias'],'natureza':'conferência posterior de métricas e contrastes; nenhum ajuste novo'})
        shutil.copy2(__file__,d/'verificador.py');salvar_json(d/'manifesto.json',{'arquivos':{q.name:sha256(q) for q in d.iterdir() if q.is_file()}})
        comparacao={'arquivo':(d/'comparacao.json').relative_to(RAIZ).as_posix(),'sha256':sha256(d/'comparacao.json')};salvar_json(REGISTROS/'comparacao_atual.json',comparacao)
        relatorio=relatar(r,rp,auditoria,comparacao)
        fechado={'situacao':'concluido_conferido','utc':agora(),'execucao':rp,'novos':24,'herdados':29,'auditoria':auditoria,'comparacao':comparacao,'relatorio':relatorio,'preservados':len(antes['arquivos']),'proxima_acao':'Sem promoção automática ou novos treinamentos autorizados.'}
        cat=ler_json(RAIZ/'registros/catalogo_estudos.json')
        for rodada in cat.get('rodadas_ohlcv',[]):
            if rodada.get('execucao')==rp['id']:rodada.update(situacao='concluido_conferido',ajustes_neurais_novos_concluidos=24,publicacao=pub.relative_to(RAIZ).as_posix(),conferencia=auditoria['arquivo'],relatorio=relatorio)
        cat['etapa_atual']['situacao']='taxa_quatro_estados_concluida_conferida';cat['etapa_atual']['taxa_aprendizado']=fechado;salvar_json(RAIZ/'registros/catalogo_estudos.json',cat)
        a=RAIZ/'docs/andamento.md';texto=a.read_text(encoding='utf-8-sig');nota=f'## Taxa0,0001 nos quatro estados concluída e conferida\n\nGrade `{rp["id"]}` encerrada com24ajustes novos e29herdados; fontes/checkpoints/métricas/contrastes/preservação conferidos. [Relatório](resultados_taxa_aprendizado.md), [estado e recibos](../registros/taxa_aprendizado/estado.json). Mesmas seis seeds por estado; efeitos de taxa medidos dentro de cada arquitetura. Sem promoção automática, alteração Spot ou nova busca.2024/2025 permanecem retrospectivos.\n\n'
        a.write_text(texto.replace('# Andamento do CryptoCasting\n','# Andamento do CryptoCasting\n\n'+nota,1),encoding='utf-8')
        salvar_json(REGISTROS/'estado.json',fechado);salvar_json(REGISTROS/'fechamento.json',fechado)
        return fechado
    except BaseException:
        salvar_json(REGISTROS/'incidentes'/f'{uuid4().hex}.json',{'utc':agora(),'fase':'posprocessamento_sem_treino','execucao':rp,'erro':traceback.format_exc(),'acao':'Preservar treino concluído; não repetir executor para corrigir apresentação/conferência.'});raise


def relatar(r,rp,auditoria,comparacao):
    def num(v,n=9):return f'{v:.{n}f}'.replace('.',',')
    def pct(v):return f'{v*100:+.3f}%'.replace('.',',')
    linhas=['# Taxa de aprendizado:0,0002 versus0,0001 nos quatro estados','',f'Execução `{rp["id"]}`,24novos ajustes e29heranças. Estados8/16/32/64, mesmas seis seeds17/42/2026/7/123/31415. Dados/receita/política iguais dentro de cada par, alterando somente a taxa base. O [protocolo](protocolo_taxa_aprendizado.md) foi congelado antes do primeiro ajuste. A investigação anterior dos estados permanece [separada](resultados_estados32_64.md).','', '## Previsão: médias aritméticas de seis seeds','','RMSE é a média dos RMSE individuais. Não ensemble/carteira. Habilidade negativa significa MSE maior que Naive.']
    for b in ('validacao','teste'):
        linhas+=['',f'### {b}','','| Estado | Taxa | MSE ↓ | MAE×100 ↓ | RMSE×100 ↓ | Habilidade Naive | MSE00UTC ↓ |','|---|---|---:|---:|---:|---:|---:|']
        for n in (8,16,32,64):
            for nome,taxa in [('referencia','0,0002'),('candidata','0,0001')]:
                m=r['medias'][b][f'{nome}_estado{n}']['metricas'];d=m['origens00utc'];linhas.append(f'| {n} | {taxa} | {num(m["mse"])} | {num(m["mae"]*100,4)} | {num(m["rmse"]*100,4)} | {pct(m["habilidade_mse"])} | {num(d["mse"]) if d else "indisponível"} |')
    linhas+=['','## Efeito da taxa e incerteza','','Diferença=candidata0,0001−referência0,0002. Negativo favorece a redução. Quatro efeitos de validação formam a família primária; IC98,75% por Bonferroni mantém erro familiar nominal5%, sem corrigir toda seleção histórica/checkpoints. Teste é secundário retrospectivo, não escolhe taxa/seed.','', '| Parte | Estado | Variação MSE | IC95%14dias | IC98,75%14dias |','|---|---|---:|---|---|']
    for b in ('validacao','teste'):
        for n,c in r['contrastes'][b].items():
            a,z=c['ic95']['14'];x,y=c['ic9875_bonferroni_quatro']['14'];linhas.append(f'| {b} | {n} | {num(c["variacao_mse_percentual"],3)}% | [{a:.8g};{z:.8g}] | [{x:.8g};{y:.8g}] |')
    linhas+=['','Critério previamente definido de evidência favorável em validação (média menor e IC98,75%14dias inteiramente negativo):']
    for n,c in r['criterio_validacao'].items():linhas+=['',f'- Estado{n}: '+('atendido.' if c['evidencia_favoravel_procedimento'] else 'não atendido; não há evidência suficiente nesse procedimento para substituir a referência.')]
    linhas+=['','Esse resultado não promove automaticamente outra taxa/estado. Não interpretar inconclusão como igualdade ou IC exploratório como confirmação independente.','', '## Spot: resultados individuais médios','','Mesma política R0 e sinais definidos antes do teste; custos base0,10%/slippage0,05% por lado. Bruto preserva os sinais. Drawdown médio não é risco de carteira média.','', '| Estado | Taxa | Bruto | Líquido base | Agravado | Drawdown base | Operações médias |','|---|---|---:|---:|---:|---:|---:|']
    for n in (8,16,32,64):
        for nome,taxa in [('referencia','0,0002'),('candidata','0,0001')]:
            op=r['medias']['teste'][f'{nome}_estado{n}']['spot'];b=op['base'];linhas.append(f'| {n} | {taxa} | {pct(op["bruto_mesmos_sinais"]["retorno_liquido"])} | {pct(b["retorno_liquido"])} | {pct(op["agravado"]["retorno_liquido"])} | {pct(b["drawdown"])} | {num(b["entradas_planejadas"],1)} |')
    linhas+=['','## Seeds individuais','','| Estado | Seed | MSE teste0,0002 | MSE teste0,0001 | MSE validação0,0002 | MSE validação0,0001 |','|---|---|---:|---:|---:|---:|']
    for n in (8,16,32,64):
        for s in (17,42,2026,7,123,31415):
            a=r['por_ajuste'][f'estado{n}_{s}']['metricas'];b=r['por_ajuste'][f'taxa0001_estado{n}_{s}']['metricas'];linhas.append(f'| {n} | {s} | {num(a["teste"]["mse"])} | {num(b["teste"]["mse"])} | {num(a["validacao"]["mse"])} | {num(b["validacao"]["mse"])} |')
    linhas+=['','## Evidências e limites','',f'[Conferência](../{auditoria["arquivo"]}), [comparação posterior](../{comparacao["arquivo"]}), [estado](../registros/taxa_aprendizado/estado.json) e [catálogo](../registros/catalogo_estudos.json). As publicações53resultados identificam cada tentativa e se ela foi nova/herdada. Fontes,checkpoint,seleção por validação,recarga exata e métricas foram preservados e conferidos. O pós-processamento não treinou modelos; referências/qualificações não são novos ajustes de mercado.',
        '', 'Mamba oficial/CUDA, mesmas entradas/escalas/origens e divisão fixa;2024/2025 já consultados. Não é walk-forward nem novo holdout. Repetição sintética e recarga exata não substituem repetição completa de mercado, excluída do orçamento24. Reduzir taxa afeta a trajetória e o decay efetivo AdamW; não é prova isolada de mecanismo causal. MSE não garante lucro; simulação não certifica execução Binance/ordens/livro. Sem backup externo comprovado.']
    destino=RAIZ/'docs/resultados_taxa_aprendizado.md'
    texto='\n'.join(linhas)+'\n'
    if destino.exists():
        if destino.read_text(encoding='utf-8-sig')!=texto:raise FileExistsError('Relatório diferente já existe; preservar e revisar sem sobrescrever.')
    else:destino.write_text(texto,encoding='utf-8')
    return destino.relative_to(RAIZ).as_posix()
