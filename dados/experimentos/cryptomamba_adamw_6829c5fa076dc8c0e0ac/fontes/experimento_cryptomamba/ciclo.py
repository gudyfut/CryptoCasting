"""Seis ajustes de uma abordagem adaptada; fontes anteriores imutáveis."""
import contextlib
import importlib.util
import shutil
import traceback
from pathlib import Path
from uuid import uuid4
import pandas as pd
from infraestrutura.artefatos import RAIZ,agora,identidade,ler_json,salvar_json,sha256,conferir_arquivos,fontes as listar_fontes
from treinamento.ambiente import conferir as ambiente
from treinamento.preservacao import publicar as selar,conferir,exclusividade
from treinamento.ciclo import reproducao
from modelos.consumo import ConsumoModelos
from experimento_taxa_aprendizado.ciclo import conferir_execucao as abrir_taxa,fontes as fontes_anteriores
from avaliacao.publicacao import conferir_previsoes
from .treino import ajustar,avaliar
from .publicacao import publicar

REGISTROS=RAIZ/'registros/cryptomamba'
CONFIG='configuracoes/cryptomamba_adaptado_001.json'
PROTOCOLO='docs/protocolo_cryptomamba_adaptado.md'
COMMIT='fef42727861a9c3a32241283ab981ef21a49e291'
EXTERNAS=REGISTROS/'fontes_externas'/COMMIT
SEEDS=[17,42,2026,7,123,31415]
ORDEM=[42,17,2026,7,123,31415]


def configuracao():
    c=ler_json(RAIZ/CONFIG);b=ler_json(RAIZ/'configuracoes/mamba_estado16_complemento_001.json')
    removidas={'mamba','lstm','configuracao_modelos','seeds_pareadas','referencia_execucao','controle'}
    adicionadas={'origem_codigo','parametros_esperados','arquitetura','otimizador','scheduler','perda','orcamento_ajustes_reais','comparacao_primaria','controle'}
    if set(c)!=(set(b)-removidas)|adicionadas:raise ValueError('Campos da adaptação divergentes.')
    especiais={'versao','ciclo','hipotese','modelos','treino'}|removidas
    for k in set(b)-especiais:
        if c[k]!=b[k]:raise ValueError(f'Dado/alvo/população alterado: {k}')
    a={'contexto_projetado':14,'larguras':[14,16,32,1],'densidade':4,'estado':64,'convolucao':4,'expansao':2,'dropout':0.0,'eps_layernorm':1e-5,'varredura':'canais','canais':5}
    if c['arquitetura']!=a or c['treino']!=dict(b['treino'],taxa_aprendizado=.01,batch=32,microbatch=32):raise ValueError('Receita fora do contraste delimitado.')
    if (c['parametros_esperados']!=139317 or c['origem_codigo']!=COMMIT or c['orcamento_ajustes_reais']!=6 or c['seeds']!=SEEDS
        or c['modelos']!=['cryptomamba_adaptado'] or c['otimizador']!={'nome':'Adam','betas':[.9,.999],'eps':1e-8,'isencoes_oficiais':True}
        or c['scheduler']!={'nome':'StepLR','passo_epocas':10,'gamma':.5} or c['perda']!={'nome':'rmse_por_lote','epsilon':1e-8,'escala':'alvo_padronizado_treino'}):raise ValueError('Adaptação não corresponde ao protocolo.')
    return c


def fontes():
    f=fontes_anteriores();f.update(listar_fontes('experimento_cryptomamba','tests_cryptomamba'))
    for nome in (CONFIG,'run_cryptomamba.py'):f[nome]=sha256(RAIZ/nome)
    m=ler_json(EXTERNAS/'proveniencia.json')
    for nome,info in m['arquivos'].items():
        p=EXTERNAS/nome
        if sha256(p)!=info['sha256']:raise ValueError('Fonte externa alterada.')
        f[p.relative_to(RAIZ).as_posix()]=info['sha256']
    f[(EXTERNAS/'proveniencia.json').relative_to(RAIZ).as_posix()]=sha256(EXTERNAS/'proveniencia.json');return f


