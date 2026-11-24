"""Um trabalho CUDA por vez. Nao consulta Astra nem muda sua receita."""
import argparse
import os
import socket
import traceback
from pathlib import Path
from infraestrutura.artefatos import RAIZ, ler_json, salvar_json, sha256, agora, conferir_arquivos

def executar(pedido):
    import fcntl
    from .dados import Dados, carregar_candles
    from .treino import ajustar
    q = ler_json(pedido)
    root = RAIZ/q['execucao_pasta']
    f = ler_json(root/'congelamento.json')
    assert sha256(root/'congelamento.json') == q['congelamento_sha256']
    ptr=ler_json(RAIZ/'registros/busca_astra/execucao.json')
    assert ptr==ler_json(root/'autorizacao.json')['execucao']
    assert ptr['pasta']==q['execucao_pasta'] and ptr['congelamento_sha256']==q['congelamento_sha256']
    jobs=ler_json(root/'ajustes.json')
    assert 1<=q['numero']<=108 and len(jobs)==q['numero']
    assert jobs[-1]==dict(q,status='iniciado'),'Pedido ausente do orcamento ou ja executado.'
    assert 0<q['limite_segundos']<=2700
    assert (RAIZ/q['destino']).resolve().is_relative_to(root.resolve())
    assert (RAIZ/q['receita_arquivo']).resolve().is_relative_to((root/'receitas').resolve())
    from .contrato import ambiente_cuda, SEEDS, DESENVOLVIMENTO, FINAIS
    assert q['seed'] in SEEDS and q['bloco'] in dict(DESENVOLVIMENTO,**FINAIS)
    assert ambiente_cuda()==f['ambiente_cuda'],'Ambiente CUDA diverge da qualificacao.'
    conferir_arquivos(RAIZ, f['fontes'])
    assert q['receita'] == ler_json(RAIZ/q['receita_arquivo'])
    if q['bloco'].startswith('B'):
        ff=ler_json(root/'finalista.json')
        assert q['receita'] in [ff['receita'],f['referencia']]
        assert sha256(root/'finalista.json') == q['finalista_sha256']
        assert q['finalista_sha256']==ler_json(root/'fase_final.json')['finalista_sha256']
    destino = RAIZ/q['destino']
    processo = destino.parent/(destino.name+'_processo.json')
    with (root/'gpu.lock').open('a+b') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        salvar_json(processo, {'ativo':True,'pid':os.getpid(),'host':socket.gethostname(),
            'boot':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'utc':agora()})
        try:
            dados=Dados(carregar_candles(q['bloco'].startswith('D')),q['receita'],q['bloco'])
            ajustar(dados,q['receita'],q['seed'],destino,q,q['limite_segundos'])
        except BaseException:
            salvar_json(destino.parent/(destino.name+'_incidente.json'),{'utc':agora(),'erro':traceback.format_exc()})
            raise
        finally:
            salvar_json(processo, {'ativo':False,'pid':os.getpid(),'host':socket.gethostname(),'utc':agora()})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('pedido');a=p.parse_args();executar(a.pedido)
