import os, socket, shutil, subprocess, time, traceback
from pathlib import Path
from infraestrutura.artefatos import RAIZ, ler_json, salvar_json, sha256, identidade, conferir_arquivos, agora
from .contrato import REG, ORIGEM, ASTRA, CRUA, grade, fontes, conferir_execucao

def preparar():
    assert not (REG/'execucao.json').exists(),'Ciclo ja preparado; nao duplicar.'
    assert ler_json(ORIGEM/'fechamento.json')['situacao']=='concluido_conferido'
    assert not ler_json(ORIGEM/'processo.json')['ativo']
    processos=subprocess.check_output(['wsl','-d','Ubuntu','--','ps','-eo','args'],text=True)
    assert not any('python' in s and ('experimentos.' in s or 'run_' in s) for s in processos.splitlines()),'Inspecionar outro processo Python de experimentos.'
    q=ler_json(REG/'qualificacao.json');assert q['situacao']=='aprovado'
    assert q['fontes']==fontes()
    testes=ler_json(REG/'testes.json');assert testes['codigo']==0 and testes['fontes']==q['fontes']
    f0=ler_json(ORIGEM/'congelamento.json');conferir_arquivos(RAIZ,f0['fontes'])
    assert ler_json(ORIGEM/'finalista.json')['receita']==ASTRA
    protegidos=ler_json(RAIZ/'registros/busca_astra/preservacao_antes.json')['arquivos'].copy()
    for arquivo in ORIGEM.rglob('*'):
        if arquivo.is_file():protegidos[arquivo.relative_to(RAIZ).as_posix()]=sha256(arquivo)
    print('Conferindo preservacao de',len(protegidos),'arquivos',flush=True)
    conferir_arquivos(RAIZ,protegidos)
    salvar_json(REG/'preservacao_antes.json',{'utc':agora(),'arquivos':protegidos})
    pub=ler_json(ORIGEM/'publicacao.json');d=RAIZ/pub['pasta']
    assert sha256(d/'manifesto.json')==pub['manifesto_sha256']
    conferir_arquivos(d,ler_json(d/'manifesto.json')['arquivos'])
    herancas={}
    for item in grade():
        if item['tipo']!='crua':continue
        b,s=item['bloco'],item['seed'];a=ORIGEM/'final/candidata'/f'{b}_{s}'
        m=ler_json(a/'conclusao.json');conferir_arquivos(a,m['arquivos'])
        r=ler_json(a/'resultado.json');assert r['receita']==ASTRA and r['recarga_exata']
        herancas[f'{b}_{s}']={'pasta':a.relative_to(RAIZ).as_posix(),'conclusao_sha256':sha256(a/'conclusao.json')}
    ancoras={}
    caminhos=[ORIGEM/'congelamento.json',ORIGEM/'finalista.json',ORIGEM/'publicacao.json',
              d/'manifesto.json',d/'resultados.json',
              RAIZ/f0['candles']['pasta']/'manifesto.json',
              RAIZ/'dados/experimentos/backtest_carteira_8ec8a66648313caa48e3/congelamento.json',
              RAIZ/'dados/mercado/binance_spot/449aab6c79dbf88aa625/manifesto.json']
    for a in caminhos:ancoras[a.relative_to(RAIZ).as_posix()]=sha256(a)
    contrato={'configuracao':ler_json(RAIZ/'configuracoes/comparacao_astra_crua_001.json'),
        'fontes':q['fontes'],'ambiente_cuda':q['ambiente'],'grade':grade(),'herancas':herancas,
        'publicacao_origem':pub,'ancoras':ancoras,'preservacao_sha256':sha256(REG/'preservacao_antes.json'),
        'qualificacao':{'arquivo':(REG/'qualificacao.json').relative_to(RAIZ).as_posix(),'sha256':sha256(REG/'qualificacao.json')},
        'testes_sha256':sha256(REG/'testes.json')}
    codigo=identidade(contrato)[:20];p=RAIZ/f'dados/experimentos/comparacao_astra_crua_{codigo}';p.mkdir(parents=True,exist_ok=False)
    for nome in contrato['fontes']:
        dest=p/'fontes'/nome;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(RAIZ/nome,dest)
    salvar_json(p/'congelamento.json',dict(contrato,id=codigo,utc=agora()))
    ptr={'id':codigo,'pasta':p.relative_to(RAIZ).as_posix(),'congelamento_sha256':sha256(p/'congelamento.json')}
    auth={'utc':agora(),'execucao':ptr,'pedido':'comparar de forma justa a candidata do Astra com o OHLCV cru + Huber, usando o mesmo executor, os mesmos dados e oito seeds; pode começar',
          'orcamento':'32principais crus +1controle cru +1controle de heranca Astra =34ajustes;32Astra herdados;192simulacoes novas+216herdadas.',
          'busca_adicional':False,'promocao_automatica':False}
    salvar_json(p/'autorizacao.json',auth);salvar_json(REG/'autorizacao.json',auth)
    salvar_json(REG/'execucao.json',ptr);salvar_json(REG/'estado.json',{'utc':agora(),'situacao':'preparado_autorizado','execucao':ptr})
    print(ptr,flush=True)

