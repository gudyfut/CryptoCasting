"""Astra via assinatura ChatGPT; somente JSON, sem acesso ao repositorio/teste."""
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from infraestrutura.artefatos import salvar_json
from .contrato import configuracao, esquema
from infraestrutura.artefatos import identidade

def validar_contexto(c):
    assert set(c)=={'fase','recortes','receitas','historico','rejeicoes','instrucao'}
    assert c['fase'] in ['qualificacao','busca','contraste']
    assert c['recortes']==configuracao()['recortes']
    for v in c['historico']:
        assert set(v)=={'id','bloco','seed','metricas','media_constante','diario_00utc','parametros','epoca','segundos'}
        assert v['bloco'] in ['S1','S2','S3']
        assert v['seed'] in [42,17,2026]
    for k,v in c['receitas'].items():
        from .contrato import validar_receita,ancoras
        validar_receita(v,ancora=v in ancoras().values())
    # Contexto construido por projecao positiva; nao serializar resultados completos.
    assert all(set(r)=={'consulta','motivo'} for r in c['rejeicoes'])

def consultar(pasta, contexto, esforco='max', versao_cli=None, limite_segundos=1800):
    validar_contexto(contexto)
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=False)
    schema = pasta/'esquema.json'; salvar_json(schema, esquema())
    instrucoes = """Voce e Astra, proponente cientifico numa busca local de Mamba1 oficial CUDA.
Nao tem ferramentas, arquivos, memoria ou acesso ao teste. Responda somente o esquema JSON.
Proponha exatamente UM fator diferente de uma receita-pai conhecida, no espaco permitido, ou encerre.
Valor e um texto contendo JSON valido. Explique mecanismo falsificavel, metrica esperada, risco e custo.
BTC OHLCV1h, alvo log-retorno futuro24h; treino horario. Contextos24/72/168, aquecimento comum336.
T treina e ajusta escalas; V escolhe checkpoint por MSE; S pontua receita somente depois da recarga.
Triagem duas seeds42/17 nos tres recortes, melhores tres recebem2026. Comparar somente cobertura completa.
Primario Q=media MSE/Naive; menor melhor. Nao selecionar por lucro, correlacao ou seed isolada.
Portoes finais: Q<=.999*min(1,Qancoras,Qmedia_constante), supera melhor ancora em2/3recortes e6/9pares,
nenhum recorte piora5%, razao MAE/Naive media nao piora1%. Se ninguem passar, sem finalista.
Rede: preLayerNorm residual,2camadas,estado16,dconv4,expand2,AdamW.001,taxa fixa,100epocasmax,
patiencia10,batch64micro32,clip1,2Huber(delta1 no alvo padronizado somenteT),ganho1.
relativa=ln(OHLC/Cprev),ln1pV comzscoreT; log_niveis=lnOHLC,ln1pV,zscoreT;
janela_relativa=ln(OHLC/Cultima_janela),zscoreln1pVna janela; extras zscoreT.
momentum acrescenta logret24/168; volatilidade stdhoraria24/168; volume_relativo ln1pV-media168.
Extras podem ter historia maior que contexto. Crua e exclusiva da ancora fixa, nao candidata mutavel.
N01-N04 ja predefinidas: momentum,volatilidade,volume_relativo,poolingmedia sobre A0.
Nas duas vagas de contraste priorize remover UM fator de combinacao promissora; nao repetir receitas.
Nao editar pesos/ganho/custos/avaliador. Nao garantir melhora. Todos periodos sao retrospectivos.
"""
    prompt=instrucoes+'\nESPACO:\n'+json.dumps(configuracao()['espaco'])+'\nCONTEXTO:\n'+json.dumps(contexto,ensure_ascii=False,allow_nan=False)
    salvar_json(pasta/'contexto_permitido.json',{'contexto':contexto,'sha256_logico':identidade(contexto)})
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
        'area_isolada':str(area),'limite_segundos':limite_segundos})
    with (pasta/'eventos.jsonl').open('w',encoding='utf-8') as saida, (pasta/'stderr.log').open('w',encoding='utf-8') as erros:
        proc = subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=saida,stderr=erros,env=env,
            text=True,encoding='utf-8',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        try:
            proc.communicate(prompt,timeout=limite_segundos)
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
    resposta['valor']=json.loads(resposta['valor'])
    assert resposta['acao'] in ['experimentar','encerrar']
    salvar_json(pasta/'conferencia.json', {'modelo_solicitado':'gpt-6-astra','sem_ferramentas':True,
                                          'uso':usos,'sem_resultados_teste_no_prompt':True})
    return resposta
