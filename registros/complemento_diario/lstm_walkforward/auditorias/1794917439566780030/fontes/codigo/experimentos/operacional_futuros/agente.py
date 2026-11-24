"""Proponente Astra isolado; não é executor nem recebe avaliação retrospectiva final."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from infraestrutura.artefatos import salvar_json,identidade
from .receitas import proposta,propor


def consultar(pasta,receitas,historico,qualificacao=False,limite_segundos=900):
    if any(v.get('fase') not in ('exploracao','reforco') or any(b not in ['D1','D2','D3'] for b in v.get('recortes',[])) for v in historico):
        raise ValueError('Proponente não pode receber dados finais.')
    # Projeção positiva: nunca enviar trajetórias, checkpoints, arquivos ou bloco B.
    permitidos={'id','fase','recortes','elegivel','motivos','medias','score_calmar','stress2x','por_lado','seeds'}
    if any(set(v)-permitidos for v in historico): raise ValueError('Campos de contexto não autorizados.')
    pasta=Path(pasta);pasta.mkdir(parents=True,exist_ok=False)
    schema={'type':'object','properties':{'acao':{'type':'string','enum':['propor','encerrar']},
        'pai':{'type':'string'},'campo':{'type':'string'},'valor_json':{'type':'string'},
        'hipotese':{'type':'string'},'risco':{'type':'string'}},
        'required':['acao','pai','campo','valor_json','hipotese','risco'],'additionalProperties':False}
    salvar_json(pasta/'esquema.json',schema)
    contexto={'receitas':receitas,'historico':historico,'espaco':proposta()['espaco_receitas'],
              'qualificacao':qualificacao}
    instrucao='''Você é Astra, proponente de uma busca limitada, sem ferramentas, arquivos ou acesso ao teste final.
Proponha exatamente UM fator diferente de um pai conhecido, sem duplicar receita, ou encerre.
Não mude família do alvo. R0 terminal24h usa Huber; P0 dois payoffs líquidos compra/venda usa MSE.
OHLCV futuro BTCUSDT1h, comum336h, T treina/escalas,V checkpoint,C política,S comparação em2023.
Cada um de D1/D2/D3 tem seu C anterior a S. Dados e custos não são modificáveis.
R0 crua168h estado16 lr.0002; P0 mesma rede, cabeça2 e alvo operacional com barreiras.
Bases relativa/log_niveis padronizadas sóT, crua não; extras sempre padronizadosT.
Campos são literalmente os fornecidos. Barreiras só podem mudar em payoff e exigem retreino.
Critério mediana Calmar(CAGR/MDD do mesmo período), crescimento e estabilidade, não MSE.
Política uma por receita/recorte escolhida conjunta seeds emC entre12 combinações: limiar0/10/20bps,
risco0.5/1% do patrimônio, cadência1/4h. Nocional<=95%, stopvol168h piso0.5%, hold<=24h.
Gates S: >=20 trades cada carteira, sem insolvência/saída prudencial, crescimento médio positivo
base e2xslippage, dois de três recortes positivos, Calmar mediano positivo. Reforço>=6/8seeds positivas.
Fees5bps/lado, slip5bps/lado base, funding histórico; custos não são fatores de busca.
O risco de drawdown importa; picos de patrimônio não provam lucro sustentável. Sem garantia de vitória.
Exploração três seeds42/17/2026, até6 propostas novas; reforço oito seeds. Períodos retrospectivos.
Valor_json deve conter só um literal JSON válido. Explique hipótese falsificável e risco.
Se qualificação=true, apenas uma proposta técnica válida sem consultar resultado; não será treinada.
'''
    prompt=instrucao+'\n'+json.dumps(contexto,ensure_ascii=False,allow_nan=False)
    (pasta/'prompt.txt').write_text(prompt,encoding='utf-8')
    salvar_json(pasta/'contexto_permitido.json',{'contexto':contexto,'sha256_logico':identidade(contexto)})
    codex=shutil.which('codex.cmd');node=shutil.which('node.exe')
    if not codex or not node: raise RuntimeError('Codex autenticado Windows obrigatório; não usar API paga.')
    js=Path(codex).parent/'node_modules/@openai/codex/bin/codex.js'
    area=Path(tempfile.mkdtemp(prefix='cc_operacional_proponente_'))
    cmd=[node,str(js),'exec','--ignore-user-config','--ephemeral','--skip-git-repo-check','-C',str(area),
        '-m','gpt-6-astra','-s','read-only','--json','--output-schema',str((pasta/'esquema.json').resolve()),
        '-o',str((pasta/'resposta.json').resolve()),'-c','approval_policy="never"',
        '-c','model_reasoning_effort="max"','-c','web_search="disabled"','-c','project_doc_max_bytes=0',
        '-c','suppress_unstable_features_warning=true']
    for f in ['shell_tool','unified_exec','apps','plugins','multi_agent','code_mode_host','browser_use',
              'browser_use_external','computer_use','image_generation','view_image','memories','hooks',
              'shell_snapshot','skill_search']:
        cmd+=['-c',f'features.{f}=false']
    cmd+=['-c','features.skip_host_skill_discovery=true','-']
    env=os.environ.copy()
    for k in ['OPENAI_API_KEY','CODEX_API_KEY']: env.pop(k,None)
    salvar_json(pasta/'invocacao.json',{'modelo':'gpt-6-astra','comando':cmd,'isolamento':str(area),
        'api_paga':False,'autenticacao':'Codex ChatGPT','limite_segundos':limite_segundos})
    with (pasta/'eventos.jsonl').open('w',encoding='utf-8') as out,(pasta/'stderr.log').open('w',encoding='utf-8') as err:
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=out,stderr=err,env=env,text=True,
            encoding='utf-8',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        try: proc.communicate(prompt,timeout=limite_segundos)
        except subprocess.TimeoutExpired:
            subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],capture_output=True)
            raise TimeoutError('Proponente excedeu limite; sem repetição automática.')
    if proc.returncode: raise RuntimeError('Falha/cota do proponente; não substituir modelo.')
    for linha in (pasta/'eventos.jsonl').read_text(encoding='utf-8').splitlines():
        e=json.loads(linha)
        if e.get('type') in ['turn.failed','error']: raise RuntimeError('Erro do proponente.')
        if e.get('type') in ['item.started','item.completed']:
            item=e['item'];tipo=item['type']
            if tipo not in ['agent_message','reasoning','error']: raise RuntimeError('Ferramenta inesperada no proponente.')
            if tipo=='error' and 'Code Mode is unavailable' not in item.get('message',''): raise RuntimeError('Erro no proponente.')
    r=json.loads((pasta/'resposta.json').read_text(encoding='utf-8'))
    if r['acao']=='propor':
        receita=propor(r['pai'],r['campo'],json.loads(r['valor_json']),receitas)
        salvar_json(pasta/'receita_validada.json',receita)
    return r
