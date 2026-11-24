"""Astra via assinatura ChatGPT; somente JSON, sem acesso ao repositorio/teste."""
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from infraestrutura.artefatos import salvar_json
from .contrato import ESPACO, REFERENCIA, esquema, validar_receita

def validar_contexto(contexto):
    if isinstance(contexto,dict):
        for k,v in contexto.items():
            if k in ['teste','carteiras','publicacao','medias_globais','finalista']:
                raise ValueError('Conteudo proibido no prompt de desenvolvimento: '+k)
            validar_contexto(v)
    elif isinstance(contexto,(list,tuple)):
        for v in contexto:validar_contexto(v)

def consultar(pasta, contexto, esforco='max', versao_cli=None):
    validar_contexto(contexto)
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=False)
    schema = pasta/'esquema.json'; salvar_json(schema, esquema())
    instrucoes = '''Voce e o pesquisador Astra numa busca ADAPTATIVA experimental de Mamba-1 CUDA.
Voce nao tem ferramentas. Nao tente abrir arquivos, pesquisar, executar codigo ou consultar testes.
Recebe somente resumos de treino/validacao. Nao invente resultados. Retorne exclusivamente o JSON do esquema.
Objetivo: propor UMA candidata fundamentada no diagnostico e no historico. Pode mudar varios fatores,
mas explique o mecanismo esperado e os confundidores. Priorize uma mudanca quando ela responde a pergunta.
Nao precisa preencher todas as 12 vagas: encerre se nao houver hipotese util. Nao proponha receita repetida.
Dominio: BTC OHLCV1h, retorno log terminal24h. Sem dados externos, ordens reais ou lucro como seletor.
D1: treino2021-2022, validacao2023H1. D2: treino2021-2023H1, validacao2023H2. Purga24h.
Triagem seed42 em dois recortes; ate3melhores promovidas seeds17/2026. Todas as tentativas preservadas.
Referencia e candidatas usam as mesmas origens, indice minimo336 (aquecimento composto).
Score: media MSE/Naive nos recortes/seeds. Menor e melhor. Valores proximos de1 nao provam sinal.
Receita: relativa=ln(OHLC/Cprev),ln1p(V),zscoretreino; crua=OHLCV sem Xscaler;
niveis=OHLCV zscoretreino; log_niveis=ln(OHLC),ln1p(V),zscoretreino;
janela_relativa=ln(OHLC/Cultima_da_janela),zscore ln1pV dentroda janela, so passado conhecido.
Indicadores adicionam logret24/168,volatilidadehoraria24/168 e ln1pV menos media168, zscoretreino.
Mamba oficial dconv4 expand2 preLayerNorm residual finalLayerNorm. poolingultimo ou media.
Adam/AdamW, batch64 micro32, clipping1, max100epocas paciencia10; selecao MSEvalidacao.
Huber=2*Huber(delta1 no alvo zscoretreino). Plateau fator.5 paciencia2 minlr.000025.
ganho_saida aplica edicao fixa APOS selecionarcheckpoint: y_novo=ganho*y_antigo no logretreal.
Isso e edicao dos pesos da cabeca em copia, nao uma calibração adicional escolhida vendo teste.
Sem escolha individual por seed. Contracao pode aproximarNaive sem gerar poderpreditivo.
Analise evidencias, alternativas, custos e estabilidade. Nao prometa lucro/significancia.
O conjunto final nunca orienta sua resposta. A busca inteira e retrospectiva no contexto do TCC.
'''
    prompt = instrucoes+'\nESPACO:\n'+json.dumps(ESPACO,ensure_ascii=False)+'\nREFERENCIA:\n'+json.dumps(REFERENCIA)+'\nCONTEXTO:\n'+json.dumps(contexto,ensure_ascii=False,allow_nan=False)
    (pasta/'prompt.txt').write_text(prompt, encoding='utf-8')
    codex = shutil.which('codex.cmd')
    node = shutil.which('node.exe')
    if not codex or not node:
        raise RuntimeError('Codex autenticado local indisponivel; nao usar API paga como fallback.')
    js = Path(codex).parent/'node_modules/@openai/codex/bin/codex.js'
    if not js.is_file():
        raise FileNotFoundError(str(js))
    if versao_cli:
        assert subprocess.check_output([node,str(js),'--version'],text=True).strip()==versao_cli
    area = Path(tempfile.mkdtemp(prefix='cryptocasting_astra_sem_testes_'))
    cmd = [node,str(js),'exec','--ignore-user-config','--ephemeral','--skip-git-repo-check',
           '-C',str(area),'-m','gpt-6-astra','-s','read-only','--json',
           '--output-schema',str(schema.resolve()),'-o',str((pasta/'resposta.json').resolve()),
           '-c','approval_policy="never"','-c',f'model_reasoning_effort="{esforco}"',
           '-c','web_search="disabled"','-c','project_doc_max_bytes=0',
           '-c','suppress_unstable_features_warning=true']
    for f in ['shell_tool','unified_exec','apps','plugins','multi_agent','code_mode_host',
              'browser_use','browser_use_external','computer_use','image_generation','view_image',
              'memories','hooks','shell_snapshot','skill_search']:
        cmd += ['-c',f'features.{f}=false']
    cmd += ['-c','features.skip_host_skill_discovery=true','-']
    env = os.environ.copy()
    for k in ['OPENAI_API_KEY','CODEX_API_KEY']:
        env.pop(k,None)
    salvar_json(pasta/'invocacao.json', {'modelo':'gpt-6-astra','esforco':esforco,'comando':cmd,
        'autenticacao':'ChatGPT previamente conferida; variaveis de API removidas',
        'area_isolada':str(area),'limite_segundos':1800})
    with (pasta/'eventos.jsonl').open('w',encoding='utf-8') as saida, (pasta/'stderr.log').open('w',encoding='utf-8') as erros:
        proc = subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=saida,stderr=erros,env=env,
            text=True,encoding='utf-8',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        try:
            proc.communicate(prompt,timeout=1800)
        except subprocess.TimeoutExpired:
            subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],capture_output=True)
            raise TimeoutError('Astra excedeu30min; interrupcao preservada, sem repetir a consulta.')
    if proc.returncode:
        raise RuntimeError(f'Astra encerrou codigo{proc.returncode}; verificar stderr/cota. Sem fallback.')
    usos = []
    for linha in (pasta/'eventos.jsonl').read_text(encoding='utf-8').splitlines():
        e = json.loads(linha)
        if e.get('type') in ['item.started','item.completed']:
            tipo = e['item']['type']
            if tipo not in ['agent_message','reasoning','error']:
                raise RuntimeError(f'Ferramenta inesperada do agente: {tipo}')
            if tipo == 'error' and 'Code Mode is unavailable' not in e['item'].get('message',''):
                raise RuntimeError('Erro do agente registrado; investigar.')
        if e.get('type') in ['turn.failed','error']:
            raise RuntimeError('Falha da chamada Astra.')
        if e.get('type') == 'turn.completed':
            usos.append(e.get('usage',{}))
    assert usos, 'Ausencia de conclusao da chamada.'
    resposta = json.loads((pasta/'resposta.json').read_text(encoding='utf-8'))
    validar_receita(resposta['receita'])
    assert resposta['acao'] in ['experimentar','encerrar']
    salvar_json(pasta/'conferencia.json', {'modelo_solicitado':'gpt-6-astra','sem_ferramentas':True,
                                          'uso':usos,'sem_resultados_teste_no_prompt':True})
    return resposta
