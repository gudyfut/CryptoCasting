"""Um processo CUDA isolado por ajuste autorizado, com identidade e lock."""
import os
import socket
import traceback
import time
from pathlib import Path
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,sha256,agora,conferir_arquivos
from .contrato import REG,SEEDS,FINAIS,ambiente_cuda,ancoras,validar_receita

def executar(pedido):
    import fcntl
    from .dados import Dados,carregar_candles
    from .metricas import avaliar
    from experimentos.busca_astra.treino import ajustar
    q=ler_json(pedido);ptr=ler_json(REG/'execucao.json');p=RAIZ/ptr['pasta']
    assert q['execucao']==ptr and sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    f=ler_json(p/'congelamento.json')
    assert ler_json(p/'autorizacao.json')['execucao']==ptr
    jobs=ler_json(p/'ajustes.json');assert 1<=q['numero']<=197 and len(jobs)==q['numero']
    assert jobs[-1]==dict(q,status='iniciado')
    assert q['seed'] in SEEDS and q['bloco'] in ['S1','S2','S3',*FINAIS]
    assert 0<q['limite_segundos']<=2700 and time.time()<q['prazo_timestamp']
    assert ambiente_cuda()==f['ambiente_cuda']
    conferir_arquivos(RAIZ,f['fontes'])
    destino=RAIZ/q['destino'];assert destino.resolve().is_relative_to(p.resolve())
    receita=ler_json(p/'receitas'/f'{q["receita_id"]}.json');assert receita==q['receita']
    validar_receita(receita,ancora=receita in ancoras().values())
    if q['bloco'].startswith('B'):
        assert sha256(p/'finalista.json')==q['finalista_sha256']
        assert receita in [*ancoras().values(),ler_json(p/'finalista.json')['receita']]
    with (REG/'gpu.lock').open('a+b') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        processo=destino.parent/(destino.name+'_processo.json')
        salvar_json(processo,{'ativo':True,'pid':os.getpid(),'host':socket.gethostname(),'boot':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'utc':agora()})
        try:
            dados=Dados(carregar_candles(q['bloco'].startswith('S')),receita,q['bloco'])
            ajustar(dados,receita,q['seed'],destino,q,q['limite_segundos'])
            avaliar(destino,dados)
        except BaseException as e:
            salvar_json(destino.parent/(destino.name+'_incidente.json'),{'utc':agora(),'tipo':type(e).__name__,'erro':traceback.format_exc()})
            raise
        finally:
            salvar_json(processo,{'ativo':False,'pid':os.getpid(),'host':socket.gethostname(),'utc':agora()})

if __name__=='__main__':
    import sys
    executar(sys.argv[1])