def referencias():
    p,f,consumo,partes,_=abrir_taxa()
    if ler_json(p/'progresso.json')['status']!='concluido' or ler_json(p/'processo.json')['ativo']:raise ValueError('Taxa não encerrada.')
    a=ler_json(RAIZ/'registros/taxa_aprendizado/conferencia_conclusao.json');conferir_arquivos(RAIZ,{a['arquivo']:a['sha256']})
    if ler_json(RAIZ/a['arquivo'])['execucao']!=f['id']:raise ValueError('Auditoria anterior divergente.')
    pp=ler_json(p/'publicacao.json');pub=p/pp['pasta'];conferir_arquivos(pub,{'manifesto.json':pp['manifesto_sha256']});conferir_arquivos(pub,ler_json(pub/'manifesto.json')['arquivos'])
    r=ler_json(pub/'resultados.json');refs={k:RAIZ/d['tentativa_origem'] for k,d in r['por_ajuste'].items()}
    if len(refs)!=53:raise ValueError('Heranças não totalizam53.')
    for t in refs.values():conferir(t)
    return consumo,partes,refs


def equivalencia_publica():
    """Somente classe neural de fonte revisada/licenciada; nenhuma CLI externa."""
    import torch
    from torch import nn
    from .modelo import NucleoCMamba
    fonte=EXTERNAS/'models/cmamba.py';spec=importlib.util.spec_from_file_location('cryptomamba_publico_verificado',fonte);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    ref=m.CMamba(num_features=5,hidden_dims=[14,16,32,1],d_states=64,layer_density=4,mlp_ratio=0,drop=0.,norm_layer=nn.LayerNorm).cuda().eval()
    nosso=NucleoCMamba(5).cuda().eval();nosso.load_state_dict(ref.state_dict(),strict=True)
    eixos=[];h=ref.blocks[0][0].op.register_forward_pre_hook(lambda mod,args:eixos.append(list(args[0].shape)))
    x=torch.randn(2,5,14,device='cuda')
    with torch.inference_mode():a=ref(x);b=nosso(x)
    h.remove();delta=float((a-b).abs().max());assert eixos==[[2,5,14]] and delta<=1e-6
    return {'fonte_sha256':sha256(fonte),'eixo_mamba_observado':eixos[0],'max_diferenca_absoluta':delta,'mesmas_chaves_pesos':True,'parametros_nucleo':sum(p.numel() for p in nosso.parameters()),'escopo':'equivalência do núcleo em tensor sintético/pesos iguais; não reprodução do treinamento/artigo'}


def qualificar():
    from tests_modelos.apoio import conjunto
    p=REGISTROS/'qualificacoes'/uuid4().hex;p.mkdir(parents=True);fs=fontes()
    for nome in fs:
        d=p/'fontes'/nome;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(RAIZ/nome,d)
    salvar_json(p/'inicio.json',{'utc':agora(),'fontes':fs,'natureza':'sintético; zero ajustes reais'})
    try:
        c=configuracao();consumo=ConsumoModelos(conjunto(),'qualificacao_cryptomamba');v={'natureza':'sintetico','familia':'cryptomamba_adaptado'}
        with (p/'qualificacao.log').open('w',encoding='utf-8',buffering=1) as log:
            with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                eq=equivalencia_publica()
                for nome in ('a','b'):
                    d=p/nome;d.mkdir();rede,r=ajustar(consumo,42,dict(c,treino=dict(c['treino'],epocas=2,paciencia=2)),d,v)
                    assert r['parametros']==139317
                    avaliar(consumo,consumo._conjunto.partes,dict(c,treino=dict(c['treino'],epocas=2,paciencia=2)),d,v,rede,r);del rede
                controle=reproducao(p/'a',p/'b',c['reproducao'])
                import unittest
                suite=unittest.defaultTestLoader.loadTestsFromName('tests_cryptomamba.test_adaptacao');resultado=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
                if not resultado.wasSuccessful() or resultado.skipped:raise ValueError('Testes reprovados.')
        if fontes()!=fs:raise ValueError('Fontes alteradas na qualificação.')
        salvar_json(p/'qualificacao.json',{'status':'aprovado','utc':agora(),'fontes':fs,'ambiente':ambiente(),'equivalencia':eq,'controle_sintetico':controle,'testes':resultado.testsRun,'skips':0,'ajustes_reais':0,
            'arquivos':{t.relative_to(p).as_posix():sha256(t) for t in p.rglob('*') if t.is_file()}})
    except BaseException:
        salvar_json(p/'falha.json',{'utc':agora(),'erro':traceback.format_exc()});raise
    return p/'qualificacao.json'


