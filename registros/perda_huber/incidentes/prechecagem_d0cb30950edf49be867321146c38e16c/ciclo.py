"""Uma hipótese, seis seeds; sem modificar executores ou artefatos anteriores."""
import ast
import contextlib
import inspect
import shutil
import traceback
import unittest
from pathlib import Path
from uuid import uuid4
from infraestrutura.artefatos import RAIZ,agora,ler_json,salvar_json,sha256,identidade,conferir_arquivos,fontes as listar_fontes
from modelos.consumo import carregar_consumo,ConsumoModelos
from treinamento.ambiente import conferir as ambiente_base
from treinamento.preservacao import conferir,publicar as selar,exclusividade
from treinamento.avaliar import avaliar
from treinamento.ciclo import reproducao
from .referencias import estudo_anterior,mapa_preservacao
from .treino import ajustar
from .perda import POLITICA

REG=RAIZ/'registros/perda_huber'
CONFIG='configuracoes/mamba16_perda_huber_001.json'
PROTOCOLO='docs/protocolo_perda_huber.md'
SEEDS=[17,42,2026,7,123,31415]
ORDEM=[42,17,2026,7,123,31415]


def configuracao():
    c=ler_json(RAIZ/CONFIG);b=ler_json(RAIZ/'configuracoes/mamba_estado16_complemento_001.json')
    if set(c)!=set(b)|{'perda'}:raise ValueError('Campos inesperados.')
    for k in set(b)-{'versao','ciclo','hipotese','controle'}:
        if c[k]!=b[k]:raise ValueError(f'Fator extra alterado:{k}')
    if c['perda']!=POLITICA or c['seeds']!=SEEDS:raise ValueError('Política/seeds inesperadas.')
    return c


def conferir_treinador():
    a=(RAIZ/'treinamento/neural.py').read_text(encoding='utf-8')
    b=(RAIZ/'experimentos/perda_huber/treino.py').read_text(encoding='utf-8')
    b=b.replace('from treinamento.otimizacao import fixar_seed, criar_otimizador\nfrom .perda import atualizar_lote',
                'from .otimizacao import fixar_seed, criar_otimizador, atualizar_lote')
    b=b.replace('from treinamento.selecao import','from .selecao import').replace('from treinamento import checkpoints','from . import checkpoints')
    b=b.replace("cfg['clipping'], cfg['perda'])", "cfg['clipping'])")
    b=b.replace("'taxa_aprendizado': otimizador.param_groups[0]['lr'], ", '')
    b=b.replace("'perda_treino_padronizada'", "'mse_treino_padronizado'")
    b=b.replace("'perda': cfg['perda'], ", '')
    aa,bb=ast.parse(a),ast.parse(b);aa.body=aa.body[1:];bb.body=bb.body[1:]
    if ast.dump(aa)!=ast.dump(bb):raise ValueError('Treinador diverge além da perda e sua identificação nos logs.')
    # Verificação separada da acumulação: só validação da política e fórmula mudam.
    from treinamento.otimizacao import atualizar_lote as anterior
    from .perda import atualizar_lote as novo
    antigo=ast.parse(inspect.getsource(anterior)); atual=ast.parse(inspect.getsource(novo))
    func=atual.body[0];func.args.args.pop()
    func.body.pop(0)  # import math adicional para validar delta
    # A condição original do contrato de lote permanece; só a política é adicionada.
    func.body[1].test=antigo.body[0].body[1].test
    for node in ast.walk(func):
        if isinstance(node,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='perda' for x in node.targets):
            node.value=ast.parse("torch.nn.functional.mse_loss(p, real, reduction='sum')",mode='eval').body
    if ast.dump(antigo)!=ast.dump(atual):raise ValueError('Atualização diverge além da perda/política.')
    return {'demais_instrucoes_iguais':True,'acumulacao_igual':True,'referencia_sha256':sha256(RAIZ/'treinamento/neural.py')}


def ambiente():
    import torch
    a=ambiente_base();a['perdas_instaladas_sha256']=sha256(Path(inspect.getfile(torch.nn.functional.huber_loss)))
    return a


def fontes():
    fs=listar_fontes('treinamento','avaliacao','modelos','entradas_modelo','mercado_binance','infraestrutura',
        'experimentos','experimentos/perda_huber','analises','tests_huber','tests_modelos','backtest_carteira','tests_backtest_carteira')
    for n in (CONFIG,PROTOCOLO,'configuracoes/modelos_ohlcv24_001.json','configuracoes/mamba_estado16_complemento_001.json',
              'configuracoes/entradas_ohlcv24_001.json','run_experimento.py'):fs[n]=sha256(RAIZ/n)
    return fs


