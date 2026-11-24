"""Duas execuções imutáveis de seis ajustes; nenhuma alteração nas rodadas16/8."""
import contextlib
import shutil
import traceback
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd
from infraestrutura.artefatos import RAIZ,agora,identidade,ler_json,salvar_json,sha256,conferir_arquivos,fontes as listar_fontes
from treinamento.ambiente import conferir as ambiente
from treinamento.preservacao import publicar as selar,conferir,exclusividade
from treinamento.ciclo import reproducao
from treinamento.neural import ajustar
from treinamento.avaliar import avaliar
from modelos.consumo import ConsumoModelos
from experimento_estado_mamba.ciclo import conferir_execucao as abrir_estado8, fontes as fontes_estado8
from avaliacao.publicacao import conferir_previsoes,contraste_temporal
from .publicacao import publicar

REGISTROS=RAIZ/'registros/estados_ampliados'
SEEDS=[17,42,2026,7,123,31415]
ORDEM=[42,17,2026,7,123,31415]
PARAMETROS={32:26401,64:38689}


def registro(estado):
    if type(estado) is not int or estado not in (32,64):
        raise ValueError('Rodadas delimitadas a32/64.')
    return REGISTROS/f'estado{estado}'


def configuracao(estado):
    registro(estado)
    c=ler_json(RAIZ/f'configuracoes/mamba_estado{estado}_001.json')
    b=ler_json(RAIZ/'configuracoes/mamba_estado8_001.json')
    if set(c)!=set(b):raise ValueError('Campos divergentes.')
    for k in set(b)-{'versao','ciclo','hipotese','configuracao_modelos','mamba'}:
        if c[k]!=b[k]:raise ValueError(f'Fator extra alterado: {k}')
    if c['mamba']!=dict(b['mamba'],estado=estado) or c['seeds']!=SEEDS:
        raise ValueError('Estado/seeds fora do desenho.')
    arq=ler_json(RAIZ/c['configuracao_modelos']);esperado=ler_json(RAIZ/'configuracoes/modelos_mamba_estado8_001.json')
    esperado['mamba']['estado']=estado
    if arq!=esperado:raise ValueError('Arquitetura contém outra diferença.')
    return c


def fontes():
    f=fontes_estado8()
    f.update(listar_fontes('experimento_estados_ampliados','tests_estados_ampliados'))
    for estado in (32,64):
        for nome in (f'configuracoes/mamba_estado{estado}_001.json',f'configuracoes/modelos_mamba_estado{estado}_001.json'):
            f[nome]=sha256(RAIZ/nome)
    f['run_estados_ampliados.py']=sha256(RAIZ/'run_estados_ampliados.py')
    return f


def referencias_base():
    pasta,f,consumo,partes,refs=abrir_estado8()
    if f['id']!='dcf4b0ed9012f7247bce' or ler_json(pasta/'progresso.json')['status']!='concluido':
        raise ValueError('Estado8 não está encerrado/compatível.')
    pub=ler_json(pasta/'publicacao.json');p=pasta/pub['pasta']
    conferir_arquivos(p,{'manifesto.json':pub['manifesto_sha256']});conferir_arquivos(p,ler_json(p/'manifesto.json')['arquivos'])
    refs=dict(refs)
    for s in SEEDS:
        t=pasta/'celulas'/f'mamba_{s}'/'tentativa_001';conferir(t);refs[f'estado8_{s}']=t
    return consumo,partes,refs


def qualificar(estado):
    from tests_modelos.apoio import conjunto
    pasta=registro(estado)/'qualificacoes'/uuid4().hex;pasta.mkdir(parents=True)
    originais=fontes()
    for nome in originais:
        destino=pasta/'fontes'/nome;destino.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(RAIZ/nome,destino)
    salvar_json(pasta/'inicio.json',{'utc':agora(),'fontes':originais,'estado':estado,'natureza':'somente sintético'})
    try:
        c=configuracao(estado);consumo=ConsumoModelos(conjunto(),f'qualificacao_estado{estado}_sintetica')
        vinculo={'natureza':'sintetico','estado':estado}
        with (pasta/'qualificacao.log').open('w',encoding='utf-8',buffering=1) as log:
            with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                for nome in ('a','b'):
                    destino=pasta/nome;destino.mkdir()
                    rede,r=ajustar(consumo,'mamba',42,dict(c['treino'],epocas=2,paciencia=2),RAIZ/c['configuracao_modelos'],destino,vinculo)
                    assert r['parametros']==PARAMETROS[estado]
                    assert all(list(v.shape)==[64,estado] for k,v in rede.state_dict().items() if k.endswith('A_log'))
                    avaliar(consumo,consumo._conjunto.partes,'mamba',c,destino,vinculo,rede,r)
                    del rede
                controle=reproducao(pasta/'a',pasta/'b',c['reproducao'])
                import unittest
                suite=unittest.defaultTestLoader.loadTestsFromName('tests_estados_ampliados.test_sequencia')
                resultado=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
                if not resultado.wasSuccessful() or resultado.skipped:raise ValueError('Testes reprovados.')
        if fontes()!=originais:raise ValueError('Fontes mudaram durante qualificação.')
        salvar_json(pasta/'qualificacao.json',{'status':'aprovado','utc':agora(),'estado':estado,'fontes':originais,
            'ambiente':ambiente(),'controle_sintetico':controle,'parametros':PARAMETROS[estado],
            'testes_orquestracao':resultado.testsRun,'skips':0,'ajustes_reais':0,
            'arquivos':{p.relative_to(pasta).as_posix():sha256(p) for p in pasta.rglob('*') if p.is_file()}})
    except BaseException:
        salvar_json(pasta/'falha.json',{'utc':agora(),'erro':traceback.format_exc()});raise
    return pasta/'qualificacao.json'


