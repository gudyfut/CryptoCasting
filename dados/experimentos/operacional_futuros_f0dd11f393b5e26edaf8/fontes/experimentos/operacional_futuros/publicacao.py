"""Fechamento de leitura: nunca chama executor, consulta Astra ou reabre ajuste."""
from pathlib import Path
import numpy as np
from infraestrutura.artefatos import RAIZ,agora,ler_json,salvar_json,sha256,conferir_arquivos
from avaliacao.metricas_operacionais import resumo_pareado
from avaliacao.incerteza_operacional import comprimir_dias,bootstrap_pareado
from .ciclo import REG,preservar


def publicar():
    ptr=ler_json(REG/'execucao.json');p=RAIZ/ptr['pasta']
    if not (p/'encerramento.json').exists(): raise ValueError('Ciclo ainda não encerrou.')
    f=ler_json(p/'congelamento.json');conferir_arquivos(RAIZ,f['fontes']);preservar()
    d=p/'publicacao'
    if d.exists(): raise FileExistsError('Publicação existente; usar nova conferência, não sobrescrever.')
    d.mkdir()
    from simulacao_operacoes.operacional.mercado import carregar
    from simulacao_operacoes.operacional.auditoria import conferir
    final=(p/'avaliacoes/final').exists();m,h=carregar(final=final)
    jobs=ler_json(p/'ajustes.json');conferidos=[]
    for j in jobs:
        if j['status']!='concluido': continue
        jp=RAIZ/j['pasta'];c=ler_json(jp/'ajuste/conclusao.json')
        if sha256(jp/'ajuste'/c['checkpoint'])!=c['checkpoint_sha256']: raise ValueError('Checkpoint mudou.')
        for fase in ('validacao','calibracao','comparacao'):
            npz=jp/'ajuste'/(fase+'.npz')
            if sha256(npz)!=c[fase+'_sha256']: raise ValueError('Previsão mudou.')
            z=np.load(npz);erro=z['previsoes']-z['alvos'];mse=float(np.sum(erro*erro)/erro.size)
            if not np.isclose(mse,c['metricas'][fase]['mse'],rtol=1e-12,atol=1e-15):
                raise ValueError('MSE independente divergente.')
        conferidos.append(j['id'])
    carteiras=[]
    for raiz in ('avaliacoes','baselines'):
        for manifesto in sorted((p/raiz).rglob('manifesto.json')):
            man=ler_json(manifesto);cp=manifesto.parent;conferir_arquivos(cp,man['arquivos'])
            r=ler_json(cp/'resultado.json');z=np.load(cp/'curva.npz')
            r.update(patrimonio=z['patrimonio'],segundos_utc=z['segundos_utc'])
            a=conferir(r,m,int(z['segundos_utc'][0]*1000),int(z['segundos_utc'][-1]*1000))
            carteiras.append({'pasta':cp.relative_to(RAIZ).as_posix(),'vinculo':man['vinculo'],
                             'metricas':r['metricas'],'auditoria':a})
    tabelas=[];incertezas=[];coortes={}
    for fase in ('exploracao','reforco','final'):
        for receita in sorted((p/'avaliacoes'/fase).glob('*')):
            if not receita.is_dir(): continue
            linhas=[]
            for recibo in receita.glob('*/conclusao.json'): linhas+=ler_json(recibo)['linhas']
            seeds=f['proposta']['seeds']['exploracao' if fase=='exploracao' else 'reforco_e_final']
            blocos=[b['id'] for b in f['proposta']['calendario']['final_retrospectiva' if fase=='final' else 'desenvolvimento']]
            cobertura={(l['recorte'],l['seed'],l['cenario']) for l in linhas}
            completo=len(linhas)==len(blocos)*len(seeds)*5 and len(cobertura)==len(linhas)
            if not completo:
                tabelas.append({'fase':fase,'receita':receita.name,'completa':False,'celulas_concluidas':len(linhas)})
                continue
            coortes[fase,receita.name]=(linhas,blocos,seeds)
            for cenario in ('base','custo2x','custo3x','comprado','vendido'):
                ls=[l for l in linhas if l['cenario']==cenario]
                r=resumo_pareado(ls,blocos,seeds)
                extras={k:float(np.mean([l['metricas'][k] for l in ls])) for k in
                        ['operacoes','giro','comissoes','funding','pnl_compras','pnl_vendas']}
                tabelas.append({'fase':fase,'receita':receita.name,'cenario':cenario,'completa':True,**r,**extras})
    for (fase,nome),(linhas,blocos,seeds) in coortes.items():
        if nome=='R0' or (fase,'R0') not in coortes: continue
        ref=coortes[fase,'R0'][0];a={};b={};motivo=None
        for ls,dic in [(linhas,a),(ref,b)]:
            for l in ls:
                if l['cenario']!='base':continue
                # Resolve from execution hierarchy, independent of Windows absolute editorial path.
                cp=p/'avaliacoes'/fase/l['receita']/l['recorte']/'S'/str(l['seed'])/'base/curva.npz'
                z=np.load(cp)
                try: dic[l['recorte'],l['seed']]=comprimir_dias(z['patrimonio'],z['segundos_utc'])
                except ValueError as exc: motivo=str(exc)
        if motivo:
            incertezas.append({'fase':fase,'candidata':nome,'referencia':'R0','indisponivel':motivo});continue
        for tamanho in (14,7,28):
            r=bootstrap_pareado(a,b,blocos,seeds,bloco=tamanho)
            incertezas.append({'fase':fase,'candidata':nome,'referencia':'R0',**r})
    salvar_json(d/'auditoria_independente.json',{'utc':agora(),'ajustes':conferidos,'carteiras':len(carteiras),
        'preservacao_conferida':True,'criterio':'Recalcular MSE, conferir hashes dos checkpoints/previsões e reconstruir ledger de cada carteira.'})
    salvar_json(d/'carteiras.json',carteiras);salvar_json(d/'comparacao.json',tabelas)
    salvar_json(d/'incerteza.json',incertezas)
    salvar_json(d/'situacao.json',{'encerramento':ler_json(p/'encerramento.json'),'ajustes_iniciados':len(jobs),
        'ajustes_concluidos':len(conferidos),'carteiras_fisicas_conferidas':len(carteiras),
        'controles_fora_medias':True,'retrospectivo':True,'custos_e_liquidacao_exchange_nao_certificados':True})
    arquivos={x.name:sha256(x) for x in d.iterdir() if x.is_file()}
    salvar_json(d/'manifesto.json',{'utc':agora(),'execucao':ptr,'arquivos':arquivos})
    e=ler_json(REG/'estado.json');e.update(publicacao=d.relative_to(RAIZ).as_posix(),
        publicacao_sha256=sha256(d/'manifesto.json'),auditoria_posterior_concluida=True)
    salvar_json(REG/'estado.json',e)
    return e
