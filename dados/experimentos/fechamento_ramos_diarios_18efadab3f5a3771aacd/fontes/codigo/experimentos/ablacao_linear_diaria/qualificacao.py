"""Qualificação isolada: dados idênticos, pesos iniciais, causalidade e reprodução."""
import os
import subprocess
import sys
import time
import traceback
import numpy as np
import pandas as pd
import torch
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,agora,sha256
from entradas_modelo.padronizacao_diaria import preparar_com_escalas
from qualificacao.dados_sinteticos import dados_artificiais
from treinamento.otimizacao import fixar_seed
from experimentos.cryptomamba_reproducivel.qualificacao import ambiente
from experimentos.penalizacao_seletiva_diaria.treinamento import ajustar as ajustar_herdado
from experimentos.penalizacao_seletiva_diaria.qualificacao import conferir_controle_A
from experimentos.taxa_diaria.qualificacao import iguais
from experimentos.eixo_temporal_diario.evidencias import conferir_pesos_controle
from .contratos import receita
from .treinamento import ajustar,carregar_rede,inferir


def executar():
    import fcntl
    from .ciclo import REG,CFG,fontes
    with (RAIZ/'registros/operacional_futuros/gpu.lock').open('a+b') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip(),'GPU ocupada.'
        destino=REG/'qualificacoes'/agora().replace(':','').replace('+','_');destino.mkdir(parents=True,exist_ok=False)
        try:
            salvar_json(destino/'processo.json',{'pid':os.getpid(),'utc':agora(),'fase':'qualificacao'})
            c=ler_json(CFG);inicio=time.monotonic();relativo=(destino/'referencias.json').relative_to(RAIZ).as_posix()
            nativo=RAIZ/'.venv/Scripts/python.exe';py=str(nativo) if nativo.exists() else sys.executable
            aud=subprocess.run([py,'-B','-m','experimentos.ablacao_linear_diaria.evidencias',relativo],cwd=RAIZ,capture_output=True,text=True)
            (destino/'integridade.log').write_text(aud.stdout+aud.stderr,encoding='utf8');assert aud.returncode==0,aud.stdout+aud.stderr
            ref=ler_json(destino/'referencias.json')
            suites=['testes.ablacao_linear_diaria.test_contratos','testes.ablacao_linear_diaria.test_modelo',
                    'testes.padronizacao_diaria.test_contratos','testes.alvo_retorno_diario.test_contratos',
                    'testes.penalizacao_seletiva_diaria.test_contratos','testes.penalizacao_seletiva_diaria.test_otimizacao',
                    'testes.eixo_temporal_diario.test_avaliacao',
                    'testes.simulacao_operacoes.test_continuidade_diaria',
                    'testes.simulacao_operacoes.test_auditoria_grade_continuidade']
            t=subprocess.run([sys.executable,'-B','-m','unittest','-v',*suites],cwd=RAIZ,capture_output=True,text=True)
            (destino/'tests.log').write_text(t.stdout+t.stderr,encoding='utf8');assert t.returncode==0,t.stdout+t.stderr
            df=dados_artificiais();df['volume']=120000+np.arange(len(df))*5
            dados,_=preparar_com_escalas(df,c)
            dados={f:{k:v[:65] for k,v in z.items()} for f,z in dados.items() if f!='teste'}
            class Proibido(dict):
                def __getitem__(self,chave):raise AssertionError('Teste acessado pelo treinamento.')
            dados['teste']=Proibido();duracoes={}
            construtor_original=ajustar_herdado.__globals__['construir']
            for v in ('A','L'):
                cfg=receita(c,v);t0=time.monotonic()
                for repeticao in (1,2):ajustar(dados,cfg,42,destino/f'{v}_{repeticao}',{'tipo':'artificial'},epocas=6)
                iguais(destino/f'{v}_1',destino/f'{v}_2')
                if v=='A':
                    ajustar_herdado(dados,cfg,42,destino/'A_herdado',{'tipo':'artificial'},epocas=6)
                    iguais(destino/'A_1',destino/'A_herdado')
                duracoes[v]=time.monotonic()-t0
            assert ajustar_herdado.__globals__['construir'] is construtor_original
            reais,escalas=preparar_com_escalas(pd.read_parquet(RAIZ/ref['referencias']['A']['diario']['pasta']/'diario.parquet'),c)
            assert escalas==ref['referencias']['A']['escalas']
            for fase,z in reais.items():
                with np.load(RAIZ/ref['dados_preparados'][fase]) as original:
                    assert set(z)==set(original.files)
                    for k in z:np.testing.assert_array_equal(z[k],original[k])
            n=conferir_pesos_controle(ref['referencias']['A']);controles={}
            for seed in c['seeds']:
                pasta=RAIZ/ref['referencias']['A']['provas'][str(seed)]['pasta']
                rede=carregar_rede(pasta,receita(c,'A'));p=inferir(rede,reais['validacao']['x'])
                np.testing.assert_array_equal(p,np.load(pasta/'validacao.npz')['previsoes'])
                controles[str(seed)]={'recarga_validacao_exata':True,'prefixo200_comprovado':True,'checkpoints_controle42':n}
                del rede;torch.cuda.empty_cache()
            fixar_seed(42)
            r={'utc':agora(),'situacao':'aprovado','ambiente':ambiente(),
               'parametros':{'A':136952,'L':824},'inicializacao_projecoes_A_L_e_rng_identicos':True,
               'projecoes_gradientes_iguais_A_com_ramos_zerados':True,'treinador_A_equivalente':True,
               'treino_sintetico':{'epocas':6,'exemplos':65,'repeticoes_exatas':2,'duracoes_segundos':duracoes,'teste_inacessivel':True},
               'reproducao_herdada':controles,'referencias_arquivo':relativo,'referencias_sha256':sha256(destino/'referencias.json'),
               'escalas':escalas,'populacoes':{f:len(z['y']) for f,z in reais.items()},'dados_fatorial_exatos':True,
               'novos_treinamentos_mercado':0,'segundos':time.monotonic()-inicio,
               'limite':'Controles reais A42 e L42 ainda devem passar no executor antes das demais seeds.'}
            salvar_json(destino/'qualificacao.json',r)
            salvar_json(REG/'qualificacao.json',{'arquivo':(destino/'qualificacao.json').relative_to(RAIZ).as_posix(),
                        'sha256':sha256(destino/'qualificacao.json'),'fontes':fontes()})
            print('QUALIFICACAO_APROVADA',r,flush=True)
        except BaseException:
            salvar_json(destino/'incidente.json',{'utc':agora(),'erro':traceback.format_exc()});raise
