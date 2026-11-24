"""Qualificação e execução finita da reestimação A/L por blocos."""
import argparse
import io
import os
import platform
from pathlib import Path
import shutil
import subprocess
import sys
import traceback
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ, agora, conferir_arquivos, identidade, ler_json, salvar_json, sha256
from .dados import configuracao_bloco, preparar as preparar_dados

REG=RAIZ/'registros/walkforward_diario'
CFG=RAIZ/'configuracoes/walkforward_diario_001.json'
PROTOCOLO=RAIZ/'docs/protocolo_walkforward_diario.md'


def relativo(p):return Path(p).relative_to(RAIZ).as_posix()


def fontes():
    caminhos=[p for p in (RAIZ/'codigo').rglob('*.py') if '__pycache__' not in p.parts]
    caminhos+=list((RAIZ/'testes/walkforward_diario').glob('*.py'))+[CFG,PROTOCOLO]
    return {relativo(p):sha256(p) for p in sorted(caminhos)}


def referencias(c):
    ptr=ler_json(RAIZ/c['referencia']);p=RAIZ/ptr['pasta']
    assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    fecho=ler_json(p/'fechamento.json');assert fecho['situacao']=='concluido_conferido'
    conferir_arquivos(p,fecho['arquivos'])
    f=ler_json(p/'congelamento.json');info=f['referencias']['moedas'][c['simbolo']]
    arquivos={}
    def guardar(q):arquivos[relativo(q)]=sha256(q)
    for q in (p/'congelamento.json',p/'fechamento.json',p/c['simbolo']/'configuracao.json'):guardar(q)
    for item in (info['diario'],info['mercado_minuto']):
        raiz=RAIZ/item['pasta'];manifesto=raiz/'manifesto.json'
        assert sha256(manifesto)==item['manifesto_sha256']
        conteudo=ler_json(manifesto)['arquivos'];conferir_arquivos(raiz,conteudo);guardar(manifesto)
        for nome in conteudo:guardar(raiz/nome)
    return dict(execucao=ptr,diario=info['diario'],mercado=info['mercado_minuto'],arquivos=arquivos)


