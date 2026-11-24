"""Coordenador Windows limitado, com processos WSL exclusivos e registros imutáveis."""
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
import traceback
import numpy as np
from infraestrutura.artefatos import RAIZ,agora,ler_json,salvar_json,sha256,identidade,conferir_arquivos
from .receitas import proposta,iniciais,validar,propor

REG=RAIZ/'registros/operacional_futuros'
PYLIN='/home/murilorfm/.venvs/cc/bin/python'
RAIZLIN='/mnt/c/Users/MuriloRFM/Documents/GitHub/CryptoCasting'


class PrazoEncerrado(RuntimeError): pass


def fontes():
    pastas=['experimentos/operacional_futuros','simulacao_operacoes/operacional','tests_operacional_futuros',
            'entradas_modelo','modelos','treinamento','avaliacao','infraestrutura']
    r={p.relative_to(RAIZ).as_posix():sha256(p) for pasta in pastas for p in (RAIZ/pasta).rglob('*.py')}
    for nome in ['docs/desenho_operacional_futuros.md','configuracoes/operacional_futuros_001_proposta.json',
                 'registros/operacional_futuros/goal_noturno.txt']:
        r[nome]=sha256(RAIZ/nome)
    return r


def preservar():
    mapa=ler_json(REG/'organizacao/preservacao_antes.json')
    chave=next(k for k,v in mapa.items() if isinstance(v,dict) and len(v)>100)
    conferir_arquivos(RAIZ,mapa[chave])
    return mapa[chave]


def preparar(qualificacao):
    if (REG/'execucao.json').exists(): raise FileExistsError('Execução já preparada; não sobrescrever.')
    q=ler_json(qualificacao)
    if q['status']!='aprovado' or q['fontes']!=fontes(): raise ValueError('Qualificação/fontes divergentes.')
    sessao=ler_json(REG/'sessao_goal.json');antes=preservar()
    dados={}
    for nome in ['registros/operacional_futuros/dados/execucao.json','registros/mercado_futuros/execucao.json']:
        ptr=ler_json(RAIZ/nome);p=RAIZ/ptr['pasta']
        if sha256(p/'manifesto.json')!=ptr['manifesto_sha256']: raise ValueError('Dados alterados.')
        m=ler_json(p/'manifesto.json');conferir_arquivos(p,m['arquivos'])
        dados[nome]=ptr
    base={'fontes':fontes(),'proposta':proposta(),'qualificacao':str(Path(qualificacao).relative_to(RAIZ)),
        'qualificacao_sha256':sha256(qualificacao),'dados':dados,'sessao':sessao,
        'autorizacao':{'treinamento':True,'busca':True,'backtest':True,'conta_real':False,'api_paga':False,
                      'texto':sessao['autorizacao_recebida']},'preservacao':antes,
        'tolerancia_controle_real_absoluta':1e-5}
    codigo=identidade(base)[:20];p=RAIZ/'dados/experimentos'/('operacional_futuros_'+codigo)
    p.mkdir(parents=True,exist_ok=False)
    for n in base['fontes']:
        d=p/'fontes'/n;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(RAIZ/n,d)
    salvar_json(p/'congelamento.json',dict(base,id=codigo,utc=agora()))
    salvar_json(p/'receitas.json',iniciais());salvar_json(p/'ajustes.json',[])
    ptr={'id':codigo,'pasta':p.relative_to(RAIZ).as_posix(),'congelamento_sha256':sha256(p/'congelamento.json')}
    salvar_json(REG/'execucao.json',ptr)
    sessao.update(execucao=ptr,vinculo_execucao_pendente=False,situacao='preparado_autorizado')
    salvar_json(REG/'sessao_goal.json',sessao)
    salvar_json(REG/'estado.json',{'situacao':'preparado_autorizado','utc':agora(),'execucao':ptr})
    return ptr


def conferir_controle(a,b,destino):
    a,b=Path(a)/'ajuste',Path(b)/'ajuste';ra=ler_json(a/'conclusao.json');rb=ler_json(b/'conclusao.json')
    if ra['epoca']!=rb['epoca']: raise ValueError('Controle escolheu outra época.')
    desvios={}
    for fase in ('validacao','calibracao','comparacao'):
        x=np.load(a/(fase+'.npz'));y=np.load(b/(fase+'.npz'))
        for nome in x.files:
            if nome=='previsoes':
                np.testing.assert_allclose(x[nome],y[nome],rtol=0,atol=1e-5)
                desvios[fase]=float(np.max(abs(x[nome]-y[nome])))
            elif not np.array_equal(x[nome],y[nome]): raise ValueError('Controle mudou dados/origens.')
    salvar_json(destino,{'aprovado':True,'epoca':ra['epoca'],'tolerancia_absoluta':1e-5,'desvios':desvios,
        'controles_fora_das_medias':True,'recarga_individual_exata':True})


