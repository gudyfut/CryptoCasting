"""Coordenador Windows: orçamento único, propostas isoladas, CUDA sequencial."""
import os
import sys
import shutil
import socket
import subprocess
import time
import traceback
from pathlib import Path
import numpy as np
from infraestrutura.artefatos import RAIZ,agora,ler_json,salvar_json,sha256,identidade,conferir_arquivos
from .contrato import REG,CFG,SEEDS,FINAIS,configuracao,ancoras,validar_proposta,score,selecionar,completo
from .metricas import conferir_ajuste,controle

class OrcamentoEncerrado(RuntimeError):pass

def fontes():
    arquivos={}
    # Verificar fontes encerradas contra seus recibos, não aceitar hashes novos.
    for registro in ['busca_astra','comparacao_astra_crua','revisao_operacional']:
        ptr=ler_json(RAIZ/f'registros/{registro}/execucao.json');p=RAIZ/ptr['pasta']
        assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
        f=ler_json(p/'congelamento.json');f=f.get('assinatura',f)
        conferir_arquivos(RAIZ,f['fontes']);arquivos.update(f['fontes'])
    for pasta in ['experimentos/busca_astra_002','tests_busca_astra_002']:
        arquivos.update({p.relative_to(RAIZ).as_posix():sha256(p) for p in (RAIZ/pasta).rglob('*.py')})
    for nome in ['configuracoes/busca_astra_002.json','docs/protocolo_busca_astra_002.md']:
        arquivos[nome]=sha256(RAIZ/nome)
    return arquivos

def preparar(qualificacao):
    assert not (REG/'execucao.json').exists(), 'Preparação já existente.'
    q=ler_json(qualificacao);fs=fontes();assert q['situacao']=='aprovado' and q['fontes']==fs
    qa=ler_json(REG/'qualificacao_agente/conferencia.json');assert qa['sem_ferramentas']
    testes=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','discover','-s','tests_busca_astra_002','-v'],
        cwd=RAIZ,capture_output=True,text=True,encoding='utf-8')
    (REG/'testes_preparacao.log').write_text(testes.stdout+testes.stderr,encoding='utf-8')
    assert testes.returncode==0, 'Testes de preparação reprovados.'
    antigo=ler_json(RAIZ/'registros/revisao_operacional/preservacao_antes.json')['arquivos']
    conferir_arquivos(RAIZ,antigo)
    fptr=ler_json(RAIZ/'registros/revisao_operacional/execucao.json');fp=RAIZ/fptr['pasta']
    ofe=ler_json(RAIZ/'registros/revisao_operacional/estado.json');assert ofe['situacao']=='concluido_conferido'
    assert sha256(fp/'publicacao/manifesto.json')==ofe['publicacao_sha256']
    pm=ler_json(fp/'publicacao/manifesto.json');conferir_arquivos(fp/'publicacao',pm['arquivos']);conferir_arquivos(fp,pm['carteiras'])
    for nome in pm['carteiras']:
        mp=fp/nome;conferir_arquivos(mp.parent,ler_json(mp)['arquivos'])
    antigos=dict(antigo)
    antigos.update({p.relative_to(RAIZ).as_posix():sha256(p) for p in fp.rglob('*') if p.is_file()})
    salvar_json(REG/'preservacao_antes.json',{'utc':agora(),'arquivos':antigos})
    candles='dados/mercado/candles/93509a1b06b19103ac1c/BTCUSDT.parquet'
    cli=subprocess.check_output(['cmd','/c','codex','--version'],text=True).strip()
    base={'configuracao':configuracao(),'fontes':fs,'qualificacao':str(Path(qualificacao).resolve().relative_to(RAIZ).as_posix()),
        'qualificacao_sha256':sha256(qualificacao),'qualificacao_agente_sha256':sha256(REG/'qualificacao_agente/conferencia.json'),
        'testes_sha256':sha256(REG/'testes_preparacao.log'),'ambiente_cuda':q['ambiente'],'versao_cli':cli,'candles':{candles:sha256(RAIZ/candles)},
        'operacional':fptr,'preservacao_sha256':sha256(REG/'preservacao_antes.json'),
        'heranca_final':{'ajustes_herdados':0,'ajustes_novos_maximos':197,'motivo':'Reestimar as duas ancoras no mesmo executor; nenhuma equivalencia presumida.'}}
    codigo=identidade(base)[:20];p=RAIZ/'dados/experimentos'/f'busca_astra_002_{codigo}';p.mkdir(parents=True,exist_ok=False)
    for nome in ['qualificacao_agente','inicio_preparo.json']:
        origem=REG/nome
        if origem.is_dir():shutil.copytree(origem,p/nome)
        elif origem.exists():shutil.copyfile(origem,p/nome)
    for n in fs:
        dest=p/'fontes'/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(RAIZ/n,dest)
    salvar_json(p/'congelamento.json',dict(base,id=codigo,utc=agora()))
    ptr={'id':codigo,'pasta':p.relative_to(RAIZ).as_posix(),'congelamento_sha256':sha256(p/'congelamento.json')}
    aut={'utc':agora(),'execucao':ptr,'texto_usuario':'arrume tudo e já pode começar o processo. Vou deixar o notebook ligado',
        'escopo':'Protocolo busca002, até197ajustes/12consultas/800carteiras/24h, sem API paga ou expansão automática.'}
    salvar_json(p/'autorizacao.json',aut);salvar_json(REG/'autorizacao.json',aut);salvar_json(REG/'execucao.json',ptr)
    salvar_json(REG/'estado.json',{'situacao':'preparado_autorizado','execucao':ptr,'utc':agora()})
    print(ptr,flush=True)

