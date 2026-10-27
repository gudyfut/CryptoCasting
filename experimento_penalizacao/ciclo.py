"""Execução isolada, retomável e vinculada ao estudo anterior por hashes."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout,redirect_stderr
from pathlib import Path
import fcntl
import os
import shutil
import socket
import subprocess
import sys
import traceback
import numpy as np
import pandas as pd
import torch
from previsao24.arquivos import RAIZ,agora,identidade,ler_json,salvar_json,sha256,verificar_arquivos
from previsao24.configuracao import celulas
from previsao24.dados import verificar_dataset,separar,ajustar_escalas
from previsao24.auditoria import auditar_modelo
from previsao24.execucao import tentativa
from .otimizador import descrever_grupos
from .qualificacao import executar as qualificar

PONTEIRO=RAIZ/'registros/penalizacao/execucao.json'


def hashes(caminhos):
    caminhos=sorted(set(p for p in caminhos if p.is_file()))
    with ThreadPoolExecutor(max_workers=8) as grupo:
        valores=list(grupo.map(sha256,caminhos))
    return {p.relative_to(RAIZ).as_posix():h for p,h in zip(caminhos,valores)}


def indice(pasta):
    saida={}
    for p in sorted(pasta.glob('celulas/*/tentativa_*/tentativa.json')):
        t=ler_json(p)
        if t['status']!='auditada': continue
        chave=identidade(t['celula'])[:20]
        if chave in saida: raise ValueError('Resultado auditado duplicado.')
        saida[chave]=p.parent
    return saida


def conferir_fontes(destino):
    a=ler_json(destino/'execucao.json')['assinatura']
    verificar_arquivos(RAIZ,a['fontes']); verificar_arquivos(destino/'fontes',a['fontes'])
    return a


def preparar():
    if PONTEIRO.exists():
        destino=RAIZ/ler_json(PONTEIRO)['caminho']; conferir_fontes(destino)
        return destino
    configuracao=ler_json(RAIZ/'configuracoes/penalizacao_mamba_001.json')
    base=RAIZ/'dados/experimentos'/('retorno24_'+configuracao['referencia'])
    referencia=ler_json(base/'execucao.json'); a=referencia['assinatura']; c=a['configuracao']
    if identidade(a)[:20]!=configuracao['referencia']: raise ValueError('Identidade da referência inválida.')
    verificar_arquivos(RAIZ,a['fontes']); verificar_arquivos(base/'fontes',a['fontes'])
    if c!=ler_json(RAIZ/'configuracoes/retorno24_001.json'): raise ValueError('Configuração base alterada.')
    if len(indice(base))!=832: raise ValueError('Referência incompleta.')
    dataset=verificar_dataset(RAIZ/referencia['dataset_caminho'])
    if dataset['id']!=configuracao['dataset']: raise ValueError('Dataset divergente.')
    if shutil.disk_usage(RAIZ).free<10*1024**3: raise RuntimeError('Menos de 10GB disponíveis.')
    etapa=RAIZ/'registros/penalizacao'/('preparacao_'+agora().replace(':','').replace('+','_'))
    etapa.mkdir(parents=True,exist_ok=False)
    salvar_json(etapa/'estado.json',{'status':'em_andamento','inicio_utc':agora()})
    try:
        preservados=list(base.rglob('*'))
        for prefixo in ('registros/analises','registros/auditorias'):
            preservados+=list((RAIZ/prefixo/configuracao['referencia']).rglob('*'))
        preservados += [RAIZ/p for p in a['fontes']]
        preservados += [RAIZ/'configuracoes/retorno24_001.json',RAIZ/'registros/execucao_atual.json',RAIZ/'registros/dataset_atual.json',RAIZ/'registros/exposicao_previa.json']
        preservados += list((RAIZ/'registros/qualificacao').glob('*.json'))
        antes=hashes(preservados)
        salvar_json(etapa/'preservacao_antes.json',{'utc':agora(),'referencia':configuracao['referencia'],'arquivos':antes})
        print(f'PRESERVAÇÃO {len(antes)} arquivos inventariados.',flush=True)
        for local in indice(base).values(): verificar_arquivos(local,ler_json(local/'auditoria.json')['arquivos'])
        for fase in ('desenvolvimento','avaliacao'):
            publicacao=RAIZ/'registros/analises'/configuracao['referencia']/fase
            verificar_arquivos(publicacao,ler_json(publicacao/'publicacao.json')['arquivos'])
        testes=[]
        for pasta in ('tests','tests_penalizacao'):
            processo=subprocess.run([sys.executable,'-m','unittest','discover','-s',pasta,'-v'],cwd=RAIZ,capture_output=True,text=True)
            (etapa/f'{pasta}.log').write_text(processo.stdout+processo.stderr,encoding='utf-8')
            if processo.returncode: raise RuntimeError(f'Testes falharam: {pasta}')
            testes.append({'pasta':pasta,'sha256':sha256(etapa/f'{pasta}.log')})
        qualificar(c,etapa,referencia)
        caminhos=[RAIZ/p for p in a['fontes']]
        caminhos+=list((RAIZ/'experimento_penalizacao').glob('*.py'))+list((RAIZ/'tests_penalizacao').glob('*.py'))
        caminhos+=list((RAIZ/'tests').glob('*.py'))
        caminhos += [RAIZ/'configuracoes/retorno24_001.json',RAIZ/'configuracoes/penalizacao_mamba_001.json',RAIZ/'docs/protocolo_penalizacao_mamba.md',RAIZ/'run_penalizacao.py']
        caminhos += [RAIZ/'manutencao/consolidar_resultados.py']
        assinatura={'configuracao':configuracao,'configuracao_treino':c,'referencia':configuracao['referencia'],
                    'referencia_execucao_sha256':sha256(base/'execucao.json'),'dataset':dataset['id'],
                    'dataset_manifesto_sha256':sha256(RAIZ/referencia['dataset_caminho']/'dataset.json'),
                    'fontes':hashes(caminhos),'qualificacao_sha256':sha256(etapa/'qualificacao.json'),
                    'testes':testes,'preservacao_antes_sha256':sha256(etapa/'preservacao_antes.json')}
        chave=identidade(assinatura)[:20]
        destino=RAIZ/'dados/experimentos'/('penalizacao_'+chave)
        destino.mkdir(parents=True,exist_ok=False)
        for relativo in assinatura['fontes']:
            alvo=destino/'fontes'/relativo; alvo.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(RAIZ/relativo,alvo)
        salvar_json(destino/'execucao.json',{'id':chave,'assinatura':assinatura,'inicio_utc':agora(),
                    'preparacao_caminho':etapa.relative_to(RAIZ).as_posix(),'referencia_caminho':base.relative_to(RAIZ).as_posix(),
                    'dataset_caminho':referencia['dataset_caminho'],'classificacao':'extensao_retrospectiva_periodos_expostos'})
        salvar_json(destino/'congelamento.json',{'status':'congelado','utc':agora(),'assinatura':identidade(assinatura),
                    'exposicao':configuracao['exposicao'],'regra':configuracao['regra']})
        salvar_json(PONTEIRO,{'id':chave,'caminho':destino.relative_to(RAIZ).as_posix(),'referencia':configuracao['referencia']})
        salvar_json(etapa/'estado.json',{'status':'aprovado','fim_utc':agora(),'execucao':chave})
        print(f'CONGELADO {chave}',flush=True)
        return destino
    except Exception as erro:
        salvar_json(etapa/'estado.json',{'status':'falha','fim_utc':agora(),'erro':repr(erro),'traceback':traceback.format_exc()})
        raise


def executar():
    destino=preparar(); a=conferir_fontes(destino)
    e=ler_json(destino/'execucao.json'); base=RAIZ/e['referencia_caminho']; originais=indice(base)
    dados=RAIZ/e['dataset_caminho']; c=a['configuracao_treino']; comum=np.load(dados/'observavel_comum.npy')
    bloqueio=(destino/'exclusao.lock').open('a')
    try: fcntl.flock(bloqueio,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError: raise RuntimeError('Outro executor está ativo; não duplicar.')
    salvar_json(destino/'processo.json',{'pid':os.getpid(),'host':socket.gethostname(),'estado':'executando','inicio_utc':agora()})
    cache={}; estado={'status':'executando','planejados_corrigidos':384,'planejados_controles':2,'concluidos_corrigidos':0,'concluidos_controles':0,'inicio_utc':agora()}
    def rodar(x,controle=False):
        conferir_fontes(destino)
        chave=(x['par'],x['fold'])
        if chave not in cache:
            cache.clear(); horas=pd.read_parquet(dados/x['par']/'horas.parquet'); blocos=separar(horas,comum,x['fold'])
            matriz,escalas=ajustar_escalas(horas,blocos['treino']); cache[chave]=(blocos,matriz,escalas)
        blocos,matriz,escalas=cache[chave]
        antigo=originais[identidade(x)[:20]]
        cp=torch.load(antigo/'checkpoint.pt',map_location='cpu',weights_only=True)
        if cp['escalas']!=escalas or cp['configuracao']!=c: raise ValueError('Escalas/configuração diferentes do controle histórico.')
        del cp
        for b in ('validacao','teste','operacional'):
            q=pd.read_parquet(antigo/f'previsoes_{b}.parquet')
            for coluna in ('origem_utc','destino_utc','indice_hora','alvo'):
                pd.testing.assert_series_equal(q[coluna].reset_index(drop=True),blocos[b][coluna].reset_index(drop=True))
        local,pronta=tentativa(destino/'controles' if controle else destino,x)
        if not pronta:
            registro=ler_json(local/'tentativa.json')
            registro.update(politica='original_reexecutado' if controle else 'marcados_sem_penalizacao',execucao=e['id'],referencia_celula=antigo.relative_to(RAIZ).as_posix())
            salvar_json(local/'tentativa.json',registro)
            try:
                from previsao24.redes import criar
                from previsao24.treino import fixar_seed
                fixar_seed(x['seed']); rede=criar('mamba',c)
                grupos=descrever_grupos(rede,c['treino']) if not controle else [{'nomes':[n for n,_ in rede.named_parameters()],'weight_decay':c['treino']['weight_decay'],'elementos':sum(p.numel() for p in rede.parameters())}]
                salvar_json(local/'otimizador.json',{'politica':registro['politica'],'grupos':grupos})
                del rede
                if controle: from previsao24.treino import treinar
                else: from .treino import treinar
                with (local/'treinamento.log').open('a',encoding='utf-8',buffering=1) as log,redirect_stdout(log),redirect_stderr(log):
                    treinar(c,x,matriz,blocos,escalas,local)
                if controle:
                    diferencas={}
                    for b in ('validacao','teste','operacional'):
                        p=pd.read_parquet(local/f'previsoes_{b}.parquet')['previsao'].to_numpy()
                        q=pd.read_parquet(antigo/f'previsoes_{b}.parquet')['previsao'].to_numpy()
                        diferencas[b]={'maxima':float(np.max(np.abs(p-q))),'exata':bool(np.array_equal(p,q))}
                    r=ler_json(local/'resultado.json'); original=ler_json(antigo/'resultado.json')
                    relativa=abs(r['metricas']['teste']['mse']/original['metricas']['teste']['mse']-1)
                    recibo={'diferencas':diferencas,'variacao_relativa_mse':relativa,'mesma_epoca':r['epoca_selecionada']==original['epoca_selecionada']}
                    salvar_json(local/'reproducao.json',recibo)
                    if max(v['maxima'] for v in diferencas.values())>1e-5 or relativa>1e-4 or not recibo['mesma_epoca']:
                        raise ValueError('Controle de reprodução excedeu tolerância predefinida.')
                auditar_modelo(local,blocos,x)
                registro.update(status='auditada',fim_utc=agora())
            except Exception as erro:
                registro.update(status='falha',fim_utc=agora(),erro=repr(erro),traceback=traceback.format_exc())
                raise
            finally: salvar_json(local/'tentativa.json',registro)
        campo='concluidos_controles' if controle else 'concluidos_corrigidos'
        estado[campo]+=1; estado.update(ultima_celula=x,atualizado_utc=agora())
        salvar_json(destino/'progresso.json',estado)
        print(f'AUDITADA {campo}={estado[campo]} {x}',flush=True)
    try:
        pilotos=a['configuracao']['controles_reexecutados']
        for x in pilotos: rodar(x,True)
        for x in pilotos: rodar(x)
        salvar_json(destino/'piloto_aprovado.json',{'status':'aprovado','utc':agora(),'celulas':pilotos})
        chaves={identidade(x) for x in pilotos}
        for fase in ('desenvolvimento','avaliacao'):
            grade=[x for x in celulas(c,fase) if x['modelo']=='mamba']
            for x in grade:
                if identidade(x) not in chaves: rodar(x)
            salvar_json(destino/f'{fase}_concluido.json',{'status':'auditado','utc':agora(),'ajustes_corrigidos':len(grade),'classificacao':'retrospectiva'})
        if len(indice(destino))!=384: raise ValueError('Grade corrigida incompleta.')
        estado.update(status='treinos_concluidos',fim_treinos_utc=agora()); salvar_json(destino/'progresso.json',estado)
        from .analise import consolidar
        consolidar(destino)
        antes=ler_json(RAIZ/e['preparacao_caminho']/'preservacao_antes.json')
        depois=hashes([RAIZ/p for p in antes['arquivos']])
        if depois!=antes['arquivos']: raise ValueError('Preservação do estudo anterior divergiu.')
        salvar_json(destino/'preservacao_depois.json',{'status':'aprovado','utc':agora(),'arquivos_conferidos':len(depois),'manifesto_antes_sha256':a['preservacao_antes_sha256']})
        estado.update(status='concluido',fim_utc=agora())
    except Exception as erro:
        estado.update(status='falha',fim_utc=agora(),erro=repr(erro),traceback=traceback.format_exc())
        raise
    finally:
        salvar_json(destino/'progresso.json',estado)
        salvar_json(destino/'processo.json',{'pid':os.getpid(),'host':socket.gethostname(),'estado':estado['status'],'fim_utc':agora()})
        bloqueio.close()
    return destino
