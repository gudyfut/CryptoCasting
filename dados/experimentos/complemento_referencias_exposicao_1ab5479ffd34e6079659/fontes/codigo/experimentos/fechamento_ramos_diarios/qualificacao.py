"""Gates CUDA e dados de todas as moedas, anteriores aos ajustes de mercado."""
import os
import subprocess
import sys
import time
import traceback
import numpy as np
import pandas as pd
import torch
from infraestrutura.artefatos import RAIZ, ler_json, salvar_json, agora, sha256, conferir_arquivos
from entradas_modelo.padronizacao_diaria import preparar_com_escalas
from qualificacao.dados_sinteticos import dados_artificiais
from treinamento.otimizacao import fixar_seed
from experimentos.cryptomamba_reproducivel.qualificacao import ambiente
from experimentos.taxa_diaria.qualificacao import iguais
from experimentos.penalizacao_seletiva_diaria.qualificacao import conferir_controle_A as conferir_reproducao
from experimentos.ablacao_linear_diaria.treinamento import ajustar as treinador_referencia
from .contratos import CFG, REG, configuracao_moeda, receita
from .treinamento import ajustar, carregar_rede, inferir


def executar():
    import fcntl
    from .ciclo import fontes
    with (RAIZ/'registros/operacional_futuros/gpu.lock').open('a+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip(), 'GPU ocupada.'
        destino = REG/'qualificacoes'/agora().replace(':','').replace('+','_')
        destino.mkdir(parents=True,exist_ok=False); inicio = time.monotonic()
        salvar_json(destino/'processo.json',dict(pid=os.getpid(),utc=agora(),fase='qualificacao'))
        try:
            c = ler_json(CFG)
            relativo = (destino/'referencias.json').relative_to(RAIZ).as_posix()
            nativo = RAIZ/'.venv/Scripts/python.exe'
            py = str(nativo) if nativo.exists() else sys.executable
            a = subprocess.run([py,'-B','-m','experimentos.fechamento_ramos_diarios.evidencias',relativo],cwd=RAIZ,capture_output=True,text=True)
            (destino/'integridade.log').write_text(a.stdout+a.stderr,encoding='utf-8')
            assert a.returncode == 0, a.stdout+a.stderr
            refs = ler_json(RAIZ/relativo)
            suites = ['testes.fechamento_ramos_diarios.test_contratos',
                'testes.ablacao_linear_diaria.test_modelo', 'testes.ablacao_linear_diaria.test_contratos',
                'testes.padronizacao_diaria.test_contratos','testes.alvo_retorno_diario.test_contratos',
                'testes.penalizacao_seletiva_diaria.test_otimizacao',
                'testes.eixo_temporal_diario.test_avaliacao',
                'testes.simulacao_operacoes.test_continuidade_diaria',
                'testes.simulacao_operacoes.test_auditoria_grade_continuidade']
            t = subprocess.run([sys.executable,'-B','-m','unittest','-v',*suites],cwd=RAIZ,capture_output=True,text=True)
            (destino/'tests.log').write_text(t.stdout+t.stderr,encoding='utf-8')
            assert t.returncode == 0 and 'skipped=' not in t.stderr, t.stdout+t.stderr
            cfg = configuracao_moeda(c,'BTCUSDT')
            df = dados_artificiais();df['volume'] = 120000+np.arange(len(df))*5
            d,_ = preparar_com_escalas(df,cfg)
            d = {fase:{k:v[:65] for k,v in z.items()} for fase,z in d.items() if fase!='teste'}
            class Proibido(dict):
                def __getitem__(self,chave): raise AssertionError('Teste acessado pelo treinamento.')
            d['teste'] = Proibido()
            assert ajustar is treinador_referencia
            for variante in cfg['variantes']:
                rc = receita(cfg,variante)
                for repeticao in (1,2): ajustar(d,rc,42,destino/f'{variante}_{repeticao}',{'tipo':'artificial'},epocas=6)
                iguais(destino/f'{variante}_1',destino/f'{variante}_2')
            recargas = {}; populacoes = {}
            for simbolo, info in refs['moedas'].items():
                cfg = configuracao_moeda(c,simbolo)
                dados,escalas = preparar_com_escalas(pd.read_parquet(RAIZ/info['diario']['pasta']/'diario.parquet'),cfg)
                assert escalas == info['escalas']
                populacoes[simbolo] = {fase:len(z['y']) for fase,z in dados.items()}
                assert populacoes[simbolo] == info['populacoes']
                for chave,prova in info['modelos'].items():
                    v,seed = chave.split('_'); pasta = RAIZ/prova['pasta']
                    rede = carregar_rede(pasta,receita(cfg,v))
                    pv = inferir(rede,dados['validacao']['x'])
                    np.testing.assert_array_equal(pv,np.load(pasta/'validacao.npz')['previsoes'])
                    np.testing.assert_array_equal(pv,np.load(RAIZ/prova['previsoes']['validacao'])['previsoes_retorno'])
                    recargas[f'{simbolo}/{chave}'] = True
                    del rede;torch.cuda.empty_cache()
            assert len(recargas) == 18
            fixar_seed(42); amb = ambiente()
            ptr = ler_json(RAIZ/'registros/ablacao_linear_diaria/execucao.json')
            assert amb == ler_json(RAIZ/ptr['pasta']/'congelamento.json')['ambiente']
            conferir_arquivos(RAIZ,refs['preservacao'])
            q = dict(utc=agora(),situacao='aprovado',ambiente=amb,referencias_arquivo=relativo,
                referencias_sha256=sha256(RAIZ/relativo),populacoes=populacoes,
                recargas_exatas=recargas,treino_sintetico=dict(variantes=4,repeticoes=2,epocas=6,exemplos=65,teste_inacessivel=True),
                novos_treinamentos_mercado=0,segundos=time.monotonic()-inicio,
                limite='Controles de mercado ainda obrigatórios; qualificação não certifica desempenho.')
            salvar_json(destino/'qualificacao.json',q)
            salvar_json(REG/'qualificacao.json',dict(arquivo=(destino/'qualificacao.json').relative_to(RAIZ).as_posix(),
                sha256=sha256(destino/'qualificacao.json'),fontes=fontes()))
            print('QUALIFICACAO_APROVADA',flush=True)
        except BaseException:
            salvar_json(destino/'incidente.json',dict(utc=agora(),erro=traceback.format_exc()));raise
