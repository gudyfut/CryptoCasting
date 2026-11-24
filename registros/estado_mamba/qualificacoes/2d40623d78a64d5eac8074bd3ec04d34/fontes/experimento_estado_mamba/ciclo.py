"""Seis ajustes Mamba; componentes de R0 reutilizados sem alterar suas fontes."""
import contextlib
import shutil
import traceback
from pathlib import Path
from uuid import uuid4
from infraestrutura.artefatos import RAIZ,agora,identidade,ler_json,salvar_json,sha256,conferir_arquivos,fontes as listar_fontes
from treinamento.ambiente import conferir as ambiente
from treinamento.preservacao import publicar as selar,conferir,exclusividade
from treinamento.ciclo import conferir_execucao as conferir_r0,reproducao
from treinamento.neural import ajustar
from treinamento.avaliar import avaliar
from modelos.consumo import ConsumoModelos
from modelos.neurais import criar_rede
from .publicacao import publicar

CONFIG='configuracoes/mamba_estado8_001.json'
REGISTROS=RAIZ/'registros/estado_mamba'


def configuracao():
    c=ler_json(RAIZ/CONFIG)
    b=ler_json(RAIZ/'configuracoes/treinamento_ohlcv24_001.json')
    especiais={'versao','ciclo','hipotese','modelos','seeds','controles_reproducao','configuracao_modelos','mamba'}
    extras={'referencia_execucao','seeds_pareadas','controle'}
    if set(c)!=set(b)|extras:
        raise ValueError('Campo desconhecido ou ausente.')
    for k in set(b)-especiais:
        if c[k]!=b[k]:
            raise ValueError(f'Mais de uma alteração científica: {k}')
    esperado=dict(b['mamba'],estado=8)
    if (c['mamba']!=esperado or c['seeds']!=[17,42,2026,7,123,31415]
            or c['modelos']!=['mamba'] or c['controles_reproducao']!=[] or c['seeds_pareadas']!=[17,42,2026]
            or c['referencia_execucao']!='ab5baf3eab3a2e66d8b2'):
        raise ValueError('Extensão delimitada a estado8 e seis seeds predefinidas.')
    arq=ler_json(RAIZ/c['configuracao_modelos']);original=ler_json(RAIZ/b['configuracao_modelos'])
    original['mamba']['estado']=8
    if arq!=original:
        raise ValueError('Arquitetura contém diferença adicional.')
    return c


def fontes():
    f=listar_fontes('experimento_estado_mamba','treinamento','avaliacao','modelos','entradas_modelo','mercado_binance','infraestrutura','tests_modelos')
    for p in [CONFIG,'configuracoes/modelos_mamba_estado8_001.json','configuracoes/modelos_ohlcv24_001.json',
              'configuracoes/treinamento_ohlcv24_001.json','run_estado_mamba.py']:
        f[p]=sha256(RAIZ/p)
    return f


def referencias():
    pasta,f,consumo,partes=conferir_r0()
    if f['id']!='ab5baf3eab3a2e66d8b2' or ler_json(pasta/'progresso.json')['status']!='concluido':
        raise ValueError('Referência não concluída/compatível.')
    caminhos={}
    for modelo in ('mamba','lstm'):
        for s in (17,42,2026):
            chave=f'estado16_{s}' if modelo=='mamba' else f'lstm_{s}'
            caminhos[chave]=pasta/'celulas'/f'{modelo}_{s}'/'tentativa_001'
    for m in ('naive','arima'):
        caminhos[m]=pasta/'celulas'/m/'tentativa_001'
    for p in caminhos.values():
        conferir(p)
    return consumo,partes,caminhos


