"""Quatro blocos, oito seeds e duas perdas. Preparar não executa mercado."""
import contextlib
import inspect
import shutil
import traceback
import unittest
from pathlib import Path
from uuid import uuid4
from infraestrutura.artefatos import RAIZ, agora, ler_json, salvar_json, sha256, identidade, fontes as listar_fontes
from treinamento.ambiente import conferir as ambiente_base
from treinamento.neural import ajustar as ajustar_mse
from experimentos.perda_huber.treino import ajustar as ajustar_huber
from treinamento.avaliar import avaliar
from treinamento.preservacao import conferir, publicar as selar, exclusividade
from treinamento.ciclo import reproducao
from .dados import REG, CONFIG, SEEDS, configuracao, receita, carregar_blocos, Verificador, conferir_escalas_reais
from .preservacao import mapa_anterior

PROTOCOLO='docs/protocolo_huber_blocos.md'


def grade(c):
    itens=[]
    for b in c['blocos']:
        for s in c['ordem_seeds']:
            for perda in c['variantes']:itens.append({'bloco':b,'perda':perda,'seed':s,'controle':False})
            if b==c['controle_bloco'] and s==c['controle_seed']:
                for perda in c['variantes']:itens.append({'bloco':b,'perda':perda,'seed':s,'controle':True})
    return itens


def chave(item):return f'{item["bloco"]}_{item["perda"]}_{item["seed"]}'


def raiz_celula(p,item):return p/('controles' if item['controle'] else 'celulas')/chave(item)


def ambiente():
    import torch
    a=ambiente_base();a['perdas_instaladas_sha256']=sha256(Path(inspect.getfile(torch.nn.functional.huber_loss)))
    return a


def fontes():
    fs=listar_fontes('infraestrutura','mercado_binance','entradas_modelo','modelos','treinamento','avaliacao',
        'analises','experimentos','experimentos/perda_huber','experimentos/huber_blocos',
        'tests_modelos','tests_huber','tests_huber_blocos','backtest_carteira','tests_backtest_carteira')
    for n in (CONFIG,PROTOCOLO,'configuracoes/mamba16_perda_huber_001.json','configuracoes/entradas_ohlcv24_001.json',
              'configuracoes/modelos_ohlcv24_001.json','configuracoes/backtest_carteira_001.json'):
        fs[n]=sha256(RAIZ/n)
    return fs


def qualificar():
    from tests_modelos.apoio import conjunto
    from modelos.consumo import ConsumoModelos
    p=REG/'qualificacoes'/uuid4().hex;p.mkdir(parents=True);fs=fontes()
    for n in fs:
        d=p/'fontes'/n;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(RAIZ/n,d)
    salvar_json(p/'inicio.json',{'utc':agora(),'fontes':fs,'treinamentos_mercado':0})
    try:
        c=configuracao();consumos=carregar_blocos(ler_json(REG/'entradas.json'));dimensoes={}
        escalas_recalculadas=conferir_escalas_reais(c,consumos)
        for b,x in consumos.items():
            assert x._conjunto.contrato['divisao']==c['blocos'][b]
            assert x.especificacao.contexto==168 and x._conjunto.matriz.shape[1]==5
            dimensoes[b]={'matriz':list(x._conjunto.matriz.shape),'populacoes':{n:len(q) for n,q in x._conjunto.partes.items()},'escalas':x._conjunto.escalas}
        sintetico=ConsumoModelos(conjunto(),'blocos_sintetico');controle={}
        with (p/'qualificacao.log').open('w',encoding='utf-8',buffering=1) as log:
            with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromName(n) for n in
                    ('tests_huber_blocos.test_ciclo','tests_huber.test_ciclo',
                     'tests_backtest_carteira.test_carteira','tests_backtest_carteira.test_mercado')])
                r=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
                if not r.wasSuccessful() or r.skipped:raise ValueError('Qualificação reprovada.')
                for perda in c['variantes']:
                    cfg=receita(c,'B1',perda);cfg['treino']=dict(cfg['treino'],epocas=2,paciencia=2)
                    for nome in ('a','b'):
                        d=p/f'{perda}_{nome}';d.mkdir();v={'natureza':'sintetico','perda':perda}
                        tcfg=dict(cfg['treino'],perda=cfg['perda'])
                        fn=ajustar_huber if perda=='huber' else ajustar_mse
                        rede,aj=fn(sintetico,'mamba',42,tcfg,RAIZ/cfg['configuracao_modelos'],d,v)
                        assert aj['parametros']==20257
                        avaliar(sintetico,sintetico._conjunto.partes,'mamba',cfg,d,v,rede,aj);del rede
                    controle[perda]=reproducao(p/f'{perda}_a',p/f'{perda}_b',cfg['reproducao'])
        assert fontes()==fs
        salvar_json(p/'qualificacao.json',{'status':'aprovado','utc':agora(),'fontes':fs,'ambiente':ambiente(),
            'testes':r.testsRun,'skips':0,'ajustes_sinteticos':4,'treinamentos_mercado':0,
            'reproducao':controle,'dados_reais_sem_treino':dimensoes,'conferencia_independente_escalas':escalas_recalculadas,
            'arquivos':{q.relative_to(p).as_posix():sha256(q) for q in p.rglob('*') if q.is_file()}})
    except BaseException:
        salvar_json(p/'falha.json',{'utc':agora(),'erro':traceback.format_exc()});raise
    return p/'qualificacao.json'


