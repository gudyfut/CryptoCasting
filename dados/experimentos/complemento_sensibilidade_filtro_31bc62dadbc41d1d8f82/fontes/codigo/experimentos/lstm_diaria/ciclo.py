"""Ciclo finito: qualificar, congelar, treinar e avaliar sem alterar estudos pais."""
import argparse
from copy import deepcopy
import io
import json
import os
import platform
from pathlib import Path
import shutil
import subprocess
import sys
import traceback
import zipfile
import numpy as np
from infraestrutura.artefatos import RAIZ, agora, conferir_arquivos, identidade, ler_json, salvar_json, sha256

REG = RAIZ/'registros/lstm_diaria'
CFG = RAIZ/'configuracoes/lstm_diaria_001.json'
PROTOCOLO = RAIZ/'docs/protocolo_lstm_diaria.md'


def relativo(p):
    return Path(p).relative_to(RAIZ).as_posix()


def fontes():
    # O snapshot conserva também as dependências científicas reutilizadas.
    caminhos = [p for p in (RAIZ/'codigo').rglob('*.py') if '__pycache__' not in p.parts]
    caminhos += list((RAIZ/'testes/lstm_diaria').glob('*.py')) + [CFG, PROTOCOLO]
    return {relativo(p): sha256(p) for p in sorted(caminhos)}


def pais(c):
    referencias = {}
    for nome in ('referencia_2025', 'referencia_2026', 'referencia_continuidade'):
        ptr = ler_json(RAIZ/c[nome]); p = RAIZ/ptr['pasta']
        assert sha256(p/'congelamento.json') == ptr['congelamento_sha256']
        referencias[nome] = ptr
    p25 = RAIZ/referencias['referencia_2025']['pasta']
    p26 = RAIZ/referencias['referencia_2026']['pasta']
    parima = RAIZ/referencias['referencia_continuidade']['pasta']
    manifesto_arima = ler_json(parima/'manifesto.json')['arquivos']
    f25 = ler_json(p25/'congelamento.json'); f26 = ler_json(p26/'congelamento.json')
    conferir_arquivos(p25, ler_json(p25/'fechamento.json')['arquivos'])
    assert sha256(p26/'manifesto.json') == ler_json(p26/'fechamento.json')['manifesto_sha256']
    conferir_arquivos(p26, ler_json(p26/'manifesto.json')['arquivos'])
    periodo = RAIZ/f26['referencia_periodo']['pasta']
    assert sha256(periodo/'congelamento.json') == f26['referencia_periodo']['congelamento_sha256']
    mercados26 = ler_json(periodo/'mercados.json')
    guardados = {}
    def guardar(p):
        p = Path(p)
        guardados[relativo(p)] = sha256(p)
    for p in (p25/'congelamento.json', p25/'fechamento.json', p26/'congelamento.json',
              p26/'manifesto.json', p26/'fechamento.json', p26/'operacoes.json', p26/'carteiras.zip',
              periodo/'congelamento.json', periodo/'mercados.json', parima/'manifesto.json', parima/'resultados.json'):
        guardar(p)
    assert sha256(parima/'resultados.json') == manifesto_arima['resultados.json']
    for moeda in c['moedas']:
        for ano, base in ((2025, p25/moeda), (2026, p26/moeda)):
            arquivos = [base/'configuracao.json', base/'escalas.json'] if ano == 2025 else [base/'entradas.npz']
            if ano == 2025:
                arquivos += [base/'dados'/f'{fase}.npz' for fase in ('treino','validacao','teste')]
                arquivos += [base/'publicacao/operacoes.json',base/'publicacao/carteiras.zip']
                arquivos += [base/'publicacao/previsoes'/f'teste_{nome}.npz' for nome in
                             [f'{v}_{s}' for v in ('A','L') for s in c['seeds']]+['A_ensemble','L_ensemble','naive','linear']]
            else:
                arquivos += [base/f'{nome}.npz' for nome in
                             [f'{v}_{s}' for v in ('A','L') for s in c['seeds']]+['A_ensemble','L_ensemble','naive','linear']]
            for arquivo in arquivos: guardar(arquivo)
        arima=parima/f'arima_{moeda}'/'teste.npz'
        assert sha256(arima)==manifesto_arima[f'arima_{moeda}/teste.npz']
        guardar(arima)
        with np.load(p25/moeda/'dados/teste.npz',allow_pickle=False) as z, np.load(arima,allow_pickle=False) as q:
            np.testing.assert_array_equal(z['origens_ms'],q['origens_ms'])
            np.testing.assert_array_equal(z['ultimo_close'],q['ultimo_close'])
            np.testing.assert_allclose(z['y'],q['y']/q['ultimo_close']-1,rtol=0,atol=1e-15)
        for info in (f25['referencias']['moedas'][moeda]['mercado_minuto'], mercados26[moeda]):
            pasta = RAIZ/info['pasta']
            assert sha256(pasta/'manifesto.json') == info['manifesto_sha256']
            manifesto = ler_json(pasta/'manifesto.json')
            conferir_arquivos(pasta, manifesto['arquivos'])
            guardar(pasta/'manifesto.json')
            for nome in manifesto['arquivos']: guardar(pasta/nome)
        # População e alvo preservados são idênticos para todas as referências.
        for ano, zpath, caminho in ((2025,p25/moeda/'dados/teste.npz',p25/moeda/'publicacao/previsoes/teste_A_42.npz'),
                                     (2026,p26/moeda/'entradas.npz',p26/moeda/'A_42.npz')):
            with np.load(zpath, allow_pickle=False) as z, np.load(caminho, allow_pickle=False) as q:
                np.testing.assert_array_equal(z['origens_ms'],q['origens_ms'])
                np.testing.assert_array_equal(z['ultimo_close'],q['ultimo_close'])
                np.testing.assert_array_equal(z['y' if ano == 2025 else 'alvo_retorno'],q['alvo_retorno'])
                assert z['x'].shape == (350 if ano == 2025 else 314,6,14)
    return referencias, guardados


