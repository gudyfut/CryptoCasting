"""Rotina finita posterior: espera fechamento já auditado, diagnostica e analisa, sem treino."""
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from uuid import uuid4
from infraestrutura.artefatos import RAIZ,agora,ler_json,salvar_json,sha256,conferir_arquivos


def concluir():
    import msvcrt
    reg=RAIZ/'registros/cryptomamba';ptr=ler_json(reg/'execucao.json');base=RAIZ/ptr['pasta']
    with (reg/'rotina_posterior.lock').open('a+b') as lock:
        if not lock.tell():lock.write(b'0');lock.flush()
        lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        estado={'ativo':True,'pid_windows':os.getpid(),'inicio_utc':agora(),'execucao':ptr['id'],'natureza':'Rotina finita de leitura/inferência depois do fechamento; não treina e não é agendamento recorrente.'}
        fontes={n:sha256(RAIZ/n) for n in ('manutencao/concluir_analise_cryptomamba.py','manutencao/diagnosticar_sensibilidade_cryptomamba.py','manutencao/analisar_cryptomamba_concluido.py')}
        estado['fontes']=fontes;salvar_json(reg/'rotina_posterior.json',estado)
        inicio=time.monotonic()
        try:
            while not (reg/'fechamento.json').exists():
                try:pr=ler_json(base/'progresso.json')
                except json.JSONDecodeError:time.sleep(1);continue
                if pr['status']=='interrompido':raise RuntimeError('Treino interrompido; preservar e investigar, sem repetir.')
                if time.monotonic()-inicio>24*3600:raise TimeoutError('Aguardar avaliação humana; limite24h da rotina posterior.')
                time.sleep(30)
            conferir_arquivos(RAIZ,fontes)
            indice=ler_json(reg/'sensibilidade_atual.json') if (reg/'sensibilidade_atual.json').exists() else {}
            for seed in (17,42,2026,7,123,31415):
                if str(seed) in indice:continue
                subprocess.run(['wsl.exe','-d','Ubuntu','--cd','/mnt/c/Users/MuriloRFM/Documents/GitHub/CryptoCasting','--',
                    '/home/murilorfm/.venvs/cc/bin/python','-B','-u','-m','manutencao.diagnosticar_sensibilidade_cryptomamba','--seed',str(seed)],cwd=RAIZ,check=True)
            from manutencao.analisar_cryptomamba_concluido import analisar
            if (reg/'analise_interpretativa_atual.json').exists():raise FileExistsError('Análise já entregue; não repetir.')
            a=analisar();conferir_arquivos(RAIZ,fontes)
            s=ler_json(reg/'estado.json');s['analise_interpretativa']=ler_json(reg/'analise_interpretativa_atual.json');s['sensibilidade']='registros/cryptomamba/sensibilidade_atual.json';salvar_json(reg/'estado.json',s)
            doc=RAIZ/'README.md';txt=doc.read_text(encoding='utf-8-sig');txt=txt.replace('CryptoMamba adaptado em execução autorizada.','CryptoMamba adaptado concluído e conferido.');doc.write_text(txt,encoding='utf-8')
            doc=RAIZ/'docs/andamento.md';txt=doc.read_text(encoding='utf-8-sig');nota=f'## Interpretação independente do CryptoMamba adaptado\n\nConferidas59séries por somas independentes; médias3/6seeds, seis diagnósticos inicial/checkpoint, figuras PNG/PDF e análise externa de Naive preservados. [Relatório único](resultados_cryptomamba_adaptado.md) e [análise com verificador](../{s["analise_interpretativa"]["arquivo"]}). Nenhum novo ajuste, seleção, alteração de receita ou promoção automática. Encerramento da revisão em{agora()}.\n\n';doc.write_text(txt.replace('# Andamento do CryptoCasting\n','# Andamento do CryptoCasting\n\n'+nota,1),encoding='utf-8')
            estado.update(ativo=False,fim_utc=agora(),situacao='analise_concluida',analise=s['analise_interpretativa']);salvar_json(reg/'rotina_posterior.json',estado)
            print(estado,flush=True)
        except BaseException:
            estado.update(ativo=False,fim_utc=agora(),situacao='falha_posterior_sem_retreino',erro=traceback.format_exc());salvar_json(reg/'rotina_posterior.json',estado);salvar_json(reg/'incidentes'/f'{uuid4().hex}.json',estado);raise
        finally:
            lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)


if __name__=='__main__':
    concluir()