def validar_qualificacao(caminho,estado):
    qpath=Path(caminho).resolve();q=ler_json(qpath)
    if (q['status']!='aprovado' or q['estado']!=estado or q['fontes']!=fontes()
            or q['ambiente']!=ambiente() or q['ajustes_reais']!=0):
        raise ValueError('Qualificação divergente.')
    conferir_arquivos(qpath.parent,q['arquivos'])
    return qpath


def preparar(estado,qualificacao,dependencia32=None):
    c=configuracao(estado);qpath=validar_qualificacao(qualificacao,estado)
    if (estado==64)!=(dependencia32 is not None):raise ValueError('64 exige identidade32 pré-fixada.')
    consumo,partes,refs=referencias_base()
    contrato={'estado':estado,'configuracao':c,'fontes':fontes(),'ambiente':ambiente(),
        'consumo':consumo.especificacao.identidade,
        'referencias':{k:{'pasta':p.relative_to(RAIZ).as_posix(),'conclusao_sha256':sha256(p/'conclusao.json')} for k,p in refs.items()},
        'qualificacao':{'arquivo':qpath.relative_to(RAIZ).as_posix(),'sha256':sha256(qpath)},
        'protocolo_sha256':sha256(RAIZ/'docs/protocolo_estados32_64.md'),'dependencia32':dependencia32}
    codigo=identidade(contrato)[:20];pasta=RAIZ/f'dados/experimentos/estados_ampliados_{estado}_{codigo}'
    if pasta.exists() or (registro(estado)/'execucao.json').exists():raise FileExistsError('Preparação já existe; conferir.')
    pasta.mkdir(parents=True)
    for nome in contrato['fontes']:
        destino=pasta/'fontes'/nome;destino.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(RAIZ/nome,destino)
    shutil.copy2(RAIZ/'docs/protocolo_estados32_64.md',pasta/'protocolo.md')
    salvar_json(pasta/'congelamento.json',{'id':codigo,'utc':agora(),'contrato':contrato})
    salvar_json(pasta/'progresso.json',{'status':'preparado','concluidos':[]})
    p={'id':codigo,'pasta':pasta.relative_to(RAIZ).as_posix(),'congelamento_sha256':sha256(pasta/'congelamento.json')}
    salvar_json(registro(estado)/'execucao.json',p)
    return p


def validar_congelamento(p,estado):
    pasta=RAIZ/p['pasta'];conferir_arquivos(pasta,{'congelamento.json':p['congelamento_sha256']})
    f=ler_json(pasta/'congelamento.json');c=f['contrato']
    if p['id']!=f['id'] or f['id']!=identidade(c)[:20] or c['estado']!=estado:raise ValueError('Identidade divergente.')
    conferir_arquivos(RAIZ,c['fontes']);conferir_arquivos(pasta/'fontes',c['fontes'])
    conferir_arquivos(pasta,{'protocolo.md':c['protocolo_sha256']})
    conferir_arquivos(RAIZ,{c['qualificacao']['arquivo']:c['qualificacao']['sha256']})
    validar_qualificacao(RAIZ/c['qualificacao']['arquivo'],estado)
    if c['ambiente']!=ambiente():raise ValueError('Ambiente divergente.')
    return pasta,f