def qualificar():
    import fcntl
    import torch
    from .treinamento import ajustar
    REG.mkdir(parents=True,exist_ok=True)
    with (RAIZ/'registros/operacional_futuros/gpu.lock').open('a+b') as gpu:
        fcntl.flock(gpu,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert torch.cuda.is_available()
        assert not subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
        c=ler_json(CFG); referencias, preservados=pais(c)
        resultado = subprocess.run([sys.executable,'-B','-m','unittest','testes.lstm_diaria.test_contratos','-v'],
                                   cwd=RAIZ,capture_output=True,text=True)
        assert resultado.returncode == 0, resultado.stdout+resultado.stderr
        pasta=REG/'qualificacoes'/agora().replace(':','').replace('+','_');pasta.mkdir(parents=True,exist_ok=False)
        (pasta/'testes.log').write_text(resultado.stdout+resultado.stderr,encoding='utf-8')
        rng=np.random.default_rng(91)
        tr=dict(x=rng.normal(size=(65,6,14)).astype('float32'),y=(rng.normal(size=65)*.02).astype('float64'))
        val=dict(x=rng.normal(size=(31,6,14)).astype('float32'),y=(rng.normal(size=31)*.02).astype('float64'))
        for n in (1,2): ajustar(tr,val,c['treinamento'],42,pasta/f'sintetico_{n}',{'tipo':'sintetico'},epocas=4)
        a,b=[ler_json(pasta/f'sintetico_{n}/selecao.json') for n in (1,2)]
        assert a['epoca']==b['epoca'] and a['rmse_validacao']==b['rmse_validacao']
        with np.load(pasta/'sintetico_1/validacao.npz') as x,np.load(pasta/'sintetico_2/validacao.npz') as y:
            np.testing.assert_array_equal(x['previsoes'],y['previsoes'])
        conferir_arquivos(RAIZ,preservados)
        q=dict(utc=agora(),situacao='aprovado',cuda=torch.version.cuda,torch=torch.__version__,gpu=torch.cuda.get_device_name(),
               fontes=fontes(),referencias=referencias,dependencias=preservados,controle_sintetico_exato=True,
               limite='Teste sintético e controle de dados; controles de mercado ainda obrigatórios.')
        salvar_json(pasta/'qualificacao.json',q)
        salvar_json(REG/'qualificacao.json',dict(arquivo=relativo(pasta/'qualificacao.json'),sha256=sha256(pasta/'qualificacao.json')))
        print('QUALIFICACAO_APROVADA',flush=True)


def preparar():
    assert not (REG/'execucao.json').exists(), 'Identidade já existe; investigar estado antes de qualquer retomada.'
    ponteiro=ler_json(REG/'qualificacao.json');assert sha256(RAIZ/ponteiro['arquivo'])==ponteiro['sha256']
    q=ler_json(RAIZ/ponteiro['arquivo']);assert q['situacao']=='aprovado' and q['fontes']==fontes()
    conferir_arquivos(RAIZ,q['dependencias'])
    c=ler_json(CFG)
    f=dict(utc=agora(),configuracao=c,fontes=q['fontes'],referencias=q['referencias'],dependencias=q['dependencias'],qualificacao=ponteiro,
           escopo='12 ajustes LSTM e 4 controles; períodos conhecidos retrospectivos; sem escolha por teste.')
    ident=identidade(f)[:20];p=RAIZ/'dados/experimentos'/f'lstm_diaria_{ident}';p.mkdir(parents=True,exist_ok=False)
    for nome in f['fontes']:
        destino=p/'fontes'/nome;destino.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(RAIZ/nome,destino)
    salvar_json(p/'congelamento.json',f)
    ptr=dict(id=ident,pasta=relativo(p),congelamento_sha256=sha256(p/'congelamento.json'))
    salvar_json(REG/'execucao.json',ptr)
    salvar_json(REG/'estado.json',dict(utc=agora(),situacao='preparado',execucao=ptr,ajustes_concluidos=0,total_ajustes=16))
    print('PREPARADO',ptr,flush=True)


def contexto():
    ptr=ler_json(REG/'execucao.json');p=RAIZ/ptr['pasta']
    assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    f=ler_json(p/'congelamento.json')
    conferir_arquivos(RAIZ,f['fontes']);conferir_arquivos(p/'fontes',f['fontes']);conferir_arquivos(RAIZ,f['dependencias'])
    return ptr,p,f


def estado(p,ptr,situacao,**kw):
    s=dict(utc=agora(),situacao=situacao,execucao=ptr,**kw)
    salvar_json(p/'progresso.json',s);salvar_json(REG/'estado.json',s)
    print('ESTADO',situacao,json.dumps(kw,ensure_ascii=False),flush=True)


def executar():
    import fcntl
    import torch
    from .treinamento import ajustar
    with (RAIZ/'registros/operacional_futuros/gpu.lock').open('a+b') as gpu, (REG/'execucao.lock').open('a+b') as lock:
        fcntl.flock(gpu,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
        ptr,p,f=contexto();assert not (p/'inicio.json').exists(),'Já iniciada; investigar antes de retomar.'
        proc=dict(pid=os.getpid(),host=platform.node(),boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                  inicio_processo_ticks=Path('/proc/self/stat').read_text().split()[21],utc=agora(),ativo=True)
        salvar_json(p/'inicio.json',proc);salvar_json(p/'processo.json',proc)
        c=f['configuracao'];ref=RAIZ/f['referencias']['referencia_2025']['pasta'];concluidos=0
        try:
            for moeda in c['moedas']:
                dados={fase:dict(np.load(ref/moeda/'dados'/f'{fase}.npz',allow_pickle=False)) for fase in ('treino','validacao')}
                for seed,controle in [(42,False),(42,True),(17,False),(2026,False)]:
                    nome=('controle_' if controle else 'seed_')+str(seed)
                    estado(p,ptr,'treinando',moeda=moeda,ajuste=nome,ajustes_concluidos=concluidos,total_ajustes=16)
                    destino=p/moeda/'ajustes'/nome
                    ajustar(dados['treino'],dados['validacao'],c['treinamento'],seed,destino,
                            dict(execucao=ptr['id'],moeda=moeda,seed=seed))
                    if controle:
                        a=ler_json(p/moeda/'ajustes/seed_42/selecao.json');b=ler_json(destino/'selecao.json')
                        assert a['epoca']==b['epoca'] and a['rmse_validacao']==b['rmse_validacao']
                        with np.load(p/moeda/'ajustes/seed_42/validacao.npz') as x,np.load(destino/'validacao.npz') as y:
                            np.testing.assert_array_equal(x['previsoes'],y['previsoes'])
                        salvar_json(p/moeda/'controle.json',dict(aprovado=True,epoca=a['epoca'],repeticao_validacao_exata=True))
                    concluidos+=1
            estado(p,ptr,'avaliando',ajustes_concluidos=concluidos,total_ajustes=16)
            from .avaliacao import executar as avaliar
            resumo=avaliar(p,f,lambda **kw:estado(p,ptr,'avaliando',ajustes_concluidos=concluidos,total_ajustes=16,**kw))
            contexto()
            arquivos={q.relative_to(p).as_posix():sha256(q) for q in p.rglob('*') if q.is_file() and 'fontes' not in q.relative_to(p).parts and q.name not in ('processo.json','progresso.json','fechamento.json')}
            salvar_json(p/'fechamento.json',dict(utc=agora(),situacao='concluido_controles_aprovados',execucao=ptr,
                        ajustes_cientificos=12,controles=4,resumo=resumo,arquivos=arquivos))
            salvar_json(REG/'fechamento.json',dict(arquivo=relativo(p/'fechamento.json'),sha256=sha256(p/'fechamento.json')))
            estado(p,ptr,'concluido_controles_aprovados',ajustes_concluidos=16,total_ajustes=16,conferencia_posterior='pendente')
        except BaseException:
            salvar_json(p/'incidente.json',dict(utc=agora(),erro=traceback.format_exc()))
            estado(p,ptr,'interrompido_preservado',ajustes_concluidos=concluidos,total_ajustes=16)
            raise
        finally:
            proc.update(ativo=False,encerramento_utc=agora());salvar_json(p/'processo.json',proc)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('acao',choices=['qualificar','preparar','executar'])
    globals()[parser.parse_args().acao]()
