"""Revisão posterior, sem treinar ou sobrescrever evidências do ciclo concluído."""
from collections import Counter
from pathlib import Path
import subprocess
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from previsao24.arquivos import RAIZ, agora, identidade, ler_json, salvar_json, sha256, verificar_arquivos
from previsao24.configuracao import FOLDS, celulas
from previsao24.dados import verificar_dataset


def conferir(a, b):
    np.testing.assert_allclose(a, b, rtol=1e-10, atol=1e-13, equal_nan=True)


def main():
    inicio = agora()
    destino = RAIZ/'registros/revisoes'/('revisao_'+inicio.replace(':','').replace('+','_'))
    destino.mkdir(parents=True, exist_ok=False)
    salvar_json(destino/'estado.json', {'status':'em_andamento','inicio_utc':inicio,'tipo':'revisao_pos_avaliacao_sem_treino'})
    try:
        ponteiro = ler_json(RAIZ/'registros/execucao_atual.json')
        pasta = RAIZ/ponteiro['caminho']
        execucao = ler_json(pasta/'execucao.json')
        assinatura = execucao['assinatura']
        c = assinatura['configuracao']
        assert identidade(assinatura)[:20] == ponteiro['id']
        assert ler_json(RAIZ/'configuracoes/retorno24_001.json') == c
        verificar_arquivos(RAIZ, assinatura['fontes'])
        verificar_arquivos(pasta/'fontes', assinatura['fontes'])
        assert ler_json(RAIZ/'registros/qualificacao/testes_atual.json') == assinatura['testes']
        q = assinatura['qualificacao']
        assert sha256(RAIZ/q['caminho']) == q['sha256']
        congelamento = ler_json(pasta/'congelamento.json')
        assert congelamento['assinatura'] == identidade(assinatura)
        dados = RAIZ/execucao['dataset_caminho']
        manifesto = verificar_dataset(dados)
        assert manifesto['id'] == assinatura['dataset']
        horas, blocos = {}, {}
        causais, observaveis = [], []
        for par in c['pares']:
            h = pd.read_parquet(dados/par/'horas.parquet')
            minutos = np.load(dados/par/'minutos.npy', mmap_mode='r').reshape(-1,60,6)
            completo = np.isfinite(minutos).all(axis=(1,2))
            closes = np.where(completo, minutos[:,-1,3], np.nan)
            retorno = np.r_[np.nan, np.log(closes[1:]/closes[:-1])]
            alvo = np.r_[np.log(closes[24:]/closes[:-24]), np.full(24,np.nan)]
            causal = pd.Series(np.isfinite(retorno)).rolling(336,min_periods=336).sum().eq(336).to_numpy()
            observavel = causal & np.isfinite(alvo)
            conferir(h['close'],closes); conferir(h['retorno'],retorno); conferir(h['alvo'],alvo)
            np.testing.assert_array_equal(h['causal'],causal)
            np.testing.assert_array_equal(h['observavel'],observavel)
            esperado = manifesto['primeiro_minuto']*60+(np.arange(len(h))+1)*3600
            np.testing.assert_array_equal(h['origem_utc'].dt.as_unit('s').astype('int64'),esperado)
            assert (h['destino_utc']-h['origem_utc']).eq(pd.Timedelta(hours=24)).all()
            horas[par] = h
            causais.append(causal); observaveis.append(observavel)
            del minutos
        comum = np.logical_and.reduce(observaveis)
        np.testing.assert_array_equal(np.load(dados/'observavel_comum.npy'),comum)
        np.testing.assert_array_equal(np.load(dados/'causal_comum.npy'),np.logical_and.reduce(causais))
        for par,h in horas.items():
            for fold in c['folds_desenvolvimento']+c['folds_avaliacao']:
                cortes = [pd.Timestamp(v,tz='UTC') for v in ('2021-01-01',*FOLDS[fold])]
                for nome,a,b in zip(('treino','validacao','teste'),cortes[:-1],cortes[1:]):
                    blocos[par,fold,nome] = h.loc[comum & h['origem_utc'].ge(a) & h['origem_utc'].lt(b) & h['destino_utc'].lt(b)]
                blocos[par,fold,'operacional'] = h.loc[h['causal'] & h['origem_utc'].ge(cortes[2]) & h['origem_utc'].lt(cortes[3])]
        print('Dataset reconstruído desde minutos: fechamentos, retornos, alvo, máscaras e fronteiras conferidos.',flush=True)
        previstas = celulas(c,'desenvolvimento')+celulas(c,'avaliacao')
        previstas += [{'par':p,'fold':f,'modelo':m} for f in c['folds_desenvolvimento']+c['folds_avaliacao'] for p in c['pares'] for m in ('naive','arima')]
        esperado = {identidade(x)[:20]:x for x in previstas}
        encontradas, linhas, erros, tempos, locais = {}, [], {}, {}, {}
        candidatos = Counter()
        for p in sorted(pasta.glob('celulas/*/tentativa_*/tentativa.json')):
            t = ler_json(p); x = t['celula']; chave = identidade(x)[:20]
            assert t['status']=='auditada' and chave not in encontradas and esperado[chave]==x
            a = ler_json(p.parent/'auditoria.json')
            assert a['status']=='aprovado' and a['celula']==x
            verificar_arquivos(p.parent,a['arquivos'])
            r = ler_json(p.parent/'resultado.json')
            encontradas[chave]=x; locais[chave]=p.parent
            for nome in ('validacao','teste','operacional'):
                salvo = pd.read_parquet(p.parent/f'previsoes_{nome}.parquet')
                b = blocos[x['par'],x['fold'],nome]
                pd.testing.assert_frame_equal(salvo[b.columns.intersection(salvo.columns)].reset_index(drop=True),b[b.columns.intersection(salvo.columns)].reset_index(drop=True))
                previsto = salvo['previsao'].to_numpy()
                assert np.isfinite(previsto).all()
                if nome=='operacional': continue
                real = salvo['alvo'].to_numpy(); erro = previsto-real
                recalls = [np.mean(np.sign(previsto[real*k>0])==k) for k in (-1,1)]
                medidas = {'mse':np.mean(erro**2),'rmse':np.sqrt(np.mean(erro**2)),'mae':np.mean(np.abs(erro)),
                           'mse_naive':np.mean(real**2),'vies':np.mean(erro),'acuracia_direcional':np.mean(np.sign(previsto)==np.sign(real)),
                           'acerto_balanceado_direcional':np.mean(recalls)}
                medidas['habilidade_mse']=1-medidas['mse']/medidas['mse_naive']
                for k,v in medidas.items(): conferir(v,r['metricas'][nome][k])
                if nome=='teste':
                    fase = 'desenvolvimento' if x['fold'].startswith('DB') else 'avaliacao'
                    linha = {**x,'fase':fase,**{k:float(v) for k,v in medidas.items()},'n':len(real),
                             'energia_previsao':float(np.mean(previsto**2)),'alinhamento_duplo':float(2*np.mean(previsto*real)),
                             'desvio_previsao':float(np.std(previsto)),'desvio_real':float(np.std(real)),
                             'amplitude_media_absoluta_previsao':float(np.mean(np.abs(previsto))),
                             'amplitude_media_absoluta_real':float(np.mean(np.abs(real))),
                             'so_alta':bool((previsto>0).all()),'so_queda':bool((previsto<0).all()),
                             'parametros':r.get('parametros')}
                    conferir(linha['mse']-linha['mse_naive'],linha['energia_previsao']-linha['alinhamento_duplo'])
                    erros[x['par'],x['fold'],x.get('contexto'),x.get('seed'),x['modelo']] = erro**2
                    if x['fold'] in tempos: np.testing.assert_array_equal(tempos[x['fold']],salvo['origem_utc'])
                    tempos[x['fold']] = salvo['origem_utc']
            if x['modelo'] in ('lstm','mamba'):
                epocas = ler_json(p.parent/'epocas.json')
                melhor = min(epocas,key=lambda e:e['mse_validacao'])
                assert melhor['epoca']==r['epoca_selecionada'] and r['recarga_exata']
                conferir(melhor['mse_validacao'],r['metricas']['validacao']['mse'])
                linha.update(epoca=r['epoca_selecionada'],epocas_executadas=r['epocas_executadas'],
                             treino_padronizado_primeira=epocas[0]['mse_treino_padronizado'],
                             treino_padronizado_ultima=epocas[-1]['mse_treino_padronizado'])
            elif x['modelo']=='arima':
                itens = ler_json(p.parent/'candidatos.json')['candidatos']
                candidatos.update(v['status'] for v in itens)
                melhor = min((v for v in itens if v['status']=='valido'),key=lambda v:(v['validacao']['mse'],sum(v['ordem'][::2]),v['ordem'][0],v['ordem'][2]))
                assert melhor['ordem']==r['ordem']
                conferir(melhor['validacao']['mse'],r['metricas']['validacao']['mse'])
            linhas.append(linha)
            if len(linhas)%100==0: print(f'{len(linhas)} resultados íntegros, alinhados e recalculados.',flush=True)
        assert encontradas==esperado
        quadro = pd.DataFrame(linhas)
        agregados, verificacoes_bootstrap = [], []
        for fase in ('desenvolvimento','avaliacao'):
            base = RAIZ/'registros/analises'/ponteiro['id']/fase
            publicacao = ler_json(base/'publicacao.json'); auditoria = ler_json(base/'auditoria_publicacao.json')
            assert auditoria['publicacao_sha256']==sha256(base/'publicacao.json')
            verificar_arquivos(base,publicacao['arquivos'])
            resumo = ler_json(base/'resumo.json')
            for m in resumo['modelos']:
                itens = quadro[(quadro.fase==fase)&(quadro.modelo==m['modelo'])]
                for k in ('mse','mae','habilidade_mse','acuracia_direcional','acerto_balanceado_direcional'): conferir(itens[k].mean(),m[k])
                adicionais = {k:float(itens[k].mean()) for k in ('energia_previsao','alinhamento_duplo','desvio_previsao','desvio_real','amplitude_media_absoluta_previsao','amplitude_media_absoluta_real')}
                adicionais.update(so_alta=int(itens.so_alta.sum()),so_queda=int(itens.so_queda.sum()),ajustes=len(itens))
                if m['modelo'] in ('lstm','mamba'):
                    adicionais.update(epoca_mediana=float(itens.epoca.median()),epoca_1=int((itens.epoca==1).sum()),
                                      epoca_ate_3=int((itens.epoca<=3).sum()),epocas_executadas_mediana=float(itens.epocas_executadas.median()),
                                      parametros=int(itens.parametros.iloc[0]))
                agregados.append({'fase':fase,**m,**adicionais,'mse_relativo_naive':float(itens.mse.mean()/itens.mse_naive.mean())})
            folds = c['folds_desenvolvimento'] if fase=='desenvolvimento' else c['folds_avaliacao']
            comparacoes = [(r['contraste'],r) for r in resumo['contrastes']]
            comparacoes += [(f"{r['modelo']}_W24_W{r['contexto_comparado']}",r) for r in resumo['contextos']]
            def escore(par,fold,w,m):
                return np.mean([erros[par,fold,w,s,m] for s in c['seeds']],axis=0) if m in ('lstm','mamba') else erros[par,fold,None,None,m]
            for nome,publicado in comparacoes:
                diarios=[]; pontuais=[]
                for fold in folds:
                    if '_menos_' in nome:
                        a,b=nome.split('_menos_'); dif=np.mean([escore(p,fold,w,a)-escore(p,fold,w,b) for p in c['pares'] for w in c['contextos']],axis=0)
                    else:
                        m=publicado['modelo']; w=publicado['contexto_comparado']; dif=np.mean([escore(p,fold,24,m)-escore(p,fold,w,m) for p in c['pares']],axis=0)
                    pontuais.append(float(dif.mean()))
                    diario=pd.DataFrame({'dia':tempos[fold].dt.floor('D'),'valor':dif}).groupby('dia').valor.agg(['sum','count'])
                    calendario=pd.date_range(FOLDS[fold][0],FOLDS[fold][2],freq='D',inclusive='left',tz='UTC')
                    calendario=calendario[calendario>=pd.Timestamp(FOLDS[fold][1],tz='UTC')]
                    diarios.append(diario.reindex(calendario,fill_value=0).to_numpy())
                conferir(np.mean(pontuais),publicado.get('diferenca',publicado.get('mse_curto_menos_longo')))
                for intervalo in publicado['intervalos']:
                    rng=np.random.default_rng(c['bootstrap']['seed']); amostras=np.zeros(c['bootstrap']['replicas'])
                    for diario in diarios:
                        n=len(diario); d=min(n,intervalo['dias']); inicios=rng.integers(n-d+1,size=(len(amostras),int(np.ceil(n/d))))
                        indices=(inicios[...,None]+np.arange(d)).reshape(len(amostras),-1)[:,:n]
                        sorteados=diario[indices].sum(axis=1); amostras+=sorteados[:,0]/sorteados[:,1]/len(folds)
                    limites=np.quantile(amostras,[.025,.975]); conferir(limites,[intervalo['inferior'],intervalo['superior']])
                    verificacoes_bootstrap.append({'fase':fase,'contraste':nome,'dias':intervalo['dias'],'conferido':True})
            print(f'{fase}: médias e 30 intervalos temporais reproduzidos.',flush=True)
        testes=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=RAIZ,capture_output=True,text=True)
        (destino/'testes_contratos.log').write_text(testes.stdout+testes.stderr)
        assert testes.returncode==0
        quadro.to_csv(destino/'diagnosticos_por_ajuste.csv',index=False)
        grupos={}
        for fator in ('par','fold','contexto'):
            grupos[fator]=[]
            for chaves,q in quadro.groupby(['fase','modelo',fator],dropna=False):
                grupos[fator].append({'fase':chaves[0],'modelo':chaves[1],fator:None if pd.isna(chaves[2]) else chaves[2],
                                      'mse':float(q.mse.mean()),'mse_naive':float(q.mse_naive.mean()),'habilidade_media':float(q.habilidade_mse.mean())})
        salvar_json(destino/'resumo.json',{'status':'aprovado','inicio_utc':inicio,'fim_utc':agora(),'execucao':ponteiro['id'],
                   'tipo':'diagnostico_exploratorio_pos_avaliacao_sem_treino','ajustes_recalculados':len(linhas),'candidatos':dict(candidatos),
                   'intervalos_reproduzidos':len(verificacoes_bootstrap),'contratos_codigo_saida':testes.returncode,
                   'modelos':agregados,'grupos':grupos,'bootstrap':verificacoes_bootstrap,
                   'fontes_cientificas':assinatura['fontes'],'revisor_sha256':sha256(Path(__file__)),
                   'limites':'Recalcula previsões já salvas; não executa novo treino nem demonstra causalmente por que uma arquitetura perdeu. Os hashes dos checkpoints e evidências de recarga são conferidos, sem repetir todas as inferências.'})
        salvar_json(destino/'estado.json',{'status':'aprovado','fim_utc':agora(),'execucao':ponteiro['id']})
        print(f'REVISAO_APROVADA {destino}',flush=True)
        print(pd.DataFrame(agregados).to_string(index=False),flush=True)
    except Exception as erro:
        salvar_json(destino/'estado.json',{'status':'falha','fim_utc':agora(),'erro':repr(erro)})
        raise


if __name__=='__main__':
    main()
