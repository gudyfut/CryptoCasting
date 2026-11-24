"""Coordenador Windows: Astra propoe; worker CUDA mede; testes ficam fechados."""
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import traceback
from pathlib import Path
from infraestrutura.artefatos import RAIZ, agora, identidade, ler_json, salvar_json, sha256, conferir_arquivos
from .contrato import REFERENCIA, DESENVOLVIMENTO, FINAIS, SEEDS, chave_receita, pontuar, elegivel

REG=RAIZ/'registros/busca_astra'

def fontes():
    grupos=['experimentos/busca_astra','tests_busca_astra','infraestrutura','modelos','treinamento','backtest_carteira']
    return {p.relative_to(RAIZ).as_posix():sha256(p) for g in grupos for p in (RAIZ/g).glob('*.py')}

def preparar(qualificacao):
    if (REG/'execucao.json').exists():raise FileExistsError('Busca ja preparada; conferir antes de qualquer repeticao.')
    q=ler_json(qualificacao);assert q['situacao']=='aprovado'
    conferir_arquivos(RAIZ,q['fontes'])
    cfg=ler_json(RAIZ/'configuracoes/busca_astra_001.json')
    fg=fontes()
    for p in ['docs/protocolo_busca_astra.md','configuracoes/busca_astra_001.json','experimentos/__init__.py']:
        fg[p]=sha256(RAIZ/p)
    antigo=ler_json(RAIZ/'registros/crua_huber/preservacao_antes.json')['arquivos']
    historico=RAIZ/'dados/experimentos/crua_huber_1781f557fdf2b45a3ae2'
    preservados=dict(antigo)
    for p in historico.rglob('*'):
        if p.is_file():preservados[p.relative_to(RAIZ).as_posix()]=sha256(p)
    conferir_arquivos(RAIZ,preservados)
    guardar={'utc':agora(),'arquivos':preservados};salvar_json(REG/'preservacao_antes.json',guardar)
    from .dados import CANDLES
    import platform
    import importlib.metadata as md
    cmd=Path(shutil.which('codex.cmd')).parent/'node_modules/@openai/codex/bin/codex.js'
    cli=subprocess.check_output([shutil.which('node.exe'),str(cmd),'--version'],text=True).strip()
    contrato={'configuracao':cfg,'fontes':fg,'referencia':REFERENCIA,'ambiente_cuda':q['ambiente'],
        'ambiente_coordenador':{'python':platform.python_version(),'codex':cli,
            'pacotes':{n:md.version(n) for n in ['numpy','pandas','pyarrow']}},
        'qualificacao':{'arquivo':str(Path(qualificacao).resolve().relative_to(RAIZ)), 'sha256':sha256(qualificacao)},
        'candles':{'pasta':CANDLES,'manifesto_sha256':sha256(RAIZ/CANDLES/'manifesto.json')},
        'backtest_congelamento_sha256':sha256(RAIZ/'dados/experimentos/backtest_carteira_8ec8a66648313caa48e3/congelamento.json'),
        'minutos_manifesto_sha256':sha256(RAIZ/'dados/mercado/binance_spot/449aab6c79dbf88aa625/manifesto.json'),
        'preservacao_sha256':sha256(REG/'preservacao_antes.json')}
    codigo=identidade(contrato)[:20];p=RAIZ/f'dados/experimentos/busca_astra_{codigo}'
    p.mkdir(parents=True,exist_ok=False)
    for nome in fg:
        dest=p/'fontes'/nome;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(RAIZ/nome,dest)
    salvar_json(p/'congelamento.json',dict(contrato,id=codigo,utc=agora()))
    ptr={'id':codigo,'pasta':p.relative_to(RAIZ).as_posix(),'congelamento_sha256':sha256(p/'congelamento.json')}
    salvar_json(REG/'execucao.json',ptr)
    autorizacao={'utc':agora(),'execucao':ptr,'pedido':'ok',
        'contexto':'Confirmacao explicita do plano: Astra ate12h exploracao,12candidatas,triagem1seed2recortes,ate3promovidas3seeds,uma finalista8seeds4blocos.',
        'limites':cfg['orcamento'],'api_paga':False,'conta':'ChatGPT','promocao_automatica':False}
    salvar_json(p/'autorizacao.json',autorizacao);salvar_json(REG/'autorizacao.json',autorizacao)
    salvar_json(REG/'estado.json',{'situacao':'preparado_autorizado','execucao':ptr,'utc':agora()})
    print(json.dumps(ptr),flush=True)
    return ptr