def qualificar():
    from tests_modelos.apoio import conjunto
    from modelos.neurais import prever_neural
    pasta=REGISTROS/'qualificacoes'/uuid4().hex;pasta.mkdir(parents=True)
    originais=fontes()
    for nome in originais:
        destino=pasta/'fontes'/nome;destino.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(RAIZ/nome,destino)
    salvar_json(pasta/'inicio.json',{'utc':agora(),'fontes':originais,'natureza':'sintético; zero ajustes reais'})
    try:
        c=configuracao();consumo=ConsumoModelos(conjunto(),'qualificacao_estado8_sintetica')
        vinculo={'natureza':'sintetico','estado':8}
        with (pasta/'qualificacao.log').open('w',encoding='utf-8',buffering=1) as log:
            with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                for n in ('a','b'):
                    destino=pasta/n;destino.mkdir()
                    rede,r=ajustar(consumo,'mamba',42,dict(c['treino'],epocas=2,paciencia=2),RAIZ/c['configuracao_modelos'],destino,vinculo)
                    assert r['parametros']==17185
                    avaliar(consumo,consumo._conjunto.partes,'mamba',c,destino,vinculo,rede,r)
                    del rede
                controle=reproducao(pasta/'a',pasta/'b',c['reproducao'])
                anterior=criar_rede('mamba',consumo.especificacao,RAIZ/'configuracoes/modelos_ohlcv24_001.json')
                assert sum(p.numel() for p in anterior.parameters())==20257
        if fontes()!=originais:
            raise ValueError('Fontes mudaram durante qualificação.')
        salvar_json(pasta/'qualificacao.json',{'status':'aprovado','utc':agora(),'fontes':originais,'ambiente':ambiente(),
                    'controle_sintetico':controle,'parametros_antes':20257,'parametros_depois':17185,'ajustes_reais':0,
                    'verificacoes':['apenas d_state alterado','seis seeds únicas e três pareadas','forward/backward e atualização',
                       'reprodução de ajuste curto sintético','seleção e recarga exata em três populações','mesmo contrato cinco canais168h'],
                    'arquivos':{p.relative_to(pasta).as_posix():sha256(p) for p in pasta.rglob('*') if p.is_file()}})
    except BaseException:
        salvar_json(pasta/'falha.json',{'utc':agora(),'erro':traceback.format_exc()});raise
    return pasta/'qualificacao.json'


def preparar(qualificacao):
    c=configuracao();qpath=Path(qualificacao).resolve();q=ler_json(qpath)
    if q['status']!='aprovado' or q['fontes']!=fontes() or q['ambiente']!=ambiente():
        raise ValueError('Qualificação divergente.')
    conferir_arquivos(qpath.parent,q['arquivos'])
    consumo,partes,refs=referencias()
    contrato={'configuracao':c,'fontes':fontes(),'ambiente':ambiente(),'consumo':consumo.especificacao.identidade,
        'referencias':{k:{'pasta':p.relative_to(RAIZ).as_posix(),'conclusao_sha256':sha256(p/'conclusao.json')} for k,p in refs.items()},
        'qualificacao':{'arquivo':qpath.relative_to(RAIZ).as_posix(),'sha256':sha256(qpath)},
        'protocolo_sha256':sha256(RAIZ/'docs/protocolo_estado_mamba.md')}
    codigo=identidade(contrato)[:20];pasta=RAIZ/f'dados/experimentos/estado_mamba_{codigo}'
    if pasta.exists():
        raise FileExistsError('Preparação já existe: conferir, não duplicar.')
    pasta.mkdir(parents=True)
    for nome in contrato['fontes']:
        destino=pasta/'fontes'/nome;destino.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(RAIZ/nome,destino)
    shutil.copy2(RAIZ/'docs/protocolo_estado_mamba.md',pasta/'protocolo.md')
    salvar_json(pasta/'congelamento.json',{'id':codigo,'utc':agora(),'contrato':contrato})
    salvar_json(pasta/'progresso.json',{'status':'preparado','concluidos':[]})
    ponteiro={'id':codigo,'pasta':pasta.relative_to(RAIZ).as_posix(),'congelamento_sha256':sha256(pasta/'congelamento.json')}
    salvar_json(REGISTROS/'execucao.json',ponteiro)
    return ponteiro


