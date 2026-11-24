"""Qualificação antes do congelamento; controles de mercado ficam no executor."""
import json
import os
import subprocess
import sys
import time
import traceback
import numpy as np
import pandas as pd
import torch
from mamba_ssm import Mamba
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,agora,sha256
from entradas_modelo.padronizacao_diaria import preparar_com_escalas
from qualificacao.dados_sinteticos import dados_artificiais
from treinamento.otimizacao import fixar_seed
from experimentos.cryptomamba_reproducivel.qualificacao import ambiente
from experimentos.sem_penalizacao_diaria.treinamento import ajustar as ajustar_herdado
from experimentos.taxa_diaria.qualificacao import iguais
from experimentos.eixo_temporal_diario.evidencias import conferir_pesos_controle
from .contratos import receita,selecionar_prefixo
from .treinamento import construir,ajustar,carregar_rede,inferir
from .otimizacao import separar


def conferir_controle_A(atual,herdado):
    def historia(p):
        return [{k:v for k,v in json.loads(l).items() if k!='segundos'}
                for l in (p/'epocas.jsonl').read_text().splitlines()][:200]
    a,b=historia(atual),historia(herdado)
    assert len(a)==200 and a==b,'Controle A: trajetória prefixo200 divergente.'
    assert selecionar_prefixo(a)['epoca']==ler_json(atual/'selecao.json')['epoca']==ler_json(herdado/'selecao.json')['epoca']
    np.testing.assert_array_equal(np.load(atual/'validacao.npz')['previsoes'],np.load(herdado/'validacao.npz')['previsoes'])
    novos={p.name:p for p in (atual/'checkpoints').glob('*.pt')}
    antigos={p.name:p for p in (herdado/'checkpoints').glob('*.pt') if int(p.stem.split('_')[1])<=200}
    assert novos.keys()==antigos.keys()
    for n in novos:
        x=torch.load(novos[n],map_location='cpu',weights_only=True)['pesos']
        y=torch.load(antigos[n],map_location='cpu',weights_only=True)['pesos']
        assert x.keys()==y.keys() and all(torch.equal(x[k],y[k]) for k in x),n
    return True