def qualificar():
    import fcntl
    import torch
    from .treinamento import ajustar
    from experimentos.fechamento_ramos_diarios.contratos import receita
    from experimentos.taxa_diaria.qualificacao import iguais
    from qualificacao.dados_sinteticos import dados_artificiais
    REG.mkdir(parents=True,exist_ok=True)
    with (RAIZ/'registros/operacional_futuros/gpu.lock').open('a+b') as gpu:
        fcntl.flock(gpu,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert torch.cuda.is_available()
        assert not subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
        c=ler_json(CFG);ref=referencias(c);pai=RAIZ/ref['execucao']['pasta']
        base=ler_json(pai/c['simbolo']/'configuracao.json')
        rodar=subprocess.run([sys.executable,'-B','-m','unittest','testes.walkforward_diario.test_dados','-v'],cwd=RAIZ,capture_output=True,text=True)
        assert rodar.returncode==0,rodar.stdout+rodar.stderr
        destino=REG/'qualificacoes'/agora().replace(':','').replace('+','_');destino.mkdir(parents=True,exist_ok=False)
        (destino/'testes.log').write_text(rodar.stdout+rodar.stderr,encoding='utf-8')
        df=dados_artificiais();df['volume']=120000+np.arange(len(df))*5
        cb=configuracao_bloco(base,c['blocos'][0],c['treino_inicio']);dados,_=preparar_dados(df,cb)
        d={k:{n:v[:65] for n,v in z.items()} for k,z in dados.items() if k!='teste'}
        for v in c['variantes']:
            for repeticao in (1,2):
                ajustar(d,receita(cb,v),42,destino/f'{v}_{repeticao}',{'tipo':'sintetico'},epocas=4)
            iguais(destino/f'{v}_1',destino/f'{v}_2')
        conferir_arquivos(RAIZ,ref['arquivos'])
        q=dict(utc=agora(),situacao='aprovado',fontes=fontes(),referencias=ref,
               sintetico_repetido=True,torch=torch.__version__,cuda=torch.version.cuda,gpu=torch.cuda.get_device_name(),
               limite='Os dois controles de mercado permanecem obrigatórios.')
        salvar_json(destino/'qualificacao.json',q)
        salvar_json(REG/'qualificacao.json',dict(arquivo=relativo(destino/'qualificacao.json'),sha256=sha256(destino/'qualificacao.json')))
        print('QUALIFICACAO_APROVADA',flush=True)


def preparar():
    assert not (REG/'execucao.json').exists()
    qptr=ler_json(REG/'qualificacao.json');assert sha256(RAIZ/qptr['arquivo'])==qptr['sha256']
    q=ler_json(RAIZ/qptr['arquivo']);assert q['situacao']=='aprovado' and q['fontes']==fontes()
    conferir_arquivos(RAIZ,q['referencias']['arquivos']);c=ler_json(CFG)
    base=ler_json(RAIZ/q['referencias']['execucao']['pasta']/c['simbolo']/'configuracao.json')
    df=pd.read_parquet(RAIZ/q['referencias']['diario']['pasta']/'diario.parquet')
    preparados={};escalas={};configs={};populacoes={}
    for bloco in c['blocos']:
        b=bloco['id'];cb=configuracao_bloco(base,bloco,c['treino_inicio']);d,e=preparar_dados(df,cb)
        configs[b]=cb;escalas[b]=e;populacoes[b]={k:len(v['y']) for k,v in d.items()}
        for fase,z in d.items():
            memoria=io.BytesIO();np.savez_compressed(memoria,**z);preparados[f'{b}/dados/{fase}.npz']=memoria.getvalue()
    import hashlib
    f=dict(utc=agora(),configuracao=c,fontes=q['fontes'],referencias=q['referencias'],qualificacao=qptr,
           configs_blocos=configs,escalas=escalas,populacoes=populacoes,
           dados_preparados={k:hashlib.sha256(v).hexdigest() for k,v in preparados.items()})
    ident=identidade(f)[:20];p=RAIZ/'dados/experimentos'/f'walkforward_diario_{ident}';p.mkdir(parents=True,exist_ok=False)
    for nome,b in preparados.items():
        d=p/nome;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(b)
    for nome in f['fontes']:
        d=p/'fontes'/nome;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(RAIZ/nome,d)
    salvar_json(p/'congelamento.json',f)
    ptr=dict(id=ident,pasta=relativo(p),congelamento_sha256=sha256(p/'congelamento.json'))
    salvar_json(REG/'execucao.json',ptr);salvar_json(REG/'estado.json',dict(utc=agora(),situacao='preparado',execucao=ptr))
    print('PREPARADO',ptr,flush=True)


def contexto():
    ptr=ler_json(REG/'execucao.json');p=RAIZ/ptr['pasta']
    assert sha256(p/'congelamento.json')==ptr['congelamento_sha256'];f=ler_json(p/'congelamento.json')
    conferir_arquivos(RAIZ,f['fontes']);conferir_arquivos(p/'fontes',f['fontes'])
    conferir_arquivos(RAIZ,f['referencias']['arquivos']);conferir_arquivos(p,f['dados_preparados'])
    return ptr,p,f


def estado(p,ptr,situacao,**kw):
    s=dict(utc=agora(),situacao=situacao,execucao=ptr,**kw)
    salvar_json(p/'progresso.json',s);salvar_json(REG/'estado.json',s)
    print('ESTADO',situacao,kw,flush=True)


def executar():
    import fcntl
    from .treinamento import ajustar
    from experimentos.fechamento_ramos_diarios.contratos import receita
    from experimentos.taxa_diaria.qualificacao import iguais
    with (RAIZ/'registros/operacional_futuros/gpu.lock').open('a+b') as gpu,(REG/'execucao.lock').open('a+b') as lock:
        fcntl.flock(gpu,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
        ptr,p,f=contexto();assert not (p/'inicio.json').exists()
        proc=dict(pid=os.getpid(),host=platform.node(),boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                  inicio_processo_ticks=Path('/proc/self/stat').read_text().split()[21],utc=agora(),ativo=True)
        salvar_json(p/'inicio.json',proc);salvar_json(p/'processo.json',proc);concluidos=0
        try:
            for bloco in f['configuracao']['blocos']:
                b=bloco['id'];base=p/b;cfg=f['configs_blocos'][b]
                dados={fase:dict(np.load(base/'dados'/f'{fase}.npz',allow_pickle=False)) for fase in ('treino','validacao')}
                trabalhos=[(v,42,False) for v in ('A','L')]
                if b=='B1':trabalhos += [(v,42,True) for v in ('A','L')]
                trabalhos += [(v,s,False) for s in (17,2026) for v in ('A','L')]
                for v,seed,controle in trabalhos:
                    nome=v+'_'+('controle_' if controle else '')+str(seed)
                    estado(p,ptr,'treinando',bloco=b,ajuste=nome,ajustes_concluidos=concluidos,total_ajustes=26)
                    ajuste=base/'ajustes'/nome
                    ajustar(dados,receita(cfg,v),seed,ajuste,dict(execucao=ptr['id'],bloco=b,variante=v,seed=seed))
                    if controle:
                        iguais(base/'ajustes'/f'{v}_42',ajuste)
                        salvar_json(base/f'controle_{v}.json',dict(aprovado=True,seed=42))
                    concluidos+=1
            from .avaliacao import executar as avaliar
            estado(p,ptr,'avaliando',ajustes_concluidos=concluidos,total_ajustes=26)
            resultado=avaliar(p,f,lambda **kw:estado(p,ptr,'avaliando',ajustes_concluidos=concluidos,total_ajustes=26,**kw))
            contexto();arquivos={q.relative_to(p).as_posix():sha256(q) for q in p.rglob('*') if q.is_file() and 'fontes' not in q.relative_to(p).parts and q.name not in ('processo.json','progresso.json','fechamento.json')}
            salvar_json(p/'fechamento.json',dict(utc=agora(),situacao='concluido_controles_aprovados',execucao=ptr,
                        ajustes_cientificos=24,controles=2,resumo=resultado,arquivos=arquivos))
            salvar_json(REG/'fechamento.json',dict(arquivo=relativo(p/'fechamento.json'),sha256=sha256(p/'fechamento.json')))
            estado(p,ptr,'concluido_controles_aprovados',ajustes_concluidos=26,total_ajustes=26,conferencia_posterior='pendente')
        except BaseException:
            salvar_json(p/'incidente.json',dict(utc=agora(),erro=traceback.format_exc()))
            estado(p,ptr,'interrompido_preservado',ajustes_concluidos=concluidos,total_ajustes=26);raise
        finally:
            proc.update(ativo=False,encerramento_utc=agora());salvar_json(p/'processo.json',proc)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('acao',choices=['qualificar','preparar','executar'])
    globals()[parser.parse_args().acao]()
