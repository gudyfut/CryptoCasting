"""Preparação e execução Linux exclusivas; nunca reabre uma execução encerrada."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import gc
import os
import shutil
import socket
import subprocess
import time
import traceback
import numpy as np
from infraestrutura.artefatos import RAIZ, ler_json, salvar_json, sha256, identidade, conferir_arquivos, agora
from .contrato import REG, CONFIG, BRACOS, FASES, configuracao, calendario, grade


def fontes():
    pacotes=['codigo/experimentos/historico_treino','testes/historico_treino','codigo/entradas_modelo','codigo/treinamento',
             'codigo/modelos','codigo/avaliacao','codigo/infraestrutura','codigo/simulacao_operacoes/operacional']
    saida={p.relative_to(RAIZ).as_posix():sha256(p) for nome in pacotes for p in (RAIZ/nome).rglob('*.py')}
    for nome in ['codigo/experimentos/operacional_futuros/avaliar.py','codigo/experimentos/operacional_futuros/ciclo.py',
                 'codigo/experimentos/operacional_futuros/receitas.py','configuracoes/operacional_futuros_001_proposta.json',
                 'configuracoes/historico_treino_001.json','docs/protocolo_historico_treino.md',
                 'docs/adr/0030-historico-acumulado-movel.md']:
        saida[nome]=sha256(RAIZ/nome)
    return saida


def conferir_ancestral(c):
    ptr=c['ancestral'];p=RAIZ/ptr['pasta']
    if sha256(p/'congelamento.json')!=ptr['congelamento_sha256']:
        raise ValueError('Ancestral alterado.')
    f=ler_json(p/'congelamento.json');conferir_arquivos(RAIZ,f['fontes'])
    if c['receita']!=ler_json(p/'receitas.json')['C06'] or c['recortes']!=f['proposta']['calendario']['desenvolvimento']:
        raise ValueError('Receita/calendário não correspondem ao ancestral.')
    if ler_json(RAIZ/'registros/operacional_futuros/estado.json')['situacao']!='concluido_sem_finalista':
        raise ValueError('Ciclo ancestral não está encerrado.')
    return p


def preparar():
    import fcntl
    from .qualificacao import sintetico, conferir_par
    from entradas_modelo.operacional_futuros import preparar as dados_preparar
    from simulacao_operacoes.operacional.mercado import carregar
    from simulacao_operacoes.operacional.motor import gerar_alvos
    REG.mkdir(parents=True,exist_ok=True)
    with (REG/'preparacao.lock').open('a+b') as lock, (RAIZ/'registros/operacional_futuros/gpu.lock').open('a+b') as gpu:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        fcntl.flock(gpu,fcntl.LOCK_EX|fcntl.LOCK_NB)
        consulta=subprocess.run(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],capture_output=True,text=True,check=True)
        if consulta.stdout.strip():raise RuntimeError('GPU ocupada durante preparação.')
        if (REG/'execucao.json').exists():raise FileExistsError('Já congelado; não preparar novamente.')
        c=configuracao();antes=fontes();antigo=conferir_ancestral(c)
        qdir=REG/('preparacao_'+agora().replace(':','').replace('+','_'))
        qdir.mkdir(exist_ok=False)
        salvar_json(REG/'estado.json',{'situacao':'qualificando','utc':agora(),'preparacao':str(qdir.relative_to(RAIZ))})
        try:
            # O recibo dos testes é vinculado às fontes antes da qualificação integrada.
            cmd=[os.sys.executable,'-B','-m','unittest','discover','-s','testes/operacional_futuros','-t','.','-v']
            for nome,comando in [('regressao',cmd),('contraste',[os.sys.executable,'-B','-m','unittest','discover','-s','testes/historico_treino','-t','.','-v'])]:
                with (qdir/(nome+'.log')).open('w') as log:
                    subprocess.run(comando,cwd=RAIZ,stdout=log,stderr=subprocess.STDOUT,check=True)
            sintetica=sintetico(qdir/'sintetico',c['receita'])
            ptr=ler_json(RAIZ/'registros/operacional_futuros/dados/execucao.json');base=RAIZ/ptr['pasta']
            if sha256(base/'manifesto.json')!=ptr['manifesto_sha256']:raise ValueError('Dados divergentes.')
            manifesto=ler_json(base/'manifesto.json');conferir_arquivos(base,manifesto['arquivos'])
            m,h=carregar(final=False);y,realizacao,motivos=gerar_alvos(m,h,*c['receita']['barreiras_payoff'])
            # Confere todos os rótulos, não apenas uma amostra, contra evidência antiga.
            job=next(j for j in ler_json(antigo/'ajustes.json') if j['receita_id']=='C06')
            z=np.load(RAIZ/job['pasta']/'contrato_alvos.npz')
            for chave,a in [('alvos',y),('realizacao_ms',realizacao),('motivos',motivos)]:
                np.testing.assert_array_equal(a,z[chave])
            coberturas={}
            for rec in c['recortes']:
                a=dados_preparar(h,c['receita'],calendario(rec,'acumulado'),y)
                b=dados_preparar(h,c['receita'],calendario(rec,'movel12'),y)
                coberturas[rec['id']]=conferir_par(a,b)
                for dados in (a,b):
                    for fase,ids in dados.indices.items():
                        if (realizacao[ids]>dados.origens_ms[ids,None]+1442*60000).any():
                            raise ValueError('Alvo ultrapassa purga.')
            if fontes()!=antes:raise ValueError('Fontes mudaram durante qualificação.')
            # Hashes de toda a execução ancestral: antes e depois, sem alterar nada.
            preservacao={x.relative_to(RAIZ).as_posix():sha256(x) for x in antigo.rglob('*') if x.is_file()}
            for x in (RAIZ/'registros/operacional_futuros').glob('*.json'):
                preservacao[x.relative_to(RAIZ).as_posix()]=sha256(x)
            qual={'status':'aprovado','utc':agora(),'fontes':antes,'sintetica':sintetica,'populacoes':coberturas,
                  'alvos_recalculados_iguais_ancestral':True,'dados':ptr,'testes':{n:sha256(qdir/n) for n in ('regressao.log','contraste.log')}}
            salvar_json(qdir/'qualificacao.json',qual)
            f={'configuracao':c,'fontes':antes,'dados':ptr,'preservacao':preservacao,
               'qualificacao':str((qdir/'qualificacao.json').relative_to(RAIZ)),
               'qualificacao_sha256':sha256(qdir/'qualificacao.json'),'autorizacao':c['autorizacao']}
            cod=identidade(f)[:20];p=RAIZ/'dados/experimentos'/('historico_treino_'+cod);p.mkdir(exist_ok=False)
            for nome in antes:
                dest=p/'fontes'/nome;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(RAIZ/nome,dest)
            np.savez_compressed(p/'alvos.npz',alvos=y,realizacao_ms=realizacao,motivos=motivos)
            f.update(id=cod,utc=agora(),alvos_sha256=sha256(p/'alvos.npz'))
            salvar_json(p/'congelamento.json',f)
            ptrnovo={'id':cod,'pasta':p.relative_to(RAIZ).as_posix(),'congelamento_sha256':sha256(p/'congelamento.json')}
            salvar_json(REG/'execucao.json',ptrnovo)
            salvar_json(REG/'autorizacao.json',{'utc':agora(),'execucao':ptrnovo,**c['autorizacao'],
                         'escopo':'18 ajustes principais+2 controles;456 carteiras;sem busca adicional'})
            salvar_json(REG/'estado.json',{'situacao':'preparado_autorizado','utc':agora(),'execucao':ptrnovo,'ajustes_previstos':20})
            print(ptrnovo,flush=True)
        except BaseException:
            salvar_json(qdir/'incidente.json',{'utc':agora(),'erro':traceback.format_exc()})
            salvar_json(REG/'estado.json',{'situacao':'falha_qualificacao','utc':agora(),'preparacao':str(qdir.relative_to(RAIZ))})
            raise


def executar():
    import fcntl
    import torch
    from entradas_modelo.operacional_futuros import preparar as dados_preparar
    from treinamento.operacional_futuros import ajustar
    from simulacao_operacoes.operacional.mercado import carregar
    from experimentos.operacional_futuros.ciclo import conferir_controle
    from .qualificacao import conferir_par
    from .avaliacao import executar as avaliar
    with (REG/'execucao.lock').open('a+b') as lock, (RAIZ/'registros/operacional_futuros/gpu.lock').open('a+b') as gpu:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gpu,fcntl.LOCK_EX|fcntl.LOCK_NB)
        consulta=subprocess.run(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],capture_output=True,text=True,check=True)
        if consulta.stdout.strip():raise RuntimeError('GPU ocupada; não duplicar.')
        ptr=ler_json(REG/'execucao.json');p=RAIZ/ptr['pasta'];f=ler_json(p/'congelamento.json')
        if sha256(p/'congelamento.json')!=ptr['congelamento_sha256']:raise ValueError('Congelamento alterado.')
        if (p/'inicio.json').exists():raise RuntimeError('Já iniciada; não repetir/retomar automaticamente.')
        if ler_json(REG/'autorizacao.json')['execucao']!=ptr or not f['autorizacao']['treinamento']:
            raise ValueError('Autorização não vinculada.')
        conferir_arquivos(RAIZ,f['fontes']);conferir_arquivos(p/'fontes',f['fontes'])
        conferir_arquivos(RAIZ,f['preservacao'])
        if sha256(p/'alvos.npz')!=f['alvos_sha256']:raise ValueError('Alvos alterados.')
        if sha256(RAIZ/f['qualificacao'])!=f['qualificacao_sha256']:raise ValueError('Qualificação alterada.')
        c=f['configuracao'];base=RAIZ/f['dados']['pasta']
        if ler_json(RAIZ/'registros/operacional_futuros/dados/execucao.json')!=f['dados']:
            raise ValueError('Ponteiro de dados alterado.')
        if sha256(base/'manifesto.json')!=f['dados']['manifesto_sha256']:raise ValueError('Manifesto de dados alterado.')
        conferir_arquivos(base,ler_json(base/'manifesto.json')['arquivos'])
        m,h=carregar(final=False);y=np.load(p/'alvos.npz')['alvos']
        proc={'pid':os.getpid(),'host':socket.gethostname(),'boot':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
              'utc':agora(),'ativo':True}
        salvar_json(p/'inicio.json',proc);salvar_json(p/'processo.json',proc)
        prazo=time.monotonic()+c['prazo_horas']*3600;jobs=[]
        def atualizar(situacao,**extras):
            v={'utc':agora(),'situacao':situacao,'execucao':ptr,'ajustes_previstos':20,
               'principais_previstos':18,'ajustes_concluidos':sum(j['status']=='concluido' for j in jobs),
               'carteiras_previstas':456,'processo':proc,**extras}
            salvar_json(p/'progresso.json',v);salvar_json(REG/'estado.json',v);print(v,flush=True)
        try:
            dados={}
            for rec in c['recortes']:
                for b in BRACOS:dados[b,rec['id']]=dados_preparar(h,c['receita'],calendario(rec,b),y)
                conferir_par(dados['acumulado',rec['id']],dados['movel12',rec['id']])
            for especificacao in grade(c):
                if time.monotonic()+c['limite_ajuste_segundos']+600>prazo:
                    raise TimeoutError('Reserva temporal esgotada; não iniciar novo ajuste.')
                conferir_arquivos(RAIZ,f['fontes'])
                j=dict(especificacao,status='iniciado');dest=p/'ajustes'/j['id'];dest.mkdir(parents=True,exist_ok=False)
                j['pasta']=dest.relative_to(RAIZ).as_posix();jobs.append(j)
                salvar_json(dest/'job.json',j);salvar_json(p/'ajustes.json',jobs);atualizar('treinando',job_atual=j['id'])
                dado=dados[j['braco'],j['recorte']['id']]
                salvar_json(dest/'contrato.json',{'calendario':calendario(j['recorte'],j['braco']),
                   'canais':dado.canais,'contexto':dado.contexto,'origens':{k:{'n':len(v),'primeira_ms':int(dado.origens_ms[v[0]]),
                   'ultima_ms':int(dado.origens_ms[v[-1]])} for k,v in dado.indices.items()}})
                vinculo={'execucao':ptr['id'],'job':j['id'],'braco':j['braco'],'recorte':j['recorte']['id'],
                         'seed':j['seed'],'controle':j['controle']}
                ajustar(dado,c['receita'],j['seed'],dest/'ajuste',vinculo,limite_segundos=c['limite_ajuste_segundos'])
                j['status']='concluido';j['conclusao_sha256']=sha256(dest/'ajuste/conclusao.json')
                salvar_json(p/'ajustes.json',jobs)
                if j['controle']:
                    principal=next(v for v in jobs if v['braco']==j['braco'] and not v['controle'])
                    conferir_controle(RAIZ/principal['pasta'],dest,p/f'controle_{j["braco"]}.json')
                gc.collect();torch.cuda.empty_cache();atualizar('ajuste_concluido',job_atual=j['id'])
            resumo=avaliar(p,c,jobs,m,h,atualizar)
            conferir_arquivos(RAIZ,f['fontes']);conferir_arquivos(RAIZ,f['preservacao'])
            arquivos={x.relative_to(p).as_posix():sha256(x) for pasta in ('ajustes','publicacao') for x in (p/pasta).rglob('*') if x.is_file()}
            salvar_json(p/'fechamento.json',{'utc':agora(),'situacao':'concluido_conferido','principais':18,'controles':2,
                'carteiras':456,'preservacao_antes_depois':True,'arquivos':arquivos,
                'controles':{b:sha256(p/f'controle_{b}.json') for b in BRACOS}})
            salvar_json(REG/'fechamento.json',{'execucao':ptr,'arquivo':str((p/'fechamento.json').relative_to(RAIZ)),
                         'sha256':sha256(p/'fechamento.json')})
            atualizar('concluido_conferido',publicacao=str((p/'publicacao').relative_to(RAIZ)),carteiras_concluidas=456)
        except BaseException:
            if jobs and jobs[-1]['status']=='iniciado':jobs[-1]['status']='falha';salvar_json(p/'ajustes.json',jobs)
            salvar_json(p/'incidente.json',{'utc':agora(),'erro':traceback.format_exc(),'retomada_automatica':False})
            atualizar('falha_preservada');raise
        finally:
            proc.update(ativo=False,encerramento_utc=agora());salvar_json(p/'processo.json',proc)
            estado=ler_json(REG/'estado.json');estado['processo']=proc
            salvar_json(REG/'estado.json',estado);salvar_json(p/'progresso.json',estado)