class Ciclo:
    def __init__(self):
        self.ptr=ler_json(REG/'execucao.json');self.p=RAIZ/self.ptr['pasta']
        if sha256(self.p/'congelamento.json')!=self.ptr['congelamento_sha256']: raise ValueError('Congelamento alterado.')
        self.f=ler_json(self.p/'congelamento.json');conferir_arquivos(RAIZ,self.f['fontes'])
        self.cfg=self.f['proposta'];self.receitas=ler_json(self.p/'receitas.json');self.jobs=[];self.resultados={}
        self.consultas=1;self.logicas=0;self.fisicas=0
        self.prazo=datetime.fromisoformat(self.f['sessao']['limite_novos_trabalhos_utc']).timestamp()
        self.m=None;self.h=None

    def atualizar(self,situacao,**extras):
        r={'utc':agora(),'situacao':situacao,'execucao':self.ptr,'ajustes_iniciados':len(self.jobs),
           'ajustes_concluidos':sum(j['status']=='concluido' for j in self.jobs),
           'consultas_proponente':self.consultas,'receitas':len(self.receitas),'carteiras_logicas':self.logicas,
           'carteiras_fisicas':self.fisicas,'limite_novos_trabalhos_utc':self.f['sessao']['limite_novos_trabalhos_utc'],**extras}
        salvar_json(self.p/'progresso.json',r);salvar_json(REG/'estado.json',r)

    def tempo(self,reserva=3000):
        if time.time()+reserva>=self.prazo: raise PrazoEncerrado('Reserva de fechamento preservada; não iniciar nova unidade.')

    def ajustar(self,nome,recorte,seed,controle=False):
        for j in self.jobs:
            if (j['receita_id'],j['recorte']['id'],j['seed'],j['controle'])==(nome,recorte['id'],seed,controle):
                if j['status']!='concluido': raise RuntimeError('Tentativa existente incompleta não será repetida.')
                return RAIZ/j['pasta']
        self.tempo()
        if len(self.jobs)>=185: raise RuntimeError('Orçamento de ajustes esgotado.')
        conferir_arquivos(RAIZ,self.f['fontes'])
        ident=f'{len(self.jobs)+1:03d}_{nome}_{recorte["id"]}_{seed}'+('_controle' if controle else '')
        d=self.p/'ajustes'/ident;d.mkdir(parents=True,exist_ok=False)
        job={'id':ident,'execucao_pasta':self.ptr['pasta'],'execucao_id':self.ptr['id'],
            'receita_id':nome,'receita':self.receitas[nome],'recorte':recorte,'seed':seed,'controle':controle,
            'pasta':d.relative_to(RAIZ).as_posix(),'status':'iniciado'}
        self.jobs.append(job);salvar_json(self.p/'ajustes.json',self.jobs);salvar_json(d/'job.json',job)
        self.atualizar('treinando',job_atual=ident)
        cmd=['wsl','-d','Ubuntu','--cd',RAIZLIN,PYLIN,'-B','-m','experimentos.operacional_futuros.worker',job['pasta']]
        with (d/'stdout.log').open('w',encoding='utf-8') as out,(d/'stderr.log').open('w',encoding='utf-8') as err:
            proc=subprocess.Popen(cmd,cwd=RAIZ,stdout=out,stderr=err,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            salvar_json(d/'processo_windows.json',{'pid':proc.pid,'host':socket.gethostname(),'utc':agora(),'comando':cmd})
            try: proc.wait(timeout=3000)
            except subprocess.TimeoutExpired:
                linux=ler_json(d/'processo_linux.json')
                codigo="import os,sys,json,signal;from pathlib import Path;r=json.loads(sys.argv[1]);p=Path('/proc')/str(r['pid']);assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==r['boot'];c=(p/'cmdline').read_bytes().decode().replace(chr(0),' ');assert 'experimentos.operacional_futuros.worker' in c and sys.argv[2] in c;os.kill(r['pid'],signal.SIGTERM)"
                subprocess.run(['wsl','-d','Ubuntu',PYLIN,'-c',codigo,json.dumps(linux),job['pasta']],check=True)
                proc.wait(timeout=60)
                raise TimeoutError('Worker excedeu50min; encerrado PID Linux conferido, sem retomada.')
        if proc.returncode or not (d/'conferido.json').exists():
            job['status']='falha';salvar_json(self.p/'ajustes.json',self.jobs)
            raise RuntimeError('Ajuste falhou: '+ident)
        job['status']='concluido';job['conferido_sha256']=sha256(d/'conferido.json')
        salvar_json(self.p/'ajustes.json',self.jobs);self.atualizar('ajuste_concluido',job_atual=ident)
        return d

    def avaliar(self,nome,recortes,seeds,fase):
        from .avaliar import avaliar_coorte,elegibilidade
        linhas=[]
        for recorte in recortes:
            self.tempo(300)
            jobs={s:self.ajustar(nome,recorte,s) for s in seeds}
            d=self.p/'avaliacoes'/fase/nome/recorte['id']
            previsto=len(seeds)*17
            if self.logicas+previsto>3620: raise RuntimeError('Orçamento de carteiras esgotado.')
            self.logicas+=previsto;self.atualizar('avaliando',coorte=f'{fase}/{nome}/{recorte["id"]}')
            linhas.extend(avaliar_coorte(d,self.m,self.h,self.receitas[nome],recorte,jobs,seeds,nome,fase))
            self.fisicas+=previsto
        self.resultados[(fase,nome)]=linhas
        if fase!='final':
            e=elegibilidade(linhas,[b['id'] for b in recortes],seeds,fase=='reforco')
            salvar_json(self.p/'avaliacoes'/fase/nome/'elegibilidade.json',e)
            return e
        return None

    def contexto(self):
        linhas=[]
        for (fase,nome),r in self.resultados.items():
            if fase=='final': continue
            e=ler_json(self.p/'avaliacoes'/fase/nome/'elegibilidade.json')
            base=[x for x in r if x['cenario']=='base']
            linhas.append({'id':nome,'fase':fase,'recortes':['D1','D2','D3'],
                'elegivel':e['elegivel'],'motivos':e['motivos'],'medias':e['resumo']['medias'],
                'score_calmar':e['resumo']['score_calmar'],'stress2x':e['stress2x']['medias'],
                'seeds':sorted({x['seed'] for x in base}),
                'por_lado':{k:float(np.mean([x['metricas'][k] for x in base])) for k in ['pnl_compras','pnl_vendas']}})
        return linhas

    def ranquear(self,fase):
        from .avaliar import melhor
        valores={}
        for f,n in self.resultados:
            if f!=fase or n=='R0': continue
            e=ler_json(self.p/'avaliacoes'/fase/n/'elegibilidade.json')
            if e['elegivel']:
                valores[n]=(e['resumo']['score_calmar'],e['resumo']['medias']['crescimento_log_diario'],-e['giro_medio'])
        ref=ler_json(self.p/'avaliacoes'/fase/'R0/elegibilidade.json')
        if ref['elegivel']:
            score=(ref['resumo']['score_calmar'],ref['resumo']['medias']['crescimento_log_diario'],-ref['giro_medio'])
            valores={n:v for n,v in valores.items() if melhor({'R0':score,n:v})==n}
        ordem=[]
        while valores:
            n=melhor(valores);ordem.append(n);valores.pop(n)
        return ordem

    def baselines(self,recortes):
        from .avaliar import guardar,ms
        from simulacao_operacoes.operacional.motor import Politica,simular,volatilidade_horaria
        sigma=volatilidade_horaria(self.h);origens=self.h.close_time.to_numpy(np.int64)+1
        c=self.h.close.astype(float)
        tendencia=np.sign(c.ewm(span=24,adjust=False,min_periods=168).mean()-c.ewm(span=168,adjust=False,min_periods=168).mean()).to_numpy()
        for recorte in recortes:
            inicio,fim=map(ms,recorte.get('comparacao',recorte.get('avaliacao')))
            ids=np.flatnonzero((origens>=inicio)&(origens+60000<fim))
            for nome in ['caixa','comprado','vendido','tendencia']:
                for mult in [1,2,3]:
                    self.tempo(60)
                    if self.logicas>=3620: raise RuntimeError('Orçamento de carteiras esgotado.')
                    self.logicas+=1
                    r=simular(self.m,origens[ids],tendencia[ids,None],sigma[ids],'terminal',Politica(),inicio,fim,
                              deslizamento=.0005*mult,baseline=nome)
                    guardar(self.p/'baselines'/recorte['id']/nome/str(mult),r,self.m,inicio,fim,
                            {'baseline':nome,'recorte':recorte['id'],'custo':mult})
                    self.fisicas+=1

    def executar(self):
        from simulacao_operacoes.operacional.mercado import carregar
        from .agente import consultar
        if (self.p/'inicio.json').exists(): raise RuntimeError('Ciclo já iniciado; não repetir/retomar automaticamente.')
        salvar_json(self.p/'inicio.json',{'utc':agora(),'host':socket.gethostname(),'pid':os.getpid()})
        self.m,self.h=carregar();des=self.cfg['calendario']['desenvolvimento'];seeds=self.cfg['seeds']['exploracao']
        for nome in ('R0','P0'):
            a=self.ajustar(nome,des[0],42);b=self.ajustar(nome,des[0],42,True)
            conferir_controle(a,b,self.p/'controles'/f'{nome}_D1.json')
        for nome in ('R0','P0'): self.avaliar(nome,des,seeds,'exploracao')
        for numero in range(1,7):
            self.tempo();self.consultas+=1;self.atualizar('consultando_astra',consulta=self.consultas)
            r=consultar(self.p/'consultas'/str(numero),self.receitas,self.contexto())
            if r['acao']=='encerrar': break
            nome=f'C{numero:02d}';self.receitas[nome]=propor(r['pai'],r['campo'],json.loads(r['valor_json']),self.receitas)
            salvar_json(self.p/'receitas.json',self.receitas)
            salvar_json(self.p/'receitas'/f'{nome}.json',{'receita':self.receitas[nome],'proposta':r,'utc':agora()})
            self.avaliar(nome,des,seeds,'exploracao')
        self.baselines(des)
        ordem=self.ranquear('exploracao')[:2]
        salvar_json(self.p/'promocao.json',{'promovidas':ordem,'regra':'elegibilidade e comparação com R0, sem relaxar gates'})
        if not ordem: return 'concluido_sem_finalista'
        oito=self.cfg['seeds']['reforco_e_final']
        for nome in ['R0',*ordem]: self.avaliar(nome,des,oito,'reforco')
        ordem=self.ranquear('reforco')
        if not ordem: return 'concluido_sem_finalista'
        nome=ordem[0]
        self.tempo()
        salvar_json(self.p/'finalista_congelada.json',{'id':nome,'receita':self.receitas[nome],
            'referencia':self.receitas['R0'],'utc':agora(),'escolhida_sem_ler_B':True,
            'origens':'2023 desenvolvimento já consultado','retrospectiva':True})
        self.m,self.h=carregar(final=True);blocos=self.cfg['calendario']['final_retrospectiva']
        for r in ('R0',nome):
            a=self.ajustar(r,blocos[0],42);b=self.ajustar(r,blocos[0],42,True)
            conferir_controle(a,b,self.p/'controles'/f'{r}_B1.json')
        for r in ('R0',nome): self.avaliar(r,blocos,oito,'final')
        self.baselines(blocos)
        return 'concluido_final'


def executar():
    import msvcrt
    with (REG/'coordenador.lock').open('a+b') as lock:
        lock.write(b'0');lock.flush();lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        c=Ciclo();status='falha'
        try: status=c.executar()
        except PrazoEncerrado as exc:
            status='encerrado_por_prazo';salvar_json(c.p/'interrupcao_prazo.json',{'utc':agora(),'motivo':str(exc)})
        except BaseException:
            salvar_json(c.p/'incidente.json',{'utc':agora(),'erro':traceback.format_exc()})
            raise
        finally:
            conferir_arquivos(RAIZ,c.f['fontes']);preservar()
            salvar_json(c.p/'preservacao_depois.json',{'utc':agora(),'arquivos':c.f['preservacao'],'conferidos':True})
            c.atualizar(status)
            salvar_json(c.p/'encerramento.json',{'utc':agora(),'situacao':status,'publicacao_posterior_pendente':True})
