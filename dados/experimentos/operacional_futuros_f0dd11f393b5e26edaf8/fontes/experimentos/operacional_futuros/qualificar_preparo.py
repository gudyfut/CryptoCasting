"""Recibo de qualificação vinculado às fontes exatas, antes do congelamento."""
import json
import subprocess
import sys
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,sha256,agora
from .ciclo import REG,fontes,preservar,PYLIN,RAIZLIN


def executar():
    destino=REG/'qualificacao_integrada/qualificacao_final.json'
    if destino.exists(): raise FileExistsError('Recibo já existe; preservar e criar revisão identificada se necessário.')
    antes=fontes();historico=preservar()
    sint=REG/'qualificacao_integrada/sintetico_003/conclusao.json';q=ler_json(sint)
    if q['status']!='aprovado' or q['treinos_mercado']!=0 or len(q['pares'])!=2:
        raise ValueError('Qualificação sintética inválida.')
    agente=REG/'qualificacao_integrada/proponente_001'
    if not (agente/'receita_validada.json').exists(): raise ValueError('Proponente não qualificado.')
    for linha in (agente/'eventos.jsonl').read_text(encoding='utf-8').splitlines():
        e=json.loads(linha)
        if e.get('type') in ('turn.failed','error'): raise ValueError('Erro na qualificação proponente.')
        if e.get('type') in ('item.started','item.completed') and e['item']['type'] not in ('agent_message','reasoning','error'):
            raise ValueError('Proponente chamou ferramenta.')
    cmd=['wsl','-d','Ubuntu','--cd',RAIZLIN,PYLIN,'-B','-m','unittest','discover','-s','tests_operacional_futuros','-v']
    r=subprocess.run(cmd,cwd=RAIZ,capture_output=True,text=True,encoding='utf-8')
    log=REG/'qualificacao_integrada/testes_finais.log';log.write_text(r.stdout+r.stderr,encoding='utf-8')
    if r.returncode or 'skipped' in r.stderr or '\nOK\n' not in r.stderr:
        raise ValueError('Testes finais falharam ou ignoraram CUDA.')
    if fontes()!=antes: raise ValueError('Fontes mudaram durante os testes.')
    salvar_json(destino,{'status':'aprovado','utc':agora(),'fontes':antes,'sintetico_sha256':sha256(sint),
        'sintetico':q,'proponente_resposta_sha256':sha256(agente/'resposta.json'),
        'proponente_sem_ferramentas':True,'consultas_consumidas':1,'testes_log_sha256':sha256(log),
        'historicos_preservados':len(historico),'treinos_mercado_ate_qualificacao':0,
        'limites':'Aprovação técnica não demonstra lucro, liquidação Binance ou generalização.'})
    print(str(destino),flush=True)


if __name__=='__main__':executar()