def sondar(c,destino):
    modelos={};resumo={}
    for v in ('A','S'):
        cfg=receita(c,v);fixar_seed(42);rede=construir(cfg)
        modelos[v]={k:p.detach().cpu().clone() for k,p in rede.state_dict().items()}
        assert sum(p.numel() for p in rede.parameters())==136952
        assert sum(isinstance(m,Mamba) for m in rede.modules())==12
        grupos,nomes=separar(rede,cfg['treinamento']['politica_penalizacao'],.001)
        salvar_json(destino/f'grupos_{v}.json',nomes)
        if v=='S':
            assert len(grupos)==2
            assert all(n['weight_decay']==0 for n in nomes if n['motivos_elegibilidade'])
            assert all(n['weight_decay']==.001 for n in nomes if not n['motivos_elegibilidade'])
            assert sum('marcador_no_weight_decay' in n['motivos_elegibilidade'] for n in nomes)==24
            assert sum('parametros_LayerNorm' in n['motivos_elegibilidade'] for n in nomes)==24
        x=torch.randn(3,6,14,device='cuda');y=torch.randn(3,device='cuda')*.01
        saidas=[];gradientes=[]
        for _ in range(2):
            rede.zero_grad(set_to_none=True);p=rede(x)
            assert p.shape==(3,) and torch.isfinite(p).all()
            torch.sqrt(((p-y)**2).mean()+1e-8).backward()
            saidas.append(p.detach().clone())
            gradientes.append({n:p.grad.detach().clone() for n,p in rede.named_parameters()})
        assert torch.equal(*saidas)
        assert all(torch.equal(gradientes[0][n],gradientes[1][n]) and torch.isfinite(g).all() for n,g in gradientes[0].items())
        try:rede(x.transpose(1,2).contiguous())
        except ValueError:pass
        else:raise AssertionError('Dimensão incorreta aceita.')
        resumo[v]={'parametros':136952,'isentos':sum(n['elementos'] for n in nomes if n['weight_decay']==0),
                   'grupos':len(grupos),'forward_backward_exatos':True}
        del rede;torch.cuda.empty_cache()
    assert modelos['A'].keys()==modelos['S'].keys()
    assert all(torch.equal(modelos['A'][k],modelos['S'][k]) for k in modelos['A'])
    return resumo


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
            aud=subprocess.run([py,'-B','-m','experimentos.penalizacao_seletiva_diaria.evidencias',relativo],cwd=RAIZ,capture_output=True,text=True)
            (destino/'integridade.log').write_text(aud.stdout+aud.stderr,encoding='utf8');assert aud.returncode==0,aud.stdout+aud.stderr
            ref=ler_json(destino/'referencias.json')
            suites=['testes.penalizacao_seletiva_diaria.test_contratos','testes.penalizacao_seletiva_diaria.test_otimizacao',
                    'testes.eixo_temporal_diario.test_contratos','testes.eixo_temporal_diario.test_avaliacao',
                    'testes.simulacao_operacoes.test_auditoria_grade_continuidade']
            t=subprocess.run([sys.executable,'-B','-m','unittest','-v',*suites],cwd=RAIZ,capture_output=True,text=True)
            (destino/'tests.log').write_text(t.stdout+t.stderr,encoding='utf8');assert t.returncode==0,t.stdout+t.stderr
            sondas=sondar(c,destino)
            df=dados_artificiais();df['volume']=120000+np.arange(len(df))*5
            dados,_=preparar_com_escalas(df,c)
            dados={f:{k:v[:65] for k,v in z.items()} for f,z in dados.items() if f!='teste'}
            class Proibido(dict):
                def __getitem__(self,chave):raise AssertionError('Teste acessado pelo treinamento.')
            dados['teste']=Proibido();duracoes={}
            for v in ('A','S'):
                cfg=receita(c,v);t0=time.monotonic()
                for repeticao in (1,2):ajustar(dados,cfg,42,destino/f'{v}_{repeticao}',{'tipo':'artificial'},epocas=6)
                iguais(destino/f'{v}_1',destino/f'{v}_2')
                if v=='A':
                    ajustar_herdado(dados,cfg,42,destino/'A_herdado',{'tipo':'artificial'},epocas=6)
                    iguais(destino/'A_1',destino/'A_herdado')
                duracoes[v]=time.monotonic()-t0
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
            r={'utc':agora(),'situacao':'aprovado','ambiente':ambiente(),'sondas':sondas,
               'inicializacao_A_S_identica':True,'treinador_uniforme_equivalente':True,
               'treino_sintetico':{'epocas':6,'exemplos':65,'repeticoes_exatas':2,'duracoes_segundos':duracoes,'teste_inacessivel':True},
               'reproducao_herdada':controles,'referencias_arquivo':relativo,'referencias_sha256':sha256(destino/'referencias.json'),
               'escalas':escalas,'populacoes':{f:len(z['y']) for f,z in reais.items()},'dados_fatorial_exatos':True,
               'novos_treinamentos_mercado':0,'segundos':time.monotonic()-inicio,
               'limite':'Controles reais A42 e S42 ainda devem passar no executor antes das demais seeds.'}
            salvar_json(destino/'qualificacao.json',r)
            salvar_json(REG/'qualificacao.json',{'arquivo':(destino/'qualificacao.json').relative_to(RAIZ).as_posix(),
                        'sha256':sha256(destino/'qualificacao.json'),'fontes':fontes()})
            print('QUALIFICACAO_APROVADA',r,flush=True)
        except BaseException:
            salvar_json(destino/'incidente.json',{'utc':agora(),'erro':traceback.format_exc()});raise