def validar_qualificacao(caminho):
    p=Path(caminho).resolve();q=ler_json(p)
    if q['status']!='aprovado' or q['fontes']!=fontes() or q['ambiente']!=ambiente() or q['ajustes_reais']!=0:raise ValueError('Qualificação divergente.')
    conferir_arquivos(p.parent,q['arquivos']);return p


def preparar(qualificacao):
    q=validar_qualificacao(qualificacao);c=configuracao();consumo,partes,refs=referencias()
    contrato={'configuracao':c,'fontes':fontes(),'ambiente':ambiente(),'consumo':consumo.especificacao.identidade,'referencias':{k:{'pasta':t.relative_to(RAIZ).as_posix(),'conclusao_sha256':sha256(t/'conclusao.json')} for k,t in refs.items()},'qualificacao':{'arquivo':q.relative_to(RAIZ).as_posix(),'sha256':sha256(q)},'protocolo_sha256':sha256(RAIZ/PROTOCOLO)}
    codigo=identidade(contrato)[:20];p=RAIZ/f'dados/experimentos/cryptomamba_adaptado_{codigo}'
    if p.exists() or (REGISTROS/'execucao.json').exists():raise FileExistsError('Já preparado; conferir sem duplicar.')
    p.mkdir(parents=True)
    for nome in contrato['fontes']:
        d=p/'fontes'/nome;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(RAIZ/nome,d)
    shutil.copy2(RAIZ/PROTOCOLO,p/'protocolo.md');salvar_json(p/'congelamento.json',{'id':codigo,'utc':agora(),'contrato':contrato});salvar_json(p/'progresso.json',{'status':'preparado','concluidos':[],'total':6})
    r={'id':codigo,'pasta':p.relative_to(RAIZ).as_posix(),'congelamento_sha256':sha256(p/'congelamento.json')};salvar_json(REGISTROS/'execucao.json',r);return r


def conferir_execucao():
    rp=ler_json(REGISTROS/'execucao.json');p=RAIZ/rp['pasta'];conferir_arquivos(p,{'congelamento.json':rp['congelamento_sha256']});f=ler_json(p/'congelamento.json');c=f['contrato']
    if f['id']!=rp['id'] or identidade(c)[:20]!=rp['id'] or c['configuracao']!=configuracao():raise ValueError('Identidade divergente.')
    conferir_arquivos(RAIZ,c['fontes']);conferir_arquivos(p/'fontes',c['fontes']);conferir_arquivos(p,{'protocolo.md':c['protocolo_sha256']});conferir_arquivos(RAIZ,{c['qualificacao']['arquivo']:c['qualificacao']['sha256']});validar_qualificacao(RAIZ/c['qualificacao']['arquivo'])
    consumo,partes,refs=referencias();atuais={k:{'pasta':t.relative_to(RAIZ).as_posix(),'conclusao_sha256':sha256(t/'conclusao.json')} for k,t in refs.items()}
    if atuais!=c['referencias'] or consumo.especificacao.identidade!=c['consumo']:raise ValueError('Dados/heranças alterados.')
    return p,f,consumo,partes,refs


def validar_autorizacao(caminho,codigo):
    a=ler_json(caminho)
    if a.get('execucao')!=codigo or a.get('seeds')!=SEEDS or a.get('ajustes_reais_total')!=6 or a.get('abordagem')!='cryptomamba_adaptado' or not a.get('mensagem_usuario'):raise ValueError('Autorização divergente.')
    return a