class Coordenador:
    def __init__(self,p,ptr,f):
        self.p,self.ptr,self.f=p,ptr,f;self.jobs=[];self.receitas=ancoras();self.rows={k:[] for k in self.receitas}
        self.candidatas=[];self.rejeicoes=[];self.consultas=1 # qualificação real do agente também consome orçamento
        self.inicio=ler_json(REG/'inicio_preparo.json')['inicio_timestamp'];self.prazo=self.inicio+24*3600
        self.fase='desenvolvimento';self.fhash=None;self.propostas=[]
        for k,r in self.receitas.items():salvar_json(p/'receitas'/f'{k}.json',r)
        salvar_json(p/'ajustes.json',[]);salvar_json(p/'orcamento.json',{'inicio_timestamp':self.inicio,'prazo_timestamp':self.prazo,'teto_ajustes':197,'consultas_qualificacao':1})

    def checar(self):
        assert sha256(self.p/'congelamento.json')==self.ptr['congelamento_sha256']
        conferir_arquivos(RAIZ,self.f['fontes'])
        if (REG/'PARAR').exists():raise OrcamentoEncerrado('Parada humana: não iniciar próximos ajustes.')
        if time.time()>=self.prazo:raise OrcamentoEncerrado('Prazo global24h encerrado.')

    def estado(self,fase,**extra):
        v={'utc':agora(),'situacao':'executando','fase':fase,'execucao':self.ptr,'ajustes_iniciados':len(self.jobs),
            'ajustes_concluidos':sum(x['status']=='concluido' for x in self.jobs),'teto_ajustes':197,
            'candidatas':len(self.candidatas),'consultas_astra':self.consultas,'prazo_timestamp':self.prazo,**extra}
        salvar_json(self.p/'progresso.json',v);salvar_json(REG/'estado.json',v)

    def reserva(self,n,hora):
        tempos=[j['segundos_totais'] for j in self.jobs if j['status']=='concluido']
        # Estimativa conservadora, não reserva artificial de45min para cada ajuste.
        custo=max(360.,float(np.quantile(tempos,.9))*1.5) if tempos else 600.
        return time.time()+n*custo<min(self.prazo,self.inicio+hora*3600)

    def ajuste(self,nome,b,seed,grupo='desenvolvimento',eh_controle=False):
        self.checar();assert len(self.jobs)<197
        limite_fase=self.inicio+(22 if b.startswith('B') else 14)*3600
        if time.time()+2700>min(limite_fase,self.prazo):raise OrcamentoEncerrado('Reserva insuficiente para iniciar ajuste completo.')
        r=self.receitas[nome];dest=self.p/grupo/nome/f'{b}_{seed}'
        assert not dest.exists(), 'Ajuste existente: não repetir.'
        q={'execucao':self.ptr,'numero':len(self.jobs)+1,'receita_id':nome,'receita':r,'bloco':b,'seed':seed,
            'destino':dest.relative_to(RAIZ).as_posix(),'controle':eh_controle,'limite_segundos':2700,
            'prazo_timestamp':min(limite_fase,self.prazo),'finalista_sha256':self.fhash}
        pedido=self.p/'pedidos'/f'{q["numero"]:03}.json';salvar_json(pedido,q)
        self.jobs.append(dict(q,status='iniciado'));salvar_json(self.p/'ajustes.json',self.jobs)
        self.estado(self.fase,atual={'receita':nome,'bloco':b,'seed':seed,'controle':eh_controle})
        cmd=['wsl','-d','Ubuntu','--cd','/mnt/c/Users/MuriloRFM/Documents/GitHub/CryptoCasting','--',
             '/home/murilorfm/.venvs/cc/bin/python','-B','-u','-m','experimentos.busca_astra_002.worker',pedido.relative_to(RAIZ).as_posix()]
        log=self.p/'logs'/f'{q["numero"]:03}.log';log.parent.mkdir(exist_ok=True);inicio=time.monotonic()
        with log.open('w',encoding='utf-8') as out:
            proc=subprocess.Popen(cmd,cwd=RAIZ,stdout=out,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            salvar_json(self.p/'worker_windows.json',{'pid':proc.pid,'utc':agora(),'pedido':q,'ativo':True})
            # Não matar apenas o wrapper: em timeout, interromper coordenador e exigir inspeção WSL.
            rc=proc.wait(timeout=3000)
        salvar_json(self.p/'worker_windows.json',{'pid':proc.pid,'utc':agora(),'ativo':False,'codigo':rc})
        self.jobs[-1].update(status='falhou' if rc else 'concluido',segundos_totais=time.monotonic()-inicio)
        salvar_json(self.p/'ajustes.json',self.jobs)
        if rc:raise RuntimeError(f'Ajuste {q["numero"]} falhou; incidente e log preservados, sem repetição automática.')
        rr,a=conferir_ajuste(dest);parte='teste' if b.startswith('B') else 'comparacao';m=a['partes'][parte]
        linha={'id':nome,'bloco':b,'seed':seed,'metricas':m['modelo'],'media_constante':m['media_constante'],
            'diario_00utc':m['diario_00utc'],'parametros':rr['parametros'],'epoca':rr['epoca'],'segundos':rr['segundos']}
        if not eh_controle and not b.startswith('B'):
            self.rows[nome].append(linha);salvar_json(self.p/'desenvolvimento.json',self.rows)
        return linha

    def contexto(self,contraste=False):
        return {'fase':'contraste' if contraste else 'busca','recortes':configuracao()['recortes'],'receitas':self.receitas,
            'historico':[r for rows in self.rows.values() for r in rows],'rejeicoes':self.rejeicoes,
            'instrucao':'Remover um fator de combinação promissora; se impossível propor mudança local ainda não testada, ou encerrar.' if contraste else 'Propor hipótese local útil com base nas evidências S, ou encerrar.'}

    def executar(self):
        for nome in self.receitas:
            self.ajuste(nome,'S1',42)
            if nome=='A0_C05':
                self.ajuste(nome,'S1',42,'controles/desenvolvimento',True)
                salvar_json(self.p/'controle_desenvolvimento.json',controle(self.p/'desenvolvimento'/nome/'S1_42',self.p/'controles/desenvolvimento'/nome/'S1_42'))
            for b in ['S1','S2','S3']:
                for s in SEEDS[:2]:
                    if (b,s)!=('S1',42):self.ajuste(nome,b,s)
        for i in range(1,13):
            if not self.reserva(6,11):break
            nome=f'N{i:02}'
            if i<=4:
                fator=['momentum','volatilidade','volume_relativo','pooling'][i-1]
                p={'acao':'experimentar','pai':'A0_C05','fator':fator,'valor':'media' if i==4 else True,
                    'mecanismo':'Ablação inicial predefinida no protocolo.','metrica_esperada':'MSE/Naive nos três S.','risco':'Informação extra pode sobreajustar.','custo':'Seis ajustes.'}
            else:
                p=None
                while self.consultas<12 and self.reserva(6,11):
                    from .agente import consultar
                    self.consultas+=1;self.estado('consulta_astra',consulta=self.consultas)
                    resp=consultar(self.p/'consultas'/f'{self.consultas:02}',self.contexto(i>=11),versao_cli=self.f['versao_cli'],
                        limite_segundos=min(1800,int(self.inicio+11*3600-time.time())))
                    try:validar_proposta(resp,self.receitas)
                    except (AssertionError,ValueError,TypeError) as e:
                        self.rejeicoes.append({'consulta':self.consultas,'motivo':str(e)});salvar_json(self.p/'rejeicoes.json',self.rejeicoes);continue
                    p=resp;break
                if p is None:break
            r=validar_proposta(p,self.receitas)
            self.propostas.append({'id':nome,'proposta':p,'utc':agora()});salvar_json(self.p/'propostas.json',self.propostas)
            if r is None:break
            self.receitas[nome]=r;self.rows[nome]=[];self.candidatas.append(nome)
            salvar_json(self.p/'receitas'/f'{nome}.json',r)
            for b in ['S1','S2','S3']:
                for s in SEEDS[:2]:self.ajuste(nome,b,s)
        if not self.candidatas:return self.encerrar('encerrado_sem_triagem','Nenhuma candidata completa dentro do orçamento.')
        top=sorted(self.candidatas,key=lambda n:(score(self.rows[n],SEEDS[:2]),n))[:3]
        salvar_json(self.p/'promovidas.json',{'ids':top,'criterio':'Q com6ajustes completos; desempateID'})
        self.fase='reforco_selecao'
        for nome in [*ancoras(),*top]:
            for b in ['S1','S2','S3']:self.ajuste(nome,b,2026)
        sel=selecionar({n:self.rows[n] for n in top},{n:self.rows[n] for n in ancoras()})
        salvar_json(self.p/'selecao_receita.json',sel)
        if sel['escolhida'] is None:return self.encerrar('concluido_sem_finalista','Nenhuma candidata cumpriu todos os critérios fixos; resultado negativo válido.')
        nome=sel['escolhida'];final={'utc':agora(),'id':nome,'receita':self.receitas[nome],'selecao':sel,'sem_consulta_testes':True}
        salvar_json(self.p/'finalista.json',final);self.fhash=sha256(self.p/'finalista.json')
        # Encerrou definitivamente a busca: daqui em diante nenhum prompt ao Astra.
        if not self.reserva(97,22):return self.encerrar('final_nao_iniciada_por_orcamento','Candidata congelada, mas reserva insuficiente para final completa.')
        self.fase='avaliacao_final';self.receitas['candidata']=self.receitas[nome]
        salvar_json(self.p/'receitas/candidata.json',self.receitas[nome])
        self.ajuste('candidata','B1',42,'final')
        self.ajuste('candidata','B1',42,'controles/final',True)
        salvar_json(self.p/'controle_final.json',controle(self.p/'final/candidata/B1_42',self.p/'controles/final/candidata/B1_42'))
        for b in FINAIS:
            for n in ['candidata',*ancoras()]:
                for s in SEEDS:
                    if (b,n,s)!=('B1','candidata',42):self.ajuste(n,b,s,'final')
        self.estado('publicacao_final')
        from .publicacao import publicar
        publicar(self.p,self.prazo)
        return self.encerrar('concluido_conferido','Avaliação final e operacional completas; sem promoção automática.')

    def encerrar(self,status,motivo):
        conferir_arquivos(RAIZ,self.f['fontes'])
        assert sha256(REG/'preservacao_antes.json')==self.f['preservacao_sha256']
        conferir_arquivos(RAIZ,ler_json(REG/'preservacao_antes.json')['arquivos'])
        v={'utc':agora(),'situacao':status,'execucao':self.ptr,'motivo':motivo,'ajustes_concluidos':sum(j['status']=='concluido' for j in self.jobs),
            'candidatas':len(self.candidatas),'consultas_astra':self.consultas,'preservacao_conferida':True,'retrospectivo':True,'promocao_automatica':False}
        salvar_json(self.p/'fechamento.json',v);salvar_json(REG/'estado.json',v);salvar_json(self.p/'progresso.json',v)
        (self.p/'relatorio.md').write_text('# Busca Astra002\n\n'+motivo+'\n\nEstado: `'+status+'`.\n\nEvidências: desenvolvimento.json, propostas.json, selecao_receita.json (se alcançada), controles e publicacao/resultados.json (se final completa).\n',encoding='utf-8')
        return v

def executar():
    import msvcrt
    ptr=ler_json(REG/'execucao.json');p=RAIZ/ptr['pasta'];f=ler_json(p/'congelamento.json')
    assert not (p/'processo.json').exists(), 'Ciclo já iniciado; inspeção necessária, nunca repetir.'
    assert sha256(p/'congelamento.json')==ptr['congelamento_sha256'] and ler_json(p/'autorizacao.json')['execucao']==ptr
    conferir_arquivos(p/'fontes',f['fontes']);conferir_arquivos(RAIZ,f['candles'])
    with (REG/'coordenador.lock').open('a+b') as lock:
        lock.write(b'0');lock.flush();lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        salvar_json(p/'processo.json',{'ativo':True,'pid':os.getpid(),'host':socket.gethostname(),'utc':agora()})
        try:
            c=Coordenador(p,ptr,f);return c.executar()
        except BaseException:
            v={'utc':agora(),'situacao':'interrompido','execucao':ptr,'erro':traceback.format_exc(),'retomada_automatica':False}
            salvar_json(p/'incidente.json',v);salvar_json(REG/'estado.json',v);raise
        finally:salvar_json(p/'processo.json',{'ativo':False,'pid':os.getpid(),'host':socket.gethostname(),'utc':agora()})