def estado(p,ptr,fase,jobs):
    q={'utc':agora(),'situacao':'executando','fase':fase,'execucao':ptr,
       'ajustes_iniciados':len(jobs),'ajustes_concluidos':sum(j['status']=='concluido' for j in jobs),
       'total_novos':34,'principais_novos':32,'principais_herdados':32}
    salvar_json(p/'progresso.json',q);salvar_json(REG/'estado.json',q)

def fechar(p,ptr):
    conferir_execucao(p,ptr)
    assert (p/'publicacao.json').exists()
    assert len(ler_json(p/'ajustes.json'))==34 and all(j['status']=='concluido' for j in ler_json(p/'ajustes.json'))
    conferir_arquivos(RAIZ,ler_json(REG/'preservacao_antes.json')['arquivos'])
    f={'utc':agora(),'situacao':'concluido_conferido','execucao':ptr,'novos_ajustes':34,
       'principais_novos':32,'principais_herdados':32,'simulacoes_novas':192,'simulacoes_herdadas':216,
       'preservacao_conferida':True,'promocao_automatica':False,'retrospectiva':True}
    salvar_json(p/'fechamento.json',f);salvar_json(REG/'fechamento.json',f)
    salvar_json(REG/'estado.json',f);salvar_json(p/'progresso.json',f)

def executar(publicacao_apenas=False):
    import msvcrt
    ptr=ler_json(REG/'execucao.json');p=RAIZ/ptr['pasta'];conferir_execucao(p,ptr)
    if publicacao_apenas:
        assert (p/'processo.json').exists() and not ler_json(p/'processo.json')['ativo']
        assert not (p/'publicacao.json').exists(),'Publicacao existente; nao repetir.'
    else:assert not (p/'processo.json').exists(),'Execucao ja iniciada; nunca retomar automaticamente.'
    with (REG/'coordenador.lock').open('a+b') as lock:
        lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        proc={'ativo':True,'pid':os.getpid(),'host':socket.gethostname(),'utc':agora(),'publicacao_apenas':publicacao_apenas}
        processo=p/('processo_publicacao.json' if publicacao_apenas else 'processo.json');salvar_json(processo,proc)
        try:
            jobs=[] if not publicacao_apenas else ler_json(p/'ajustes.json')
            if publicacao_apenas:assert len(jobs)==34 and all(j['status']=='concluido' for j in jobs)
            inicio=time.time()
            for n,item in ([] if publicacao_apenas else enumerate(grade(),1)):
                conferir_execucao(p,ptr)
                if (REG/'PARAR').exists():raise InterruptedError('Parada solicitada entre ajustes.')
                if time.time()-inicio>12*3600:raise TimeoutError('Prazo12h; preservar sem retomada automatica.')
                dest=p/item['tipo']/f"{item['bloco']}_{item['seed']}"
                job={'numero':n,'execucao':ptr,'item':item,'destino':dest.relative_to(RAIZ).as_posix(),'limite_segundos':2700}
                pedido=p/'pedidos'/f'{n:03}.json';salvar_json(pedido,job)
                jobs.append(dict(job,status='iniciado'));salvar_json(p/'ajustes.json',jobs)
                estado(p,ptr,f"{item['tipo']}/{item['bloco']}/{item['seed']}",jobs)
                unix='/mnt/'+RAIZ.drive[0].lower()+str(RAIZ)[2:].replace('\\','/')
                cmd=['wsl','-d','Ubuntu','--cd',unix,'--','/home/murilorfm/.venvs/cc/bin/python','-B','-u','-m',
                     'experimentos.comparacao_astra_crua.worker',pedido.relative_to(RAIZ).as_posix()]
                with pedido.with_suffix('.log').open('w',encoding='utf-8') as log:
                    child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                    salvar_json(p/'worker_windows.json',{'ativo':True,'pid':child.pid,'numero':n,'utc':agora()})
                    codigo=child.wait(timeout=3000)
                salvar_json(p/'worker_windows.json',{'ativo':False,'pid':child.pid,'codigo':codigo,'utc':agora()})
                assert codigo==0,f'Falha no ajuste{n}; consultar logs, sem repeticao.'
                conferir_arquivos(dest,ler_json(dest/'conclusao.json')['arquivos'])
                if item['tipo'].startswith('controle'):
                    from experimentos.busca_astra.ciclo import controle_cpu
                    origem=ORIGEM/'final/candidata/B1_42' if item['tipo']=='controle_astra' else p/'crua/B1_42'
                    salvar_json(p/(item['tipo']+'.json'),controle_cpu(origem,dest))
                jobs[-1]['status']='concluido';salvar_json(p/'ajustes.json',jobs)
                print('CONCLUIDO',n,'/34',item['tipo'],item['bloco'],item['seed'],flush=True)
            estado(p,ptr,'publicacao',jobs)
            from .publicacao import publicar
            publicar(p,ptr);fechar(p,ptr)
        except BaseException:
            incidente={'utc':agora(),'situacao':'interrompido','execucao':ptr,'erro':traceback.format_exc(),
                'retomada_automatica':False,'aviso':'Em timeout, conferir PID Linux: wrapper pode continuar vivo.'}
            salvar_json(p/('incidente_publicacao.json' if publicacao_apenas else 'incidente.json'),incidente)
            salvar_json(REG/'estado.json',incidente);raise
        finally:salvar_json(processo,dict(proc,ativo=False,fim=agora()))