def executar(autorizacao,retomar=False):
    p,f,consumo,partes,refs=conferir_execucao();c=f['contrato']['configuracao'];a=validar_autorizacao(autorizacao,f['id'])
    with exclusividade(p,retomar):
        status=ler_json(p/'progresso.json')['status']
        if status=='concluido':raise ValueError('Executor encerrado não deve ser repetido.')
        if status!='preparado' and not retomar:raise ValueError('Retomada exige investigação.')
        if (p/'autorizacao.json').exists():
            if ler_json(p/'autorizacao.json')!=a:raise ValueError('Autorização alterada.')
        else:salvar_json(p/'autorizacao.json',a)
        prontas={}
        try:
            for s in ORDEM:
                raiz=p/'celulas'/f'cryptomamba_{s}';ant=sorted(raiz.glob('tentativa_*'));fechadas=[t for t in ant if (t/'conclusao.json').exists()]
                if len(fechadas)>1:raise ValueError('Tentativas ambíguas.')
                if fechadas:t=fechadas[0];conferir(t)
                else:
                    t=raiz/f'tentativa_{len(ant)+1:03d}';t.mkdir(parents=True);v={'execucao':f['id'],'seed':s,'familia':'cryptomamba_adaptado','identidade_consumo':consumo.especificacao.identidade,'configuracao':c}
                    salvar_json(t/'inicio.json',{'utc':agora(),'vinculo':v,'anteriores_preservadas':[x.name for x in ant]});salvar_json(p/'progresso.json',{'status':'executando','seed_atual':s,'concluidos':list(prontas),'total':6,'utc':agora()})
                    try:
                        with (t/'treinamento.log').open('w',encoding='utf-8',buffering=1) as log:
                            with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                                rede,r=ajustar(consumo,s,c,t,v)
                                if r['parametros']!=c['parametros_esperados']:raise ValueError('Capacidade inesperada.')
                                avaliar(consumo,partes,c,t,v,rede,r);del rede
                        selar(t)
                    except BaseException:
                        salvar_json(t/'falha.json',{'utc':agora(),'erro':traceback.format_exc()});raise
                prontas[s]=t
            conferir_arquivos(RAIZ,f['contrato']['fontes'])
            for t in prontas.values():conferir(t)
            publicar(p,c,partes,prontas,refs);salvar_json(p/'progresso.json',{'status':'concluido','concluidos':list(prontas),'total':6,'utc':agora()})
        except BaseException:
            salvar_json(p/'progresso.json',{'status':'interrompido','concluidos':list(prontas),'total':6,'utc':agora(),'erro':traceback.format_exc()});raise


def conferir_conclusao():
    import torch
    p,f,consumo,partes,refs=conferir_execucao();assert ler_json(p/'progresso.json')['status']=='concluido' and not ler_json(p/'processo.json')['ativo']
    assert set(ler_json(p/'progresso.json')['concluidos'])==set(SEEDS)
    pp=ler_json(p/'publicacao.json');pub=p/pp['pasta'];conferir_arquivos(pub,{'manifesto.json':pp['manifesto_sha256']});conferir_arquivos(pub,ler_json(pub/'manifesto.json')['arquivos']);rp=ler_json(pub/'resultados.json');assert rp['novos']==6 and rp['herdados']==53
    auditoria={}
    for s in SEEDS:
        ts=[t for t in (p/'celulas'/f'cryptomamba_{s}').glob('tentativa_*') if (t/'conclusao.json').exists()];assert len(ts)==1;t=ts[0];conferir(t);r=ler_json(t/'resultado.json');sel=ler_json(t/'selecao.json')
        assert r['recarga_exata'] and r['parametros']==139317;conferir_arquivos(t,{sel['arquivo']:sel['sha256']});m=torch.load(t/sel['arquivo'],map_location='cpu',weights_only=True)['modelo']
        assert m['familia']=='cryptomamba_adaptado' and m['especificacao']['identidade']==f['contrato']['consumo'] and m['configuracao']==f['contrato']['configuracao']
        assert list(m['pesos']['adaptacao_temporal.weight'].shape)==[14,168] and sum(v.numel() for v in m['pesos'].values())==139317
        aa=[v for k,v in m['pesos'].items() if k.endswith('A_log')];assert len(aa)==12 and all(v.shape[1]==64 for v in aa)
        melhor=min(ler_json(t/'epocas.json'),key=lambda e:(e['mse_validacao'],e['epoca']));assert melhor['epoca']==sel['epoca']==r['epoca_selecionada'] and melhor['mse_validacao']==sel['mse_validacao']==r['metricas']['validacao']['mse']
        auditoria[str(s)]={b:conferir_previsoes(pd.read_parquet(t/f'previsoes_{b}.parquet'),partes[b],r['metricas'].get(b)) for b in ('validacao','teste','operacional')}
    d=REGISTROS/'conferencias'/uuid4().hex;d.mkdir(parents=True);salvar_json(d/'conclusao.json',{'status':'aprovado','utc':agora(),'execucao':f['id'],'novos':6,'herdados':53,'auditoria':auditoria,'publicacao':pub.relative_to(RAIZ).as_posix(),'limites':'Checkpoint/seleção/capacidade/métricas conferidos; recarga e operação atestadas pelo executor.'})
    recibo={'arquivo':(d/'conclusao.json').relative_to(RAIZ).as_posix(),'sha256':sha256(d/'conclusao.json')};salvar_json(REGISTROS/'conferencia_conclusao.json',recibo);return recibo
