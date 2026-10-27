"""Confere escalas e uma amostra declarada de inferência; não modifica o ciclo."""
from pathlib import Path
import inspect
import sys
import numpy as np
import pandas as pd
import torch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from previsao24.arquivos import RAIZ, agora, ler_json, salvar_json, sha256
from previsao24.configuracao import FOLDS
from previsao24.redes import criar
from previsao24.treino import fixar_seed


def main():
    inicio=agora()
    destino=RAIZ/'registros/revisoes'/('checkpoints_'+inicio.replace(':','').replace('+','_'))
    destino.mkdir(parents=True,exist_ok=False)
    salvar_json(destino/'estado.json',{'status':'em_andamento','inicio_utc':inicio})
    try:
        ponteiro=ler_json(RAIZ/'registros/execucao_atual.json')
        pasta=RAIZ/ponteiro['caminho']
        execucao=ler_json(pasta/'execucao.json')
        c=execucao['assinatura']['configuracao']
        dados=RAIZ/execucao['dataset_caminho']
        comum=np.load(dados/'observavel_comum.npy')
        escalas={}; matrizes={}
        for par in c['pares']:
            horas=pd.read_parquet(dados/par/'horas.parquet')
            for fold in c['folds_desenvolvimento']+c['folds_avaliacao']:
                fim=pd.Timestamp(FOLDS[fold][0],tz='UTC')
                treino=horas.loc[comum & horas['origem_utc'].lt(fim) & horas['destino_utc'].lt(fim)]
                ids=np.unique((treino['indice_hora'].to_numpy()[:,None]+np.arange(-335,1)).ravel())
                retornos=horas['retorno'].to_numpy(); amostra=retornos[ids]; alvo=treino['alvo'].to_numpy()
                e={'media':float(amostra.mean()),'escala':float(amostra.std()) or 1.,
                   'media_alvo':float(alvo.mean()),'escala_alvo':float(alvo.std()) or 1.,
                   'retornos_unicos':len(ids),'inicio_entradas':horas.iloc[ids[0]].origem_utc.isoformat(),
                   'fim_entradas':horas.iloc[ids[-1]].origem_utc.isoformat(),
                   'ultimo_alvo_treino':treino.destino_utc.max().isoformat()}
                escalas[par,fold]=e
                matrizes[par,fold]=((retornos-e['media'])/e['escala']).astype(np.float32)
        fixar_seed(17)
        assert torch.cuda.is_available()
        verificadas=0; recargas=[]
        estratos=set(zip(c['pares'],c['folds_avaliacao']))
        for caminho in sorted(pasta.glob('celulas/*/tentativa_*/checkpoint.pt')):
            cp=torch.load(caminho,map_location='cpu',weights_only=True)
            x=cp['celula']; e=escalas[x['par'],x['fold']]
            assert cp['configuracao']==c
            assert cp['escalas'].keys()==e.keys()
            for k,v in e.items():
                if isinstance(v,float): np.testing.assert_allclose(cp['escalas'][k],v,rtol=1e-12,atol=1e-14)
                else: assert cp['escalas'][k]==v,(x,k)
            verificadas+=1
            if (x['par'],x['fold']) not in estratos or x['seed']!=17: continue
            q=pd.read_parquet(caminho.parent/'previsoes_teste.parquet')
            rede=criar(x['modelo'],c).cuda().eval(); rede.load_state_dict(cp['pesos'])
            matriz=matrizes[x['par'],x['fold']]
            erros=[]; n=0
            for a in (0,((len(q)-1)//64)*64):
                amostra=q.iloc[a:a+64]
                ids=amostra['indice_hora'].to_numpy()[:,None]+np.arange(1-x['contexto'],1)
                entradas=torch.tensor(matriz[ids,None],device='cuda')
                with torch.inference_mode():
                    p=rede(entradas).cpu().numpy().astype(np.float64)*e['escala_alvo']+e['media_alvo']
                esperado=amostra['previsao'].to_numpy()
                np.testing.assert_array_equal(p,esperado)
                erros.append(float(np.max(np.abs(p-esperado)))); n+=len(p)
            recargas.append({**x,'n_previsoes':n,'diferenca_maxima':max(erros),'exata':True})
            del rede
        assert verificadas==768 and len(recargas)==32
        rede=criar('mamba',c)
        otimizador=torch.optim.AdamW(rede.parameters(),lr=c['treino']['taxa_aprendizado'],weight_decay=c['treino']['weight_decay'])
        marcados=[]
        for nome,p in rede.named_parameters():
            if getattr(p,'_no_weight_decay',False):
                grupo=next(g for g in otimizador.param_groups if any(p is t for t in g['params']))
                marcados.append({'nome':nome,'elementos':p.numel(),'weight_decay_efetivo':grupo['weight_decay']})
        import mamba_ssm.modules.mamba_simple as modulo
        fonte=Path(inspect.getfile(modulo))
        resumo={'status':'aprovado_com_ressalva_de_configuracao','execucao':ponteiro['id'],
                'inicio_utc':inicio,'fim_utc':agora(),'escalas_checkpoint_conferidas':verificadas,
                'regra_amostra_inferencia':'BTC/B1, ETH/B2, BNB/B3, XRP/B4; modelos Mamba e LSTM; todos os contextos; seed17; primeiro e último batch de teste nas fronteiras originais de batch64.',
                'recargas':recargas,'mamba_parametros_marcados_sem_decay':marcados,
                'biblioteca_mamba_caminho':str(fonte),'biblioteca_mamba_sha256':sha256(fonte),
                'treino_cientifico_sha256':sha256(RAIZ/'previsao24/treino.py'),
                'revisor_sha256':sha256(Path(__file__)),
                'ressalva':'O otimizador genérico aplica weight_decay=0.001 inclusive a A_log e D, marcados _no_weight_decay pela biblioteca. É a configuração efetivamente executada e congelada, mas diverge da intenção desses marcadores. O impacto no resultado não foi isolado; requer novo ciclo para comparação controlada. Nenhum peso foi atualizado nesta revisão.'}
        salvar_json(destino/'resumo.json',resumo)
        salvar_json(destino/'estado.json',{'status':resumo['status'],'fim_utc':agora()})
        print(f'CHECKPOINTS_CONFERIDOS {destino}: {verificadas} escalas, {len(recargas)} recargas amostrais exatas, {sum(r["n_previsoes"] for r in recargas)} previsões.',flush=True)
    except Exception as erro:
        salvar_json(destino/'estado.json',{'status':'falha','fim_utc':agora(),'erro':repr(erro)})
        raise


if __name__=='__main__': main()
