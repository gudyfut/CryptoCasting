"""Ensaios e reprodução herdada antes da grade; sem avaliação de2025/2026."""
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from mamba_ssm import Mamba
from infraestrutura.artefatos import RAIZ, ler_json, salvar_json, agora, sha256
from entradas_modelo.padronizacao_diaria import preparar_com_escalas
from qualificacao.dados_sinteticos import dados_artificiais
from treinamento.otimizacao import fixar_seed
from experimentos.cryptomamba_reproducivel.qualificacao import ambiente
from experimentos.sem_penalizacao_diaria.observacao import observar
from experimentos.sem_penalizacao_diaria.treinamento import ajustar as ajustar_herdado
from experimentos.taxa_diaria.qualificacao import iguais
from .contratos import receita, organizar
from .treinamento import construir, ajustar, carregar_rede, inferir
from .evidencias import conferir_pesos_controle


def sondar(c, destino):
    resultados={}
    for variante in ('A','B','C','D'):
        cfg=receita(c,variante);fixar_seed(42);rede=construir(cfg)
        esperado=c['adaptacao_temporal']['parametros_dias' if cfg['eixo']=='dias' else 'parametros_canais']
        assert sum(p.numel() for p in rede.parameters())==esperado
        assert sum(isinstance(m,Mamba) for m in rede.modules())==12
        entradas=(14,6) if cfg['eixo']=='dias' else (6,14)
        x=torch.randn(3,*entradas,device='cuda');y=torch.randn(3,device='cuda')*.01
        saidas=[];gradientes=[]
        for _ in range(3):
            rede.zero_grad(set_to_none=True);v=rede(x)
            assert v.shape==(3,) and torch.isfinite(v).all()
            torch.sqrt(((v-y)**2).mean()+1e-8).backward()
            saidas.append(v.detach().clone())
            gradientes.append({n:p.grad.detach().clone() for n,p in rede.named_parameters()})
        assert all(torch.equal(saidas[0],v) for v in saidas)
        assert all(torch.equal(gradientes[0][n],g[n]) for g in gradientes for n in g)
        assert all(torch.isfinite(g).all() for g in gradientes[0].values())
        with torch.no_grad():
            # Confere causalidade interna antes da cabeça agregadora.
            if cfg['eixo']=='dias':
                alterado=x.clone();alterado[:,8:,:]+=3
                a=rede.projecao_entrada(x);b=rede.projecao_entrada(alterado)
                for bloco in rede.nucleo.blocks:
                    a=bloco(a);b=bloco(b);torch.testing.assert_close(a[:,:8],b[:,:8],rtol=0,atol=0)
            oposto=x.transpose(1,2).contiguous()
            try:rede(oposto)
            except ValueError:pass
            else:raise AssertionError('Eixo errado aceito.')
        observar(rede,x.detach().cpu().numpy(),destino/f'sonda_{variante}.json',0)
        observacao=ler_json(destino/f'sonda_{variante}.json')
        assert observacao['pesos_e_rng_preservados']
        assert {a['forma'][1] for a in observacao['ativacoes'].values()}=={entradas[0]}
        resultados[variante]={'parametros':esperado,'blocos':12,'sequencia':entradas[0],
            'forward_backward_repetidos_exatos':True,'observador_preservado':True,
            'prefixo_temporal_causal':True if cfg['eixo']=='dias' else None}
        del rede;torch.cuda.empty_cache()
    return resultados