def validar_qualificacao(q,v):
    q=Path(q).resolve();r=ler_json(q)
    assert r['status']=='aprovado' and r['fontes']==fontes() and r['ambiente']==ambiente()
    assert r['treinamentos_mercado']==0 and r['skips']==0
    v.arquivos_em(q.parent,r['arquivos']);return q,r


def preparar(qualificacao):
    if (REG/'execucao.json').exists():raise FileExistsError('Execução já preparada; não duplicar.')
    c=configuracao();v=Verificador();q,qr=validar_qualificacao(qualificacao,v)
    mapa=ler_json(REG/'entradas.json');consumos=carregar_blocos(mapa,v)
    guard=mapa_anterior();v.arquivos_em(RAIZ,guard)
    pb=RAIZ/c['carteira_execucao'];cb=ler_json(pb/'congelamento.json')
    assert cb['id']=='8ec8a66648313caa48e3'
    receitas={b:{perda:dict(receita(c,b,perda),entradas_pasta=mapa[b]['pasta']) for perda in c['variantes']} for b in c['blocos']}
    ct={'configuracao':c,'receitas':receitas,'entradas':mapa,'identidades_consumo':{b:x.especificacao.identidade for b,x in consumos.items()},
        'fontes':fontes(),'ambiente':ambiente(),'qualificacao':{'arquivo':q.relative_to(RAIZ).as_posix(),'sha256':sha256(q)},
        'carteira':{'pasta':c['carteira_execucao'],'congelamento_sha256':sha256(pb/'congelamento.json'),'contrato':cb['contrato']},
        'protocolo_sha256':sha256(RAIZ/PROTOCOLO),'preservacao_antes_sha256':identidade(guard),'grade':grade(c)}
    codigo=identidade(ct)[:20];p=RAIZ/f'dados/experimentos/huber_blocos_{codigo}';p.mkdir(parents=True,exist_ok=False)
    for n in ct['fontes']:
        d=p/'fontes'/n;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(RAIZ/n,d)
    shutil.copyfile(RAIZ/PROTOCOLO,p/'protocolo.md');salvar_json(p/'congelamento.json',{'id':codigo,'utc':agora(),'contrato':ct})
    salvar_json(p/'progresso.json',{'status':'preparado','concluidos':[],'principais_concluidos':0,'controles_concluidos':0,'total_principais':64,'total_reais':66})
    salvar_json(REG/'preservacao_antes.json',{'utc':agora(),'arquivos':guard})
    pt={'id':codigo,'pasta':p.relative_to(RAIZ).as_posix(),'congelamento_sha256':sha256(p/'congelamento.json')}
    salvar_json(REG/'execucao.json',pt);salvar_json(REG/'estado.json',{'situacao':'preparado_qualificado','execucao':pt,'preservados':len(guard),'ajustes_principais':64,'controles_reais':2,'total_reais':66})
    return pt


def conferir_execucao():
    pt=ler_json(REG/'execucao.json');p=RAIZ/pt['pasta'];v=Verificador()
    v.arquivos_em(p,{'congelamento.json':pt['congelamento_sha256']});f=ler_json(p/'congelamento.json');ct=f['contrato']
    assert identidade(ct)[:20]==pt['id']==f['id'] and ct['configuracao']==configuracao() and ct['ambiente']==ambiente()
    v.arquivos_em(RAIZ,ct['fontes']);v.arquivos_em(p/'fontes',ct['fontes']);v.arquivos_em(p,{'protocolo.md':ct['protocolo_sha256']})
    q=RAIZ/ct['qualificacao']['arquivo'];v.arquivos_em(RAIZ,{ct['qualificacao']['arquivo']:ct['qualificacao']['sha256']});validar_qualificacao(q,v)
    guard=ler_json(REG/'preservacao_antes.json')['arquivos'];assert identidade(guard)==ct['preservacao_antes_sha256'];v.arquivos_em(RAIZ,guard)
    mapa=ct['entradas'];assert mapa==ler_json(REG/'entradas.json');consumos=carregar_blocos(mapa,v)
    for b,x in consumos.items():assert x.especificacao.identidade==ct['identidades_consumo'][b]
    cb=ct['carteira'];v.arquivos_em(RAIZ/cb['pasta'],{'congelamento.json':cb['congelamento_sha256']})
    return p,f,consumos


