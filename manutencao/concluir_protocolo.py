"""Continuação sequencial do protocolo autorizado; não duplica nem reinicia falhas.

Executar no mesmo WSL do treinamento. Aguarda o PID existente, consolida a fase,
congela e executa a avaliação apenas se todos os gates científicos forem válidos.
A conclusão deste processo não substitui o aceite final da interface e do TCC.
"""
import argparse
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from previsao24.arquivos import RAIZ,ler_json,salvar_json,agora,verificar_arquivos

def continuar(execucao,pid):
    estado=RAIZ/'registros/continuacao_protocolo.json'
    bloqueio=RAIZ/'registros/continuacao_protocolo.lock'
    with bloqueio.open('a') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        ponteiro=ler_json(RAIZ/'registros/execucao_atual.json')
        if ponteiro['id']!=execucao:
            raise ValueError('Execução ativa mudou; não continuar outra identidade.')
        pasta=RAIZ/ponteiro['caminho']
        registro={'execucao':execucao,'pid':os.getpid(),'pid_aguardado':pid,'inicio_utc':agora(),'status':'aguardando_desenvolvimento'}
        salvar_json(estado,registro)
        try:
            while True:
                try:
                    os.kill(pid,0)
                except ProcessLookupError:
                    break
                comando=Path(f'/proc/{pid}/cmdline').read_bytes()
                if b'run_previsao.py' not in comando or b'executar' not in comando:
                    raise RuntimeError('PID foi reutilizado por outro comando; não presumir conclusão.')
                time.sleep(30)
            if not (pasta/'desenvolvimento_concluido.json').exists():
                raise RuntimeError('Treinamento terminou sem conclusão auditada. Nenhum reinício automático.')
            passos=[('consolidar_desenvolvimento',['manutencao/consolidar_resultados.py','--fase','desenvolvimento']),
                    ('congelar',['run_previsao.py','congelar']),
                    ('avaliar',['run_previsao.py','executar','--fase','avaliacao']),
                    ('consolidar_avaliacao',['manutencao/consolidar_resultados.py','--fase','avaliacao']),
                    ('exportar',['manutencao/exportar_portal.py'])]
            for nome,argumentos in passos:
                atual=ler_json(RAIZ/'registros/execucao_atual.json')
                if atual['id']!=execucao:
                    raise ValueError('Identidade alterada durante a continuação.')
                verificar_arquivos(RAIZ,ler_json(pasta/'execucao.json')['assinatura']['fontes'])
                if nome=='avaliar' and (pasta/'avaliacao_concluido.json').exists():
                    continue
                registro.update(status=nome,atualizado_utc=agora())
                salvar_json(estado,registro)
                log=RAIZ/'registros/logs'/f'{nome}_{execucao}.log'
                if log.exists():
                    log=log.with_name(f'{log.stem}_{int(time.time())}.log')
                print(f'{agora()} {nome}: {log}',flush=True)
                with log.open('w') as saida:
                    processo=subprocess.run([sys.executable,'-u',*argumentos],cwd=RAIZ,stdout=saida,stderr=subprocess.STDOUT)
                if processo.returncode:
                    raise RuntimeError(f'{nome} falhou com código {processo.returncode}; consultar {log}. Sem reinício automático.')
            registro.update(status='execucao_e_publicacao_concluidas_aguardando_aceite',fim_utc=agora())
        except Exception as erro:
            registro.update(status='falha',erro=f'{type(erro).__name__}: {erro}',fim_utc=agora())
            raise
        finally:
            salvar_json(estado,registro)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--execucao',required=True)
    parser.add_argument('--aguardar-pid',type=int,required=True)
    args=parser.parse_args()
    continuar(args.execucao,args.aguardar_pid)