def conferir_execucao():
    p=ler_json(REGISTROS/'execucao.json');pasta=RAIZ/p['pasta']
    conferir_arquivos(pasta,{'congelamento.json':p['congelamento_sha256']})
    f=ler_json(pasta/'congelamento.json');c=f['contrato']
    if f['id']!=identidade(c)[:20] or f['id']!=p['id']:
        raise ValueError('Identidade divergente.')
    conferir_arquivos(RAIZ,c['fontes']);conferir_arquivos(pasta/'fontes',c['fontes'])
    conferir_arquivos(pasta,{'protocolo.md':c['protocolo_sha256']})
    conferir_arquivos(RAIZ,{c['qualificacao']['arquivo']:c['qualificacao']['sha256']})
    qpath=RAIZ/c['qualificacao']['arquivo'];q=ler_json(qpath);conferir_arquivos(qpath.parent,q['arquivos'])
    if q['status']!='aprovado' or q['fontes']!=c['fontes'] or ambiente()!=c['ambiente']:
        raise ValueError('Ambiente/qualificação divergentes.')
    consumo,partes,refs=referencias()
    if consumo.especificacao.identidade!=c['consumo']:
        raise ValueError('Dados divergentes.')
    for k,p in refs.items():
        if relativo_ref(p)!=c['referencias'][k]['pasta'] or sha256(p/'conclusao.json')!=c['referencias'][k]['conclusao_sha256']:
            raise ValueError('Referência herdada alterada.')
    return pasta,f,consumo,partes,refs


def relativo_ref(p):
    return p.relative_to(RAIZ).as_posix()


def executar(autorizacao,retomar=False):
    pasta,f,consumo,partes,refs=conferir_execucao();c=f['contrato']['configuracao']
    a=ler_json(autorizacao)
    if a.get('execucao')!=f['id'] or a.get('seeds')!=c['seeds'] or a.get('ajustes_reais')!=6 or not a.get('mensagem_usuario'):
        raise ValueError('Autorização incompatível com seis ajustes.')
    with exclusividade(pasta,retomar):
        estado=ler_json(pasta/'progresso.json')
        if estado['status']=='concluido':
            raise ValueError('Execução encerrada: não chamar novamente.')
        if estado['status']!='preparado' and not retomar:
            raise ValueError('Retomada exige investigação.')
        auth=pasta/'autorizacao.json'
        if auth.exists() and ler_json(auth)!=a:
            raise ValueError('Não substituir autorização.')
        if not auth.exists():
            salvar_json(auth,a)
        prontas={}
        try:
            for seed in [42,17,2026,7,123,31415]:
                raiz=pasta/'celulas'/f'mamba_{seed}';anteriores=sorted(raiz.glob('tentativa_*'))
                completas=[p for p in anteriores if (p/'conclusao.json').exists()]
                if len(completas)>1:
                    raise ValueError('Mais de uma tentativa concluída; não selecionar resultado.')
                if completas:
                    t=completas[0];conferir(t)
                else:
                    t=raiz/f'tentativa_{len(anteriores)+1:03d}';t.mkdir(parents=True)
                    vinculo={'execucao':f['id'],'seed':seed,'estado':8,'identidade_consumo':consumo.especificacao.identidade,'treino':c['treino']}
                    salvar_json(t/'inicio.json',{'utc':agora(),'vinculo':vinculo,'anteriores_preservadas':[p.name for p in anteriores]})
                    salvar_json(pasta/'progresso.json',{'status':'executando','atual':seed,'concluidos':list(prontas),'utc':agora()})
                    try:
                        with (t/'treinamento.log').open('w',encoding='utf-8',buffering=1) as log:
                            with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                                rede,r=ajustar(consumo,'mamba',seed,c['treino'],RAIZ/c['configuracao_modelos'],t,vinculo)
                                avaliar(consumo,partes,'mamba',c,t,vinculo,rede,r)
                                del rede
                        selar(t)
                    except BaseException:
                        salvar_json(t/'falha.json',{'utc':agora(),'erro':traceback.format_exc()});raise
                prontas[seed]=t
            if set(prontas)!=set(c['seeds']):
                raise ValueError('Cobertura incompleta.')
            conferir_arquivos(RAIZ,f['contrato']['fontes'])
            for t in prontas.values():
                conferir(t)
            publicar(pasta,c,partes,prontas,refs)
            salvar_json(pasta/'progresso.json',{'status':'concluido','concluidos':list(prontas),'utc':agora()})
        except BaseException:
            salvar_json(pasta/'progresso.json',{'status':'interrompido','concluidos':list(prontas),'utc':agora(),'erro':traceback.format_exc()});raise