def conferir_execucao(estado):
    p=ler_json(registro(estado)/'execucao.json');pasta,f=validar_congelamento(p,estado);c=f['contrato']
    consumo,partes,refs=referencias_base()
    if c['consumo']!=consumo.especificacao.identidade:raise ValueError('Contrato de dados divergente.')
    for k,d in c['referencias'].items():
        if refs[k].relative_to(RAIZ).as_posix()!=d['pasta'] or sha256(refs[k]/'conclusao.json')!=d['conclusao_sha256']:
            raise ValueError('Herança alterada.')
    if estado==64:
        base32,f32=validar_congelamento(c['dependencia32'],32)
        if ler_json(base32/'progresso.json')['status']!='concluido':raise ValueError('32 deve concluir antes de64.')
        a=ler_json(registro(32)/'conferencia_conclusao.json')
        conferir_arquivos(RAIZ,{a['arquivo']:a['sha256']})
        if ler_json(RAIZ/a['arquivo'])['execucao']!=f32['id']:raise ValueError('Auditoria32 incompatível.')
        pp=ler_json(base32/'publicacao.json');conferir_arquivos(base32/pp['pasta'],{'manifesto.json':pp['manifesto_sha256']})
        conferir_arquivos(base32/pp['pasta'],ler_json(base32/pp['pasta']/'manifesto.json')['arquivos'])
        for s in SEEDS:
            completas=[t for t in (base32/'celulas'/f'mamba_{s}').glob('tentativa_*') if (t/'conclusao.json').exists()]
            if len(completas)!=1:raise ValueError('Cobertura32 ambígua.')
            conferir(completas[0]);refs[f'estado32_{s}']=completas[0]
    return pasta,f,consumo,partes,refs


def validar_autorizacao(caminho,estado,codigo):
    a=ler_json(caminho)
    if (a.get('ordem')!=[32,64] or a.get('ajustes_reais_total')!=12 or a.get('seeds')!=SEEDS
            or a.get('execucoes',{}).get(str(estado))!=codigo or not a.get('mensagem_usuario')):
        raise ValueError('Autorização incompatível com sequência de12 ajustes.')
    return a


def executar(estado,autorizacao,retomar=False):
    pasta,f,consumo,partes,refs=conferir_execucao(estado);c=f['contrato']['configuracao']
    a=validar_autorizacao(autorizacao,estado,f['id'])
    with exclusividade(pasta,retomar):
        status=ler_json(pasta/'progresso.json')['status']
        if status=='concluido':raise ValueError('Executor encerrado não deve ser chamado novamente.')
        if status!='preparado' and not retomar:raise ValueError('Retomada exige investigação explícita.')
        auth=pasta/'autorizacao.json'
        if auth.exists() and ler_json(auth)!=a:raise ValueError('Não substituir autorização.')
        if not auth.exists():salvar_json(auth,a)
        prontas={}
        try:
            for seed in ORDEM:
                raiz=pasta/'celulas'/f'mamba_{seed}';anteriores=sorted(raiz.glob('tentativa_*'))
                fechadas=[t for t in anteriores if (t/'conclusao.json').exists()]
                if len(fechadas)>1:raise ValueError('Não selecionar entre tentativas concluídas.')
                if fechadas:t=fechadas[0];conferir(t)
                else:
                    t=raiz/f'tentativa_{len(anteriores)+1:03d}';t.mkdir(parents=True)
                    vinculo={'execucao':f['id'],'seed':seed,'estado':estado,'identidade_consumo':consumo.especificacao.identidade,'treino':c['treino']}
                    salvar_json(t/'inicio.json',{'utc':agora(),'vinculo':vinculo,'anteriores_preservadas':[p.name for p in anteriores]})
                    salvar_json(pasta/'progresso.json',{'status':'executando','atual':seed,'concluidos':list(prontas),'utc':agora()})
                    try:
                        with (t/'treinamento.log').open('w',encoding='utf-8',buffering=1) as log:
                            with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                                rede,r=ajustar(consumo,'mamba',seed,c['treino'],RAIZ/c['configuracao_modelos'],t,vinculo)
                                if r['parametros']!=PARAMETROS[estado]:raise ValueError('Modelo tem capacidade inesperada.')
                                avaliar(consumo,partes,'mamba',c,t,vinculo,rede,r);del rede
                        selar(t)
                    except BaseException:
                        salvar_json(t/'falha.json',{'utc':agora(),'erro':traceback.format_exc()});raise
                prontas[seed]=t
            if set(prontas)!=set(SEEDS):raise ValueError('Cobertura incompleta.')
            conferir_arquivos(RAIZ,f['contrato']['fontes'])
            for t in prontas.values():conferir(t)
            publicar(pasta,c,partes,prontas,refs,estado)
            salvar_json(pasta/'progresso.json',{'status':'concluido','concluidos':list(prontas),'utc':agora()})
        except BaseException:
            salvar_json(pasta/'progresso.json',{'status':'interrompido','concluidos':list(prontas),'utc':agora(),'erro':traceback.format_exc()});raise


