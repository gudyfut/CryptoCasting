"""Após seis conclusões, confere59séries e publica interpretação sem novo ajuste."""
import shutil
import traceback
from uuid import uuid4
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,agora,ler_json,salvar_json,sha256,conferir_arquivos
from treinamento.preservacao import conferir
from avaliacao.publicacao import conferir_previsoes,contraste_temporal
from .publicacao import metricas_preco


def posprocessar():
    from .ciclo import REGISTROS,SEEDS,conferir_conclusao
    ptr=ler_json(REGISTROS/'execucao.json');base=RAIZ/ptr['pasta']
    if ler_json(base/'progresso.json')['status']!='concluido' or ler_json(base/'processo.json')['ativo']:raise ValueError('Treinamento ainda não encerrado.')
    if (REGISTROS/'fechamento.json').exists():raise ValueError('Fechamento já existe; preservar.')
    try:
        auditoria=conferir_conclusao();pp=ler_json(base/'publicacao.json');pub=base/pp['pasta'];r=ler_json(pub/'resultados.json');f=ler_json(base/'congelamento.json');c=f['contrato']['configuracao']
        partes={b:pd.read_parquet(RAIZ/c['entradas_pasta']/f'{b}.parquet') for b in ('validacao','teste','operacional')};prev={};conferencias={}
        for k,item in r['por_ajuste'].items():
            t=RAIZ/item['tentativa_origem'];conferir(t);conferencias[k]={}
            for b in partes:
                q=pd.read_parquet(t/f'previsoes_{b}.parquet');conferencias[k][b]=conferir_previsoes(q,partes[b],item['metricas'].get(b));prev[k,b]=q
                if b!='operacional' and metricas_preco(q)!=item['metricas_preco'][b]:raise ValueError('Métrica de preço divergente.')
        for b in ('validacao','teste'):
            a=np.mean([(prev[f'cryptomamba_{s}',b].previsao-prev[f'cryptomamba_{s}',b].alvo).to_numpy()**2 for s in SEEDS],axis=0)
            z=np.mean([(prev[f'estado16_{s}',b].previsao-prev[f'estado16_{s}',b].alvo).to_numpy()**2 for s in SEEDS],axis=0)
            if contraste_temporal(partes[b].origem_utc,a,z,c['bootstrap'])!=r['contrastes'][b]['cryptomamba_seis_menos_estado16_taxa0002']:raise ValueError('Contraste primário divergente.')
        antes=ler_json(REGISTROS/'preservacao_antes.json');conferir_arquivos(RAIZ,antes['arquivos'])
        d=REGISTROS/'analises'/uuid4().hex;d.mkdir(parents=True);salvar_json(d/'comparacao.json',{'utc':agora(),'execucao':ptr['id'],'medias':r['medias'],'contrastes':r['contrastes'],'criterio_primario':r['criterio_primario'],'publicacao':pub.relative_to(RAIZ).as_posix(),'conferencia_metricas':conferencias,'natureza':'análise posterior sem treino; adaptação de abordagem, não reprodução literal'})
        shutil.copy2(__file__,d/'verificador.py');salvar_json(d/'manifesto.json',{'arquivos':{p.name:sha256(p) for p in d.iterdir() if p.is_file()}})
        comp={'arquivo':(d/'comparacao.json').relative_to(RAIZ).as_posix(),'sha256':sha256(d/'comparacao.json')};salvar_json(REGISTROS/'comparacao_atual.json',comp);relatorio=relatar(r,ptr,auditoria,comp)
        fim={'situacao':'concluido_conferido','utc':agora(),'execucao':ptr,'novos':6,'herdados':53,'auditoria':auditoria,'comparacao':comp,'relatorio':relatorio,'preservados':len(antes['arquivos']),'proxima_acao':'Revisar interpretação; nenhuma promoção ou novo treinamento automático.'}
        cat=ler_json(RAIZ/'registros/catalogo_estudos.json')
        for row in cat.get('rodadas_ohlcv',[]):
            if row.get('execucao')==ptr['id']:row.update(situacao='concluido_conferido',ajustes_neurais_novos_concluidos=6,publicacao=pub.relative_to(RAIZ).as_posix(),conferencia=auditoria['arquivo'],relatorio=relatorio)
        cat['etapa_atual']['situacao']='cryptomamba_adaptado_concluido_conferido';cat['etapa_atual']['cryptomamba']=fim;salvar_json(RAIZ/'registros/catalogo_estudos.json',cat)
        doc=RAIZ/'docs/andamento.md';s=doc.read_text(encoding='utf-8-sig');nota=f'## CryptoMamba adaptado concluído e conferido\n\nExecução `{ptr["id"]}`:6novos ajustes e53referências herdadas; métricas de retorno/preço,contraste primário,pesos e preservação conferidos. [Resultados e análise](resultados_cryptomamba_adaptado.md), [recibos](../registros/cryptomamba/estado.json). Arquitetura/receita foram adaptadas conforme protocolo; não é reprodução literal do artigo.2024/2025retrospectivos; sem nova promoção automática.\n\n';doc.write_text(s.replace('# Andamento do CryptoCasting\n','# Andamento do CryptoCasting\n\n'+nota,1),encoding='utf-8')
        salvar_json(REGISTROS/'estado.json',fim);salvar_json(REGISTROS/'fechamento.json',fim);return fim
    except BaseException:
        salvar_json(REGISTROS/'incidentes'/f'{uuid4().hex}.json',{'utc':agora(),'fase':'posprocessamento_sem_treino','execucao':ptr,'erro':traceback.format_exc()});raise


