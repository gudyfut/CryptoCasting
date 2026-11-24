"""Referências sempre comprado/vendido no mesmo futuro de 2026; sem GPU."""
import io
import json
import os
from pathlib import Path
import shutil
import traceback
import zipfile
import numpy as np
from infraestrutura.artefatos import RAIZ, agora, conferir_arquivos, identidade, ler_json, salvar_json, sha256
from experimentos.generalizacao_moedas.avaliacao import carregar_mercado
from simulacao_operacoes.continuidade_diaria.simulador import simular
from simulacao_operacoes.continuidade_diaria.auditoria_grade import conferir


def executar():
    reg=RAIZ/'registros/lstm_diaria';ponteiro=reg/'referencias_constantes_2026.json'
    assert not ponteiro.exists(),'Já existe execução; conferir seu estado.'
    ptr=ler_json(RAIZ/'registros/ablacao_linear_2026/execucao.json');orig=RAIZ/ptr['pasta']
    assert sha256(orig/'congelamento.json')==ptr['congelamento_sha256']
    assert ler_json(RAIZ/'registros/ablacao_linear_2026/conferencia_posterior.json')['situacao']=='aprovada'
    f=ler_json(orig/'congelamento.json');periodo=RAIZ/f['referencia_periodo']['pasta'];mercados=ler_json(periodo/'mercados.json')
    pai=RAIZ/f['referencia_modelos']['pasta'];antigo=ler_json(orig/'operacoes.json')['carteiras']
    deps={}
    def guardar(p):deps[Path(p).relative_to(RAIZ).as_posix()]=sha256(p)
    for q in (orig/'congelamento.json',orig/'operacoes.json',orig/'carteiras.zip',periodo/'mercados.json'):
        guardar(q)
    for m in ('BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT'):
        for q in (orig/m/'entradas.npz',orig/m/'A_ensemble.npz',pai/m/'configuracao.json'):guardar(q)
        mercado=RAIZ/mercados[m]['pasta'];assert sha256(mercado/'manifesto.json')==mercados[m]['manifesto_sha256']
        lista=ler_json(mercado/'manifesto.json')['arquivos'];conferir_arquivos(mercado,lista)
        guardar(mercado/'manifesto.json')
        for nome in lista:guardar(mercado/nome)
    fontes={}
    for pasta in ('codigo/simulacao_operacoes','codigo/analises/etapas/lstm_diaria'):
        for q in (RAIZ/pasta).rglob('*.py'):fontes[q.relative_to(RAIZ).as_posix()]=sha256(q)
    spec=dict(utc=agora(),natureza='Referências operacionais constantes, sem treino, retrospectiva',
              referencia=ptr,moedas=['BTCUSDT','ETHUSDT','BNBUSDT','XRPUSDT'],custos=[.0001,.0002,.0003],
              lados={'sempre_comprado':1,'sempre_vendido':-1},modo='liquida',capital=10000.,nocional=.95,
              controles='A-ensemble de 2026 com custo base, uma reprodução por ativo',dependencias=deps,fontes=fontes,
              limite='Lados constantes e LSTM diferem em exposição; comparação retrospectiva, sem garantia de fills ou lucro.')
    ident=identidade(spec)[:20];p=RAIZ/'dados/reavaliacoes'/f'referencias_constantes_2026_{ident}';p.mkdir(parents=True,exist_ok=False)
    for nome in fontes:
        dest=p/'fontes'/nome;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(RAIZ/nome,dest)
    salvar_json(p/'congelamento.json',spec)
    ptr_novo=dict(id=ident,pasta=p.relative_to(RAIZ).as_posix(),congelamento_sha256=sha256(p/'congelamento.json'))
    salvar_json(ponteiro,dict(execucao=ptr_novo,situacao='executando',pid=os.getpid(),utc=agora()))
    carteiras=[];auditorias=[];controles=[];falhas=[]
    try:
        with zipfile.ZipFile(p/'carteiras.zip','x',compression=zipfile.ZIP_DEFLATED) as out,zipfile.ZipFile(orig/'carteiras.zip') as anterior:
            for moeda in spec['moedas']:
                cfg=ler_json(pai/moeda/'configuracao.json');m=carregar_mercado(mercados[moeda])
                with np.load(orig/moeda/'entradas.npz',allow_pickle=False) as z:
                    t=z['origens_ms'].copy();ultimo=z['ultimo_close'].copy()
                with np.load(orig/moeda/'A_ensemble.npz',allow_pickle=False) as q:
                    np.testing.assert_array_equal(t,q['origens_ms']);prev_A=q['previsoes'].copy()
                for custo,slip in enumerate(spec['custos'],1):
                    from copy import deepcopy
                    regras=deepcopy(cfg['operacoes']);regras['slippage_por_lado']=slip
                    trabalhos=list(spec['lados'].items())
                    if custo==1:trabalhos += [('controle_A',None)]
                    for nome,lado in trabalhos:
                        prev=prev_A if nome=='controle_A' else ultimo
                        ident_c=f'{moeda}/{nome}/custo_{custo}'
                        try:
                            r,cv=simular(t,prev,ultimo,m,regras,'liquida',lado)
                            audit=conferir(r,cv,m,regras,'liquida',t,prev,ultimo,lado)
                        except ValueError as erro:
                            if 'Violação prudencial' not in str(erro):raise
                            falhas.append(dict(identidade=ident_c,erro=str(erro)))
                            out.writestr(ident_c+'/falha.json',json.dumps(falhas[-1],ensure_ascii=False));continue
                        if nome=='controle_A':
                            velho=next(x for x in antigo if x['moeda']==moeda and x['unidade']=='A_ensemble' and x['custo']==1)
                            for k,v in velho['metricas'].items():
                                if v is None:assert r['metricas'][k] is None
                                else:np.testing.assert_allclose(r['metricas'][k],v,atol=1e-7,rtol=1e-10)
                            with np.load(io.BytesIO(anterior.read(velho['membro']+'/curva.npz'))) as q:
                                np.testing.assert_allclose(cv['saldos_diarios'],q['saldos_diarios'],atol=1e-7,rtol=1e-10)
                            controles.append(moeda)
                        else:carteiras.append(dict(moeda=moeda,unidade=nome,custo=custo,membro=ident_c,metricas=r['metricas']))
                        out.writestr(ident_c+'/resultado.json',json.dumps(dict(regras=regras,**r),ensure_ascii=False,allow_nan=False))
                        buf=io.BytesIO();np.savez_compressed(buf,origens_ms=t,**cv);out.writestr(ident_c+'/curva.npz',buf.getvalue())
                        auditorias.append(dict(identidade=ident_c,**audit))
                del m
        assert len(carteiras)+len(falhas)==24 and len(controles)==4
        with zipfile.ZipFile(p/'carteiras.zip') as z:assert z.testzip() is None
        conferir_arquivos(RAIZ,deps);conferir_arquivos(RAIZ,fontes);conferir_arquivos(p/'fontes',fontes)
        salvar_json(p/'resultados.json',dict(carteiras=carteiras,controles=controles,falhas=falhas,auditorias=auditorias))
        arquivos={q.relative_to(p).as_posix():sha256(q) for q in p.rglob('*') if q.is_file() and 'fontes' not in q.relative_to(p).parts and q.name!='fechamento.json'}
        salvar_json(p/'fechamento.json',dict(utc=agora(),situacao='concluido_conferido',execucao=ptr_novo,carteiras=len(carteiras),
                    controles=len(controles),falhas=falhas,arquivos=arquivos))
        salvar_json(ponteiro,dict(execucao=ptr_novo,situacao='concluido_conferido',utc=agora(),fechamento_sha256=sha256(p/'fechamento.json')))
        print('REFERENCIAS_CONCLUIDAS',len(carteiras),'CONTROLES',len(controles),flush=True)
    except BaseException:
        salvar_json(p/'incidente.json',dict(utc=agora(),erro=traceback.format_exc()))
        salvar_json(ponteiro,dict(execucao=ptr_novo,situacao='interrompido_preservado',utc=agora()))
        raise


if __name__=='__main__':executar()