def conferir(p,ptr):
    assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    f=ler_json(p/'congelamento.json');conferir_arquivos(RAIZ,f['fontes']);conferir_arquivos(p/'fontes',f['fontes'])
    assert sha256(REG/'preservacao_antes.json')==f['preservacao_sha256']
    assert sha256(RAIZ/f['candles']['pasta']/'manifesto.json')==f['candles']['manifesto_sha256']
    assert sha256(RAIZ/'dados/experimentos/backtest_carteira_8ec8a66648313caa48e3/congelamento.json')==f['backtest_congelamento_sha256']
    assert sha256(RAIZ/'dados/mercado/binance_spot/449aab6c79dbf88aa625/manifesto.json')==f['minutos_manifesto_sha256']
    return f

def controle_cpu(a,b):
    import numpy as np
    import pandas as pd
    ra,rb=ler_json(a/'resultado.json'),ler_json(b/'resultado.json')
    assert ra['epoca']==rb['epoca']
    dif=abs(ra['validacao']['mse']-rb['validacao']['mse'])/ra['validacao']['mse'];assert dif<=1e-4
    maximos={}
    for parte in ['validacao']+(['teste'] if 'teste' in ra else []):
        qa,qb=pd.read_parquet(a/f'previsoes_{parte}.parquet'),pd.read_parquet(b/f'previsoes_{parte}.parquet')
        pd.testing.assert_frame_equal(qa.drop(columns='previsao'),qb.drop(columns='previsao'))
        maximos[parte]=float(np.max(np.abs(qa.previsao-qb.previsao)));assert maximos[parte]<=1e-5
    return {'mesma_epoca':True,'diferenca_relativa_mse':dif,'maxima_diferenca':maximos}