def relatar(r,ptr,auditoria,comp):
    def num(x,n=9):return f'{x:.{n}f}'.replace('.',',')
    def pct(x):return f'{100*x:+.3f}%'.replace('.',',')
    linhas=['# CryptoMamba adaptado ao nosso contrato: comparação e análise','',f'Execução `{ptr["id"]}`:6novos ajustes nas seis seeds usuais e53referências herdadas. [Protocolo/diferenças](protocolo_cryptomamba_adaptado.md), [decisão](adr/0014-cryptomamba-adaptado.md). Código público fixado emfef42727861a9c3a32241283ab981ef21a49e291. Esta é adaptação de uma abordagem composta, não réplica das métricas do artigo.',
        '', '## Fidelidade e diferenças','', 'Preservados núcleo de3C-Blocks×4CMBlocks, d_state64, larguras14→16→32→1, residual/pré-LN,merge de canais,Adam0,01,batch32 eRMSE. O Mamba percorre canais; não é o mesmo eixo temporal do nosso Mamba. Adaptados: projeção168→14,cinco canais OHLCV publicados sem timestamp extra, saída log-retorno24h,scalers de treino,max100/paciência10,StepLR10/0,5,clipping1,isenções oficiais de decay eepsilonRMSE1e−8.139.317parâmetros versus20.257na referência. As mudanças não isolam causa por hiperparâmetro.',
        '', 'O original prevê fechamento diário em dólares em2018–2024; nossa candidata prevê retorno24h com168candles horários em2021–2025. O14da projeção é dimensão latente, não contexto14dias. O paper descreve early stopping, mas o script público consultado não o configura. NormalizeFalse é a configuração pública: a rotina opcional de escala global não foi usada como evidência de vazamento nos resultados do artigo. Políticas públicas não debitam custos explicitamente; a comparação usa SpotR0 com custos para todos.',
        '', '## Métricas de retorno: médias por seed','', 'Comparação principal usa seis seeds iguais, média aritmética das métricas, não ensemble. LSTM só tem três seeds e recebe pareamento próprio.','', '| Parte | Modelo | Seeds | MSE ↓ | MAE×100 ↓ | RMSE×100 ↓ | Habilidade Naive |','|---|---|---:|---:|---:|---:|---:|']
    ordem=['cryptomamba_seis','estado16_taxa0002','estado8_taxa0002','estado32_taxa0002','estado64_taxa0002','estado8_taxa0001','estado16_taxa0001','estado32_taxa0001','estado64_taxa0001','naive','arima','lstm_tres']
    for b in ('validacao','teste'):
        for nome in ordem:
            g=r['medias'][b][nome];m=g['metricas'];linhas.append(f'| {b} | {nome} | {g["n_seeds"]} | {num(m["mse"])} | {num(m["mae"]*100,4)} | {num(m["rmse"]*100,4)} | {pct(m["habilidade_mse"])} |')
    linhas+=['','## Métricas no preço: mesma população para todos','','Preço previsto=C_atual×exp(log-retorno). MAPE usa preço positivo no denominador; não MAPE de retornos. RMSE/MAE emUSDT não são comparáveis diretamente a1598,1/1120,7USD do artigo, por diferenças de datas,tarefa,fonte e formulação.','', '| Parte | Modelo | RMSE preço ↓ | MAE preço ↓ | MAPE preço (%) ↓ |','|---|---|---:|---:|---:|']
    for b in ('validacao','teste'):
        for nome in ('cryptomamba_seis','estado16_taxa0002','naive','arima','lstm_tres'):
            p=r['medias'][b][nome]['metricas_preco'];linhas.append(f'| {b} | {nome} | {num(p["rmse_usdt"],2)} | {num(p["mae_usdt"],2)} | {num(p["mape_percentual"],3)} |')
    linhas+=['','## Incerteza e critério anterior ao treinamento','', '| Parte | Contraste | Diferença de MSE | IC95%14dias |','|---|---|---:|---|']
    for b in ('validacao','teste'):
        for nome,c in r['contrastes'][b].items():
            a,z=c['ic95']['14'];linhas.append(f'| {b} | {nome} | {c["diferenca_mse_a_menos_b"]:.9g} | [{a:.9g};{z:.9g}] |')
    crit=r['criterio_primario'];favoravel=crit['media_mse_menor'] and crit['ic95_principal_inteiramente_favoravel']
    linhas+=['', 'Critério primário '+('atendido: menor MSE médio de validação e IC95%principal inteiramente favorável.' if favoravel else 'não atendido: este procedimento não fornece evidência suficiente para substituir a referência16/0,0002.'),
        '', 'A avaliação é retrospectiva, condicional aos modelos; não corrige toda seleção histórica. Resultado favorável não prova reprodução do artigo ou lucro; resultado negativo vale para esta adaptação. Nenhuma receita é promovida automaticamente.',
        '', '## Spot com mesma política e custos','','| Modelo | Bruto | Líquido base | Agravado | Drawdown base | Operações médias |','|---|---:|---:|---:|---:|---:|']
    for nome in ordem:
        op=r['medias']['teste'][nome]['spot'];b=op['base'];linhas.append(f'| {nome} | {pct(op["bruto_mesmos_sinais"]["retorno_liquido"])} | {pct(b["retorno_liquido"])} | {pct(op["agravado"]["retorno_liquido"])} | {pct(b["drawdown"])} | {num(b["entradas_planejadas"],1)} |')
    linhas+=['','Retornos/drawdowns são médias individuais, não carteira combinada. Receita mantém decisão00UTC,latência1min,saída24h,taxa0,10%/slippage0,05% por lado e cenários; sem política nova/short/futuros. Não escolher uma seed favorável.',
        '', '## Seeds candidatas','','| Seed | MSE validação | MSE teste | Retorno líquido |','|---|---:|---:|---:|']
    for s in (17,42,2026,7,123,31415):
        d=r['por_ajuste'][f'cryptomamba_{s}'];linhas.append(f'| {s} | {num(d["metricas"]["validacao"]["mse"])} | {num(d["metricas"]["teste"]["mse"])} | {pct(d["spot"]["base"]["retorno_liquido"])} |')
    linhas+=['','## Evidências e limites','',f'[Auditoria](../{auditoria["arquivo"]}), [comparação posterior](../{comp["arquivo"]}), [estado](../registros/cryptomamba/estado.json). Fontes próprias/externas/configurações,contratos,checkpoints,seleção e recarga foram preservados e conferidos. Sem nova inferência/treino no pós-processamento. Qualificação sintética inclui equivalência do núcleo em tensor/pesos iguais, não reprodução de treinamento/artigo. Sem repetição real extra; seis ajustes de uma candidata, sem busca.2024/2025já conhecidos; divisão fixa, não walk-forward ou holdout novo. Custos/fills reais da Binance e backup externo não foram certificados.']
    texto='\n'.join(linhas)+'\n';dest=RAIZ/'docs/resultados_cryptomamba_adaptado.md'
    if dest.exists():
        if dest.read_text(encoding='utf-8-sig')!=texto:raise FileExistsError('Relatório diferente já existe; preservar e revisar.')
    else:dest.write_text(texto,encoding='utf-8')
    return dest.relative_to(RAIZ).as_posix()