def executar():
    import fcntl
    from .ciclo import REG, CFG, fontes
    with (RAIZ/'registros/operacional_futuros/gpu.lock').open('a+b') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        ocupado=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True)
        if ocupado.strip():raise RuntimeError('GPU ocupada.')
        destino=REG/'qualificacoes'/agora().replace(':','').replace('+','_')
        destino.mkdir(parents=True,exist_ok=False)
        try:
            salvar_json(destino/'processo.json',{'pid':os.getpid(),'utc':agora(),'fase':'qualificacao'})
            c=ler_json(CFG);inicio=time.monotonic()
            # Hashing pelo Windows evita o custo do DrvFS sem mudar dados/modelos.
            nativo=RAIZ/'.venv/Scripts/python.exe'
            relativo=(destino/'referencias.json').relative_to(RAIZ).as_posix()
            py=str(nativo) if os.name=='posix' and nativo.exists() else sys.executable
            aud=subprocess.run([py,'-B','-m','experimentos.eixo_temporal_diario.evidencias',relativo],cwd=RAIZ,capture_output=True,text=True)
            (destino/'integridade.log').write_text(aud.stdout+aud.stderr,encoding='utf-8')
            assert aud.returncode==0,aud.stdout+aud.stderr
            ref=ler_json(destino/'referencias.json')
            suites=['testes.eixo_temporal_diario.test_contratos',
                    'testes.eixo_temporal_diario.test_avaliacao',
                    'testes.simulacao_operacoes.test_auditoria_grade_continuidade']
            teste=subprocess.run([sys.executable,'-B','-m','unittest','-v',*suites],cwd=RAIZ,capture_output=True,text=True)
            (destino/'tests.log').write_text(teste.stdout+teste.stderr,encoding='utf-8')
            assert teste.returncode==0,teste.stdout+teste.stderr
            sondas=sondar(c,destino)
            df=dados_artificiais();df['volume']=120000+np.arange(len(df))*5
            dados,_=preparar_com_escalas(df,c)
            dados={f:{k:v[:65] for k,v in z.items()} for f,z in dados.items() if f!='teste'}
            duracoes={}
            for variante in ('A','B','C','D'):
                cfg=receita(c,variante);d=organizar(dados,cfg['eixo'])
                class Proibido(dict):
                    def __getitem__(self,chave):raise AssertionError('Teste acessado no treino.')
                d['teste']=Proibido()
                inicio_variante=time.monotonic()
                for repeticao in (1,2):
                    ajustar(d,cfg,42,destino/f'{variante}_{repeticao}',{'tipo':'artificial'},epocas=6)
                iguais(destino/f'{variante}_1',destino/f'{variante}_2')
                if cfg['eixo']=='canais':
                    ajustar_herdado(d,cfg,42,destino/f'{variante}_herdado',{'tipo':'artificial'},epocas=6)
                    iguais(destino/f'{variante}_1',destino/f'{variante}_herdado')
                duracoes[variante]=time.monotonic()-inicio_variante
            # Apenas validação para reprodução; nenhum resultado de teste aqui.
            diario=pd.read_parquet(RAIZ/ref['referencias']['A']['diario']['pasta']/'diario.parquet')
            reais,escalas=preparar_com_escalas(diario,c)
            assert escalas==ref['referencias']['A']['escalas']
            controles={}
            for variante in ('A','B'):
                n=conferir_pesos_controle(ref['referencias'][variante])
                cfg=receita(c,variante)
                for seed in c['seeds']:
                    pasta=RAIZ/ref['referencias'][variante]['provas'][str(seed)]['pasta']
                    rede=carregar_rede(pasta,cfg)
                    atual=inferir(rede,reais['validacao']['x'])
                    np.testing.assert_array_equal(atual,np.load(pasta/'validacao.npz')['previsoes'])
                    observar(rede,reais['treino']['x'],destino/f'observacao_herdada_{variante}_{seed}.json',ler_json(pasta/'selecao.json')['epoca'])
                    controles[f'{variante}_{seed}']={'validacao_exata':True,'checkpoint_prefixo200':True,'checkpoints_controle42':n}
                    del rede;torch.cuda.empty_cache()
            r={'utc':agora(),'situacao':'aprovado','ambiente':ambiente(),'sondas':sondas,
               'treino_sintetico':{'epocas':6,'exemplos':65,'repeticoes_exatas':4,'equivalencia_herdado':['A','B'],
                                  'teste_inacessivel':True,'duracoes_segundos':duracoes},
               'reproducao_herdada':controles,'referencias_arquivo':relativo,
               'referencias_sha256':sha256(destino/'referencias.json'),
               'populacoes':{f:len(z['y']) for f,z in reais.items()},'escalas':escalas,
               'segundos':time.monotonic()-inicio,'novos_treinamentos_mercado':0,
               'limite':'Controles completos C42/D42 ainda precederão demais seeds; nenhuma seleção por teste.'}
            salvar_json(destino/'qualificacao.json',r)
            salvar_json(REG/'qualificacao.json',{'arquivo':(destino/'qualificacao.json').relative_to(RAIZ).as_posix(),
                                               'sha256':sha256(destino/'qualificacao.json'),'fontes':fontes()})
            print('QUALIFICACAO_APROVADA',r,flush=True)
        except BaseException:
            salvar_json(destino/'incidente.json',{'utc':agora(),'erro':traceback.format_exc()});raise
