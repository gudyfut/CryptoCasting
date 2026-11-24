import sys, os, socket, traceback
from pathlib import Path
from infraestrutura.artefatos import RAIZ, ler_json, salvar_json, agora
from .contrato import REG, conferir_execucao, validar_pedido

def executar(pedido):
    import fcntl
    from experimentos.busca_astra.dados import Dados, carregar_candles
    from experimentos.busca_astra.treino import ajustar
    from experimentos.busca_astra.contrato import ambiente_cuda
    q=ler_json(pedido);ptr=ler_json(REG/'execucao.json');p=RAIZ/ptr['pasta']
    f=conferir_execucao(p,ptr);dest=validar_pedido(q,p,ptr,ler_json(p/'ajustes.json'))
    assert ambiente_cuda()==f['ambiente_cuda']
    with (REG/'gpu.lock').open('a+b') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        proc={'ativo':True,'pid':os.getpid(),'host':socket.gethostname(),
              'boot':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'utc':agora(),'numero':q['numero']}
        salvar_json(p/'worker_linux.json',proc)
        try:
            item=q['item'];dados=Dados(carregar_candles(),item['receita'],item['bloco'])
            ajustar(dados,item['receita'],item['seed'],dest,q,limite_segundos=2700)
        except BaseException:
            salvar_json(p/f"incidente_worker_{q['numero']:03}.json",{'utc':agora(),'erro':traceback.format_exc()});raise
        finally:salvar_json(p/'worker_linux.json',dict(proc,ativo=False,fim=agora()))

if __name__=='__main__':executar(sys.argv[1])