class Coordenador:
    def __init__(self,p,ptr,f):
        self.p,self.ptr,self.f=p,ptr,f
        self.inicio=time.time();self.limite=self.inicio+12*3600
        self.triagem_fim=self.inicio+8*3600
        self.jobs=[];self.candidatas=[];self.ref=[]

    def estado(self,fase,**outros):
        d={'utc':agora(),'situacao':'executando','fase':fase,'execucao':self.ptr,
            'ajustes_iniciados':len(self.jobs),'ajustes_concluidos':sum(x['status']=='concluido' for x in self.jobs),
            'teto_ajustes':108,'candidatas':len(self.candidatas),
            'inicio_timestamp':self.inicio,'limite_exploracao_timestamp':self.limite,**outros}
        salvar_json(self.p/'progresso.json',d);salvar_json(REG/'estado.json',d)
        print(fase, outros, flush=True)

    def checar(self):
        conferir(self.p,self.ptr)
        if hasattr(self,'finalista_sha256'):
            assert sha256(self.p/'finalista.json')==self.finalista_sha256,'Finalista alterada apos selecao.'
        if (REG/'PARAR').exists():raise InterruptedError('Parada solicitada por arquivo PARAR.')

    def ajuste(self,receita,bloco,seed,grupo,controle=False):
        self.checar()
        if len(self.jobs)>=108:raise RuntimeError('Orcamento total esgotado.')
        limite=self.limite if bloco.startswith('D') else self.final_limite
        restante=limite-time.time()
        if restante<60:raise TimeoutError('Prazo da fase esgotado; nao iniciar ajuste.')
        destino=self.p/grupo/f'{bloco}_{seed}'
        receita_p=self.p/'receitas'/f'{chave_receita(receita)}.json'
        if not receita_p.exists():salvar_json(receita_p,receita)
        else:assert ler_json(receita_p)==receita
        job={'numero':len(self.jobs)+1,'execucao_pasta':self.ptr['pasta'],
            'congelamento_sha256':self.ptr['congelamento_sha256'],'receita':receita,
            'receita_arquivo':receita_p.relative_to(RAIZ).as_posix(),'bloco':bloco,'seed':seed,
            'destino':destino.relative_to(RAIZ).as_posix(),'controle':controle,
            'limite_segundos':min(2700,int(restante)-10)}
        if bloco.startswith('B'):job['finalista_sha256']=self.finalista_sha256
        pedido=self.p/'pedidos'/f'{job["numero"]:03}.json';salvar_json(pedido,job)
        self.jobs.append(dict(job,status='iniciado'));salvar_json(self.p/'ajustes.json',self.jobs)
        self.estado('controle' if controle else 'treinamento',bloco=bloco,seed=seed,grupo=grupo)
        unix='/mnt/'+RAIZ.drive[0].lower()+str(RAIZ)[2:].replace('\\','/')
        cmd=['wsl','-d','Ubuntu','--cd',unix,'--','/home/murilorfm/.venvs/cc/bin/python','-B','-u',
             '-m','experimentos.busca_astra.worker',pedido.relative_to(RAIZ).as_posix()]
        log=pedido.with_suffix('.log')
        with log.open('w',encoding='utf-8') as saida:
            proc=subprocess.Popen(cmd,stdout=saida,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            salvar_json(self.p/'worker_windows.json',{'pid':proc.pid,'ativo':True,'pedido':job,'utc':agora()})
            # Um timeout nunca autoriza lancar outro worker; nao matar so o wrapper WSL.
            try:codigo=proc.wait(timeout=job['limite_segundos']+300)
            except subprocess.TimeoutExpired:
                raise RuntimeError('Worker ainda pode estar vivo: inspecionar PID WSL antes de retomar. Nenhuma duplicacao.')
        salvar_json(self.p/'worker_windows.json',{'pid':proc.pid,'ativo':False,'codigo':codigo,'utc':agora()})
        if codigo:raise RuntimeError(f'Worker falhou codigo{codigo}; consultar {log}')
        conferir_arquivos(destino,ler_json(destino/'conclusao.json')['arquivos'])
        r=ler_json(destino/'resultado.json')
        self.jobs[-1]['status']='concluido';salvar_json(self.p/'ajustes.json',self.jobs)
        return r

    def executar(self):
        from .dados import Dados,carregar_candles,diagnostico
        from .agente import consultar
        self.estado('diagnostico')
        candles=carregar_candles(True)
        diag={b:{v:diagnostico(Dados(candles,dict(REFERENCIA,representacao=v),b))
                 for v in ['relativa','crua']} for b in DESENVOLVIMENTO}
        salvar_json(self.p/'diagnostico_desenvolvimento.json',diag)
        # Controle antes das demais seeds; nunca entra em ranking/media.
        for b in DESENVOLVIMENTO:
            for s in SEEDS[:3]:
                self.ref.append(self.ajuste(REFERENCIA,b,s,'desenvolvimento/referencia'))
                if b=='D1' and s==42:
                    self.ajuste(REFERENCIA,b,s,'controles/referencia',True)
                    salvar_json(self.p/'controle_referencia.json',controle_cpu(
                        self.p/'desenvolvimento/referencia/D1_42',self.p/'controles/referencia/D1_42'))
        vistas={chave_receita(REFERENCIA)}
        for n in range(1,13):
            if time.time()>=self.triagem_fim:break
            self.checar();self.estado('astra_propondo',rodada=n)
            contexto={'diagnostico':diag,'referencia':self.ref,'tentativas':self.candidatas,
                'rodada':n,'maximo':12,'horas_restantes_exploracao':max(0,(self.limite-time.time())/3600)}
            proposta=consultar(self.p/'agente'/f'{n:02}',contexto,versao_cli=self.f['ambiente_coordenador']['codex'])
            if proposta['acao']=='encerrar':break
            r=proposta['receita'];key=chave_receita(r)
            if key in vistas:raise ValueError('Proposta repetida; preservar e interromper, sem consulta substituta gratuita.')
            vistas.add(key)
            cand={'id':f'C{n:02}_{key}','proposta':proposta,'resultados':[]}
            self.candidatas.append(cand)
            for b in DESENVOLVIMENTO:
                cand['resultados'].append(self.ajuste(r,b,42,'desenvolvimento/'+cand['id']))
            cand['score_triagem']=pontuar(cand['resultados'])
            salvar_json(self.p/'candidatas.json',self.candidatas)
        if not self.candidatas:return self.encerrar('concluido_sem_finalista','Nenhuma candidata proposta/concluida.')
        top=sorted(self.candidatas,key=lambda c:(c['score_triagem'][0],c['score_triagem'][2],
                    c['resultados'][0]['parametros'],c['id']))[:3]
        for cand in top:
            if time.time()>=self.limite:break
            por={(r['bloco'],r['seed']):r for r in cand['resultados']}
            for b in DESENVOLVIMENTO:
                for s in SEEDS[1:3]:
                    por[b,s]=self.ajuste(cand['proposta']['receita'],b,s,'desenvolvimento/'+cand['id'])
            cand['resultados']=[por[b,s] for b in DESENVOLVIMENTO for s in SEEDS[:3]]
            cand['score_promocao']=pontuar(cand['resultados']);cand['elegivel']=elegivel(cand['resultados'],self.ref)
            salvar_json(self.p/'candidatas.json',self.candidatas)
        elegiveis=[c for c in top if c.get('elegivel')]
        if not elegiveis:return self.encerrar('concluido_sem_finalista','Nenhuma candidata cumpriu o criterio fixo de validacao.')
        melhor=min(elegiveis,key=lambda c:(c['score_promocao'][0],c['score_promocao'][2],c['resultados'][0]['parametros'],c['id']))
        finalista={'utc':agora(),'id':melhor['id'],'receita':melhor['proposta']['receita'],
            'score':melhor['score_promocao'],'selecionada_sem_testes':True,'criterio':self.f['configuracao']['selecao']}
        salvar_json(self.p/'finalista.json',finalista)
        self.finalista_sha256=sha256(self.p/'finalista.json')
        self.final_limite=time.time()+12*3600
        salvar_json(self.p/'fase_final.json',{'utc':agora(),'limite_timestamp':self.final_limite,
            'maximo_ajustes':65,'maximo_simulacoes':408,'retrospectiva':True,'finalista_sha256':self.finalista_sha256})
        # A partir daqui nao ha mais chamadas ao Astra nem alteracao da receita.
        for b in FINAIS:
            for v,r in [('referencia',REFERENCIA),('candidata',finalista['receita'])]:
                for s in SEEDS:
                    self.ajuste(r,b,s,'final/'+v)
                    if b=='B1' and v=='candidata' and s==42:
                        self.ajuste(r,b,s,'controles/finalista',True)
                        salvar_json(self.p/'controle_finalista.json',controle_cpu(
                            self.p/'final/candidata/B1_42',self.p/'controles/finalista/B1_42'))
        self.estado('publicacao_final')
        from .publicacao import publicar
        publicar(self.p)
        return self.encerrar('concluido_conferido','Candidata congelada avaliada; sem promocao automatica.')

    def encerrar(self,status,motivo):
        self.checar();conferir_arquivos(RAIZ,ler_json(REG/'preservacao_antes.json')['arquivos'])
        dados={'utc':agora(),'situacao':status,'execucao':self.ptr,'motivo':motivo,
            'ajustes_concluidos':sum(j['status']=='concluido' for j in self.jobs),'candidatas':len(self.candidatas),
            'preservacao_conferida':True,'promocao_automatica':False,'retrospectiva':True}
        salvar_json(self.p/'fechamento.json',dados);salvar_json(REG/'fechamento.json',dados)
        salvar_json(REG/'estado.json',dados);salvar_json(self.p/'progresso.json',dados)
        return dados

def executar():
    import msvcrt
    ptr=ler_json(REG/'execucao.json');p=RAIZ/ptr['pasta']
    if (p/'processo.json').exists():raise RuntimeError('Execucao ja iniciada; revisar estado, nao reiniciar automaticamente.')
    f=conferir(p,ptr);assert ler_json(p/'autorizacao.json')['execucao']==ptr
    with (REG/'coordenador.lock').open('a+b') as lock:
        lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        salvar_json(p/'processo.json',{'ativo':True,'pid':os.getpid(),'host':socket.gethostname(),'utc':agora()})
        try:
            return Coordenador(p,ptr,f).executar()
        except BaseException:
            incidente={'utc':agora(),'situacao':'interrompido','execucao':ptr,'erro':traceback.format_exc(),
                       'retomada_automatica':False,'aviso':'Conferir worker_windows e processos WSL antes de qualquer retomada.'}
            salvar_json(p/'incidente.json',incidente);salvar_json(REG/'estado.json',incidente)
            raise
        finally:
            salvar_json(p/'processo.json',{'ativo':False,'pid':os.getpid(),'host':socket.gethostname(),'utc':agora()})