def qualificar():
    from tests_modelos.apoio import conjunto
    from treinamento.neural import ajustar as referencia
    from unittest.mock import patch
    import torch
    p=REG/'qualificacoes'/uuid4().hex;p.mkdir(parents=True);fs=fontes()
    for n in fs:
        d=p/'fontes'/n;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(RAIZ/n,d)
    salvar_json(p/'inicio.json',{'utc':agora(),'fontes':fs,'ajustes_reais':0})
    try:
        c=configuracao();consumo=ConsumoModelos(conjunto(),'huber_sintetico');v={'natureza':'sintetico','familia':'mamba16_huber'}
        with (p/'qualificacao.log').open('w',encoding='utf-8',buffering=1) as log:
            with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                ast_recebido=conferir_treinador()
                suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromName(n) for n in
                    ('tests_huber.test_ciclo','tests_backtest_carteira.test_carteira','tests_backtest_carteira.test_mercado')])
                r=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
                if not r.wasSuccessful() or r.skipped:raise ValueError('Qualificação reprovada.')
                max_residuo_quadratico=[]
                huber_original=torch.nn.functional.huber_loss
                def conferir_quadratica(entrada,alvo,**kw):
                    v=float((entrada-alvo).detach().abs().max().cpu())
                    assert v<kw['delta']==1e6
                    max_residuo_quadratico.append(v)
                    return huber_original(entrada,alvo,**kw)
                for nome in ('a','b','quadratica','referencia'):
                    d=p/nome;d.mkdir();cfg=dict(c,treino=dict(c['treino'],epocas=2,paciencia=2))
                    treino=dict(cfg['treino'],perda=dict(c['perda'],delta=1e6) if nome=='quadratica' else c['perda'])
                    fn=referencia if nome=='referencia' else ajustar
                    contexto=patch('torch.nn.functional.huber_loss',side_effect=conferir_quadratica) if nome=='quadratica' else contextlib.nullcontext()
                    with contexto:
                        rede,aj=fn(consumo,'mamba',42,treino,RAIZ/c['configuracao_modelos'],d,v)
                    assert aj['parametros']==20257
                    avaliar(consumo,consumo._conjunto.partes,'mamba',cfg,d,v,rede,aj);del rede
                repeticao=reproducao(p/'a',p/'b',c['reproducao'])
                equivalencia=reproducao(p/'quadratica',p/'referencia',c['reproducao'])
        if fontes()!=fs:raise ValueError('Fonte mudou durante qualificação.')
        salvar_json(p/'qualificacao.json',{'status':'aprovado','utc':agora(),'fontes':fs,'ambiente':ambiente(),'ast':ast_recebido,
            'testes':r.testsRun,'skips':0,'ajustes_reais':0,'ajustes_sinteticos':4,'reproducao_sintetica':repeticao,'equivalencia_quadratica':equivalencia,
            'maior_residuo_controle_quadratico':max(max_residuo_quadratico),
            'arquivos':{q.relative_to(p).as_posix():sha256(q) for q in p.rglob('*') if q.is_file()}})
    except BaseException:
        salvar_json(p/'falha.json',{'utc':agora(),'erro':traceback.format_exc()});raise
    return p/'qualificacao.json'


def validar_qualificacao(caminho):
    p=Path(caminho).resolve();q=ler_json(p)
    if q['status']!='aprovado' or q['fontes']!=fontes() or q['ambiente']!=ambiente() or q['ajustes_reais']!=0:raise ValueError('Qualificação inválida/desatualizada.')
    conferir_arquivos(p.parent,q['arquivos']);return p


def preparar(qualificacao):
    if (REG/'execucao.json').exists():raise FileExistsError('Não duplicar execução preparada.')
    q=validar_qualificacao(qualificacao);c=configuracao();ptr,pub,r,refs=estudo_anterior()
    consumo=carregar_consumo(RAIZ/c['entradas_pasta']);guard=mapa_preservacao()
    diag=ler_json(RAIZ/'registros/diagnosticos_previsoes/atual.json');conferir_arquivos(RAIZ,{diag['arquivo']:diag['sha256']})
    contrato={'configuracao':c,'fontes':fontes(),'ambiente':ambiente(),'consumo':consumo.especificacao.identidade,
        'qualificacao':{'arquivo':q.relative_to(RAIZ).as_posix(),'sha256':sha256(q)},
        'referencias':{k:{'pasta':t.relative_to(RAIZ).as_posix(),'conclusao_sha256':sha256(t/'conclusao.json')} for k,t in refs.items()},
        'publicacao_anterior':pub.relative_to(RAIZ).as_posix(),'diagnostico_anterior':diag,
        'dependencias':{c[k]:sha256(RAIZ/c[k]/'manifesto.json') for k in ('entradas_pasta','mercado_pasta')},
        'protocolo_sha256':sha256(RAIZ/PROTOCOLO),'ast':conferir_treinador()}
    codigo=identidade(contrato)[:20];p=RAIZ/f'dados/experimentos/mamba16_perda_huber_{codigo}';p.mkdir(parents=True,exist_ok=False)
    for n in contrato['fontes']:
        d=p/'fontes'/n;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(RAIZ/n,d)
    shutil.copy2(RAIZ/PROTOCOLO,p/'protocolo.md');salvar_json(p/'congelamento.json',{'id':codigo,'utc':agora(),'contrato':contrato})
    salvar_json(p/'progresso.json',{'status':'preparado','concluidos':[],'total':6})
    salvar_json(REG/'preservacao_antes.json',{'utc':agora(),'arquivos':guard})
    pt={'id':codigo,'pasta':p.relative_to(RAIZ).as_posix(),'congelamento_sha256':sha256(p/'congelamento.json')}
    salvar_json(REG/'execucao.json',pt);salvar_json(REG/'estado.json',{'situacao':'preparado_qualificado','execucao':pt,'preservados':len(guard),'novos_planejados':6,'herdados':53})
    return pt