def conferir_conclusao(estado):
    """Leitura posterior; nunca chama executar para regenerar resultados."""
    import torch
    p=ler_json(registro(estado)/'execucao.json');pasta,f=validar_congelamento(p,estado)
    e=ler_json(pasta/'progresso.json');assert e['status']=='concluido' and set(e['concluidos'])==set(SEEDS)
    assert not ler_json(pasta/'processo.json')['ativo']
    pp=ler_json(pasta/'publicacao.json');pub=pasta/pp['pasta'];conferir_arquivos(pub,{'manifesto.json':pp['manifesto_sha256']})
    conferir_arquivos(pub,ler_json(pub/'manifesto.json')['arquivos']);c=f['contrato']['configuracao']
    partes={b:pd.read_parquet(RAIZ/c['entradas_pasta']/f'{b}.parquet') for b in ('validacao','teste','operacional')}
    auditoria={}
    for s in SEEDS:
        ts=[t for t in (pasta/'celulas'/f'mamba_{s}').glob('tentativa_*') if (t/'conclusao.json').exists()];assert len(ts)==1
        t=ts[0];conferir(t);r=ler_json(t/'resultado.json');assert r['recarga_exata'] and r['parametros']==PARAMETROS[estado]
        selecao=ler_json(t/'selecao.json');conferir_arquivos(t,{selecao['arquivo']:selecao['sha256']})
        modelo=torch.load(t/selecao['arquivo'],map_location='cpu',weights_only=True)['modelo']
        assert modelo['configuracao']['mamba']['estado']==estado and modelo['especificacao']['identidade']==f['contrato']['consumo']
        estados=[v for k,v in modelo['pesos'].items() if k.endswith('A_log')]
        assert len(estados)==2 and all(list(v.shape)==[64,estado] for v in estados)
        assert sum(v.numel() for v in modelo['pesos'].values())==PARAMETROS[estado]
        epocas=ler_json(t/'epocas.json');melhor=min(epocas,key=lambda x:(x['mse_validacao'],x['epoca']))
        assert melhor['epoca']==selecao['epoca']==r['epoca_selecionada']
        assert melhor['mse_validacao']==selecao['mse_validacao']==r['metricas']['validacao']['mse']
        auditoria[str(s)]={b:conferir_previsoes(pd.read_parquet(t/f'previsoes_{b}.parquet'),partes[b],r['metricas'].get(b)) for b in partes}
    destino=registro(estado)/'conferencias'/uuid4().hex;destino.mkdir(parents=True)
    salvar_json(destino/'conclusao.json',{'status':'aprovado','utc':agora(),'execucao':f['id'],'estado':estado,'ajustes_novos':6,
        'auditoria':auditoria,'publicacao':pub.relative_to(RAIZ).as_posix(),'publicacao_manifesto_sha256':pp['manifesto_sha256'],
        'limites':'Conferência de cobertura, hashes, capacidade/checkpoints e métricas; recarga preditiva e operação atestadas pelo executor/publicação.'})
    recibo={'arquivo':(destino/'conclusao.json').relative_to(RAIZ).as_posix(),'sha256':sha256(destino/'conclusao.json')}
    salvar_json(registro(estado)/'conferencia_conclusao.json',recibo)
    return recibo


def estado_atual(estado):
    p=ler_json(registro(estado)/'execucao.json')
    return ler_json(RAIZ/p['pasta']/'progresso.json')['status']


def executar_fila(autorizacao,retomar=False):
    pasta=REGISTROS/'fila';pasta.mkdir(parents=True,exist_ok=True)
    fila=ler_json(pasta/'congelamento.json');a=ler_json(autorizacao)
    if fila['ordem']!=[32,64] or a['execucoes']!={str(n):fila['execucoes'][str(n)]['id'] for n in (32,64)}:
        raise ValueError('Fila/autorização divergentes.')
    with exclusividade(pasta,retomar):
        try:
            for n in (32,64):
                if ler_json(registro(n)/'execucao.json')!=fila['execucoes'][str(n)]:raise ValueError('Ponteiro alterado após congelar fila.')
                salvar_json(pasta/'progresso.json',{'status':'executando','estado_atual':n,'utc':agora()})
                status=estado_atual(n)
                if status!='concluido':
                    if status!='preparado' and not retomar:raise ValueError('Rodada interrompida; investigar antes de retomar.')
                    executar(n,autorizacao,retomar)
                # Apenas leitura de uma execução encerrada; não repete ajustes/publicação.
                conferir_conclusao(n)
                salvar_json(registro(n)/'estado.json',{'situacao':'concluido_conferido','utc':agora(),'estado':n,
                    'execucao':fila['execucoes'][str(n)],'ajustes_novos':6,'seeds':SEEDS})
            salvar_json(pasta/'progresso.json',{'status':'concluido_conferido','utc':agora(),'ordem':[32,64],'ajustes_reais_concluidos':12})
        except BaseException:
            salvar_json(pasta/'progresso.json',{'status':'interrompido','utc':agora(),'erro':traceback.format_exc()});raise