def validar_autorizacao(q,codigo):
    a=ler_json(q)
    if (a.get('execucao')!=codigo or a.get('seeds')!=SEEDS or a.get('ajustes_reais_total')!=66
        or a.get('ajustes_principais')!=64 or a.get('controles_reais')!=2 or a.get('abordagem')!='huber_blocos'
        or not a.get('mensagem_usuario')):raise ValueError('Autorização não corresponde à rodada delimitada.')
    return a


def progresso(prontas,status,atual=None):
    return {'status':status,'utc':agora(),'concluidos':prontas,'principais_concluidos':sum(not x['controle'] for x in prontas),
        'controles_concluidos':sum(x['controle'] for x in prontas),'total_principais':64,'total_reais':66,'atual':atual}


def executar(autorizacao,retomar=False):
    p,f,consumos=conferir_execucao();c=f['contrato']['configuracao'];a=validar_autorizacao(autorizacao,f['id'])
    with exclusividade(p,retomar):
        st=ler_json(p/'progresso.json')['status']
        if st=='concluido':raise ValueError('Não repetir executor encerrado.')
        if st!='preparado' and not retomar:raise ValueError('Retomada exige investigação.')
        if (p/'autorizacao.json').exists():assert ler_json(p/'autorizacao.json')==a
        else:salvar_json(p/'autorizacao.json',a)
        prontas=[];caminhos={};controles={}
        try:
            for item in f['contrato']['grade']:
                raiz=raiz_celula(p,item);ants=sorted(raiz.glob('tentativa_*'));fechadas=[t for t in ants if (t/'conclusao.json').exists()]
                if len(fechadas)>1:raise ValueError('Mais de uma conclusão para a mesma célula.')
                b,perda,s=item['bloco'],item['perda'],item['seed'];cfg=f['contrato']['receitas'][b][perda];x=consumos[b]
                if fechadas:t=fechadas[0];conferir(t)
                else:
                    t=raiz/f'tentativa_{len(ants)+1:03d}';t.mkdir(parents=True)
                    vinc={'execucao':f['id'],'bloco':b,'variante':perda,'controle':item['controle'],'seed':s,
                        'familia':'mamba','identidade_consumo':x.especificacao.identidade,'configuracao':cfg}
                    salvar_json(t/'inicio.json',{'utc':agora(),'vinculo':vinc,'anteriores_preservadas':[q.name for q in ants]})
                    salvar_json(p/'progresso.json',progresso(prontas,'executando',item))
                    try:
                        with (t/'treinamento.log').open('w',encoding='utf-8',buffering=1) as log:
                            with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                                fn=ajustar_huber if perda=='huber' else ajustar_mse
                                rede,aj=fn(x,'mamba',s,dict(cfg['treino'],perda=cfg['perda']),RAIZ/cfg['configuracao_modelos'],t,vinc)
                                assert aj['parametros']==20257
                                avaliar(x,x._conjunto.partes,'mamba',cfg,t,vinc,rede,aj);del rede
                        selar(t)
                    except BaseException:
                        salvar_json(t/'falha.json',{'utc':agora(),'erro':traceback.format_exc()});raise
                if item['controle']:
                    controles[perda]=reproducao(caminhos[chave(item)],t,cfg['reproducao'])
                    salvar_json(p/'controles_reproducao.json',controles)
                else:caminhos[chave(item)]=t
                prontas.append(item);salvar_json(p/'progresso.json',progresso(prontas,'executando',item))
            assert len(prontas)==66 and set(controles)=={'mse','huber'}
            # Nova conferência fresca ao fim; não reutiliza o cache da fase anterior.
            conferir_execucao()
            salvar_json(p/'progresso.json',progresso(prontas,'concluido'))
        except BaseException:
            salvar_json(p/'progresso.json',dict(progresso(prontas,'interrompido'),erro=traceback.format_exc()));raise