def conferir_execucao():
    ptr=ler_json(REG/'execucao.json');p=RAIZ/ptr['pasta'];conferir_arquivos(p,{'congelamento.json':ptr['congelamento_sha256']})
    f=ler_json(p/'congelamento.json');ct=f['contrato'];c=ct['configuracao']
    assert identidade(ct)[:20]==ptr['id']==f['id'] and c==configuracao() and ct['ambiente']==ambiente()
    conferir_arquivos(RAIZ,ct['fontes']);conferir_arquivos(p/'fontes',ct['fontes']);conferir_arquivos(p,{'protocolo.md':ct['protocolo_sha256']})
    validar_qualificacao(RAIZ/ct['qualificacao']['arquivo']);conferir_arquivos(RAIZ,{ct['qualificacao']['arquivo']:ct['qualificacao']['sha256']})
    conferir_arquivos(RAIZ,ler_json(REG/'preservacao_antes.json')['arquivos'])
    consumo=carregar_consumo(RAIZ/c['entradas_pasta']);assert consumo.especificacao.identidade==ct['consumo']
    for nome,h in ct['dependencias'].items():conferir_arquivos(RAIZ/nome,{'manifesto.json':h})
    refs={k:RAIZ/v['pasta'] for k,v in ct['referencias'].items()}
    for k,t in refs.items():conferir_arquivos(t,{'conclusao.json':ct['referencias'][k]['conclusao_sha256']});conferir(t)
    return p,f,consumo,consumo._conjunto.partes,refs


def validar_autorizacao(caminho,codigo):
    a=ler_json(caminho)
    if a.get('execucao')!=codigo or a.get('seeds')!=SEEDS or a.get('ajustes_reais_total')!=6 or a.get('abordagem')!='mamba16_perda_huber' or not a.get('mensagem_usuario'):raise ValueError('Autorização não corresponde ao escopo.')
    return a


def executar(autorizacao,retomar=False):
    p,f,consumo,partes,refs=conferir_execucao();c=f['contrato']['configuracao'];a=validar_autorizacao(autorizacao,f['id'])
    with exclusividade(p,retomar):
        status=ler_json(p/'progresso.json')['status']
        if status=='concluido':raise ValueError('Não repetir treinamento encerrado.')
        if status!='preparado' and not retomar:raise ValueError('Retomada exige investigação.')
        if (p/'autorizacao.json').exists():assert ler_json(p/'autorizacao.json')==a
        else:salvar_json(p/'autorizacao.json',a)
        prontas={}
        try:
            for s in ORDEM:
                raiz=p/'celulas'/f'mamba16_huber_{s}';ant=sorted(raiz.glob('tentativa_*'));fechadas=[t for t in ant if (t/'conclusao.json').exists()]
                if len(fechadas)>1:raise ValueError('Conclusões ambíguas.')
                if fechadas:t=fechadas[0];conferir(t)
                else:
                    t=raiz/f'tentativa_{len(ant)+1:03d}';t.mkdir(parents=True)
                    v={'execucao':f['id'],'seed':s,'familia':'mamba','identidade_consumo':consumo.especificacao.identidade,'configuracao':c}
                    salvar_json(t/'inicio.json',{'utc':agora(),'vinculo':v,'anteriores_preservadas':[x.name for x in ant]})
                    salvar_json(p/'progresso.json',{'status':'executando','seed_atual':s,'concluidos':list(prontas),'total':6,'utc':agora()})
                    try:
                        with (t/'treinamento.log').open('w',encoding='utf-8',buffering=1) as log:
                            with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                                rede,r=ajustar(consumo,'mamba',s,dict(c['treino'],perda=c['perda']),RAIZ/c['configuracao_modelos'],t,v)
                                if r['parametros']!=20257:raise ValueError('Capacidade inesperada.')
                                avaliar(consumo,partes,'mamba',c,t,v,rede,r);del rede
                        selar(t)
                    except BaseException:
                        salvar_json(t/'falha.json',{'utc':agora(),'erro':traceback.format_exc()});raise
                prontas[s]=t
            conferir_arquivos(RAIZ,f['contrato']['fontes']);conferir_arquivos(RAIZ,ler_json(REG/'preservacao_antes.json')['arquivos'])
            salvar_json(p/'progresso.json',{'status':'concluido','concluidos':list(prontas),'total':6,'utc':agora()})
        except BaseException:
            salvar_json(p/'progresso.json',{'status':'interrompido','concluidos':list(prontas),'total':6,'utc':agora(),'erro':traceback.format_exc()});raise
