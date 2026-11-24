"""Continuação técnica: metadados de modelo não são métricas de uma carteira herdada."""
import argparse
from copy import deepcopy
import shutil
import sqlite3
import zipfile
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,sha256,identidade,agora
from .executar import PONTEIRO


def preparar():
    ptr=ler_json(PONTEIRO);pai=RAIZ/ptr['pasta'];f=ler_json(pai/'congelamento.json')
    if (pai/'execucao.lock').exists() or ler_json(pai/'progresso.json')['situacao']!='falha':raise ValueError('Pai não encerrado em falha')
    db=sqlite3.connect(pai/'carteiras.sqlite');assert db.execute('PRAGMA integrity_check').fetchone()==('ok',)
    n=db.execute('SELECT COUNT(*) FROM carteiras').fetchone()[0];unicos=db.execute('SELECT COUNT(*) FROM cache').fetchone()[0];db.close()
    with zipfile.ZipFile(pai/'ledgers.zip') as z:assert z.testzip() is None
    nomes=['carteiras.sqlite','ledgers.zip','barreiras_ledgers.zip','barreiras_recalculo.json','editoriais_antes.zip','editoriais_antes.json']
    assinatura={k:deepcopy(v) for k,v in f.items() if k not in ('id','utc')}
    assinatura['fontes'][__file__.replace('\\','/').split(RAIZ.as_posix()+'/')[-1]]=sha256(__file__)
    assinatura['continuacao_tecnica']={'pai':ptr,'motivo':'Cache pode compartilhar o mesmo sinal entre modelos com metadados distintos; contexto e seed são copiados da fonte e não comparados como métricas. Todos os campos financeiros continuam exigidos.',
        'carteiras_herdadas':n,'unicas_herdadas':unicos,'artefatos':{k:sha256(pai/k) for k in nomes}}
    codigo=identidade(assinatura)[:20];p=RAIZ/'dados/reavaliacoes'/f'custos_{codigo}';p.mkdir(parents=True,exist_ok=False)
    for nome in nomes:shutil.copyfile(pai/nome,p/nome)
    salvar_json(p/'congelamento.json',{'id':codigo,'utc':agora(),**assinatura})
    salvar_json(p/'progresso.json',{'situacao':'preparado','concluidos':n,'previstos':len(f['inventario']['jobs']),'utc':agora()})
    salvar_json(PONTEIRO,{'id':codigo,'pasta':p.relative_to(RAIZ).as_posix(),'congelamento_sha256':sha256(p/'congelamento.json')})
    print(p,flush=True)


def executar():
    from .acelerar import instalar
    instalar()
    from . import adaptadores
    original=adaptadores.conferir_reproducao
    def conferir(a,b):
        campos={'seed','contexto'}
        return original({k:v for k,v in a.items() if k not in campos},{k:v for k,v in b.items() if k not in campos})
    adaptadores.conferir_reproducao=conferir
    from .executar import executar as prosseguir
    prosseguir()


if __name__=='__main__':
    cli=argparse.ArgumentParser();cli.add_argument('acao',choices=['preparar','executar']);args=cli.parse_args()
    preparar() if args.acao=='preparar' else executar()
