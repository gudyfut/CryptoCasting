"""Leitura da tentativa interrompida e repetição de gradientes artificiais, sem otimizador."""
import os
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
import json
import argparse
import numpy as np
from infraestrutura.artefatos import RAIZ,ler_json,salvar_json,sha256,agora


def executar(gpu=False):
    ptr=ler_json(RAIZ/'registros/cryptomamba_diario/execucao.json');p=RAIZ/ptr['pasta']
    assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    assert not ler_json(p/'processo.json')['ativo']
    f=ler_json(p/'congelamento.json');resultados={};historicos={};previsoes={}
    for nome in ('seed_42','controle_42'):
        d=p/'ajustes'/nome;c=ler_json(d/'conclusao.json');sel=c['checkpoint']
        assert sha256(d/sel['checkpoint'])==sel['sha256']
        z=np.load(d/'validacao.npz');y=z['y'];v=z['previsoes'];base=z['ultimo_close']
        m={'rmse':float(np.sqrt(np.mean((y-v)**2))),'mae':float(np.mean(abs(y-v))),
           'rmse_naive':float(np.sqrt(np.mean((y-base)**2))),'mae_naive':float(np.mean(abs(y-base))),
           'mape_pct':float(np.mean(abs(y-v)/y)*100),'mape_naive_pct':float(np.mean(abs(y-base)/y)*100),
           'mse_piora_vs_naive_pct':float((np.mean((y-v)**2)/np.mean((y-base)**2)-1)*100),
           'acerto_sinal':float(np.mean(np.sign(v/base-1)==np.sign(y/base-1))),
           'epoca_escolhida':c['epoca_escolhida'],'n':len(y),'recarga_exata_registrada':c['recarga_exata']}
        np.testing.assert_allclose(m['rmse'],c['metricas_validacao']['rmse_usdt'])
        resultados[nome]=m;previsoes[nome]=v
        historicos[nome]=[json.loads(l) for l in (d/'epocas.jsonl').read_text().splitlines()]
    a,b=historicos.values();va,vb=previsoes.values()
    inicio=next(i for i in range(len(a)) if any(a[i][k]!=b[i][k] for k in ['perda_treino_rmse_lotes','rmse_global_validacao']))
    sinal=lambda x:np.where((x>0)&(abs(x/base-1)>.002),np.sign(x/base-1),0)
    r={'utc':agora(),'execucao':ptr,'natureza':'Diagnóstico posterior; não é conclusão do estudo ou nova avaliação de teste.',
       'resultados_validacao':resultados,'primeira_divergencia_epoca':inicio+1,
       'delta_rmse_validacao_primeira_divergencia':a[inicio]['rmse_global_validacao']-b[inicio]['rmse_global_validacao'],
       'diferenca_previsoes_max_usdt':float(abs(va-vb).max()),'diferenca_previsoes_media_usdt':float(abs(va-vb).mean()),
       'dias_sinal_operacional_divergente':int((sinal(va)!=sinal(vb)).sum()),
       'controle_mesma_epoca':resultados['seed_42']['epoca_escolhida']==resultados['controle_42']['epoca_escolhida'],
       'fontes_analise_sha256':sha256(__file__),'novos_treinos':0,'novas_simulacoes':0}
    if gpu:
        import torch,subprocess
        from modelos.cryptomamba_diario import construir
        from treinamento.otimizacao import fixar_seed
        if subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip():raise RuntimeError('GPU ocupada.')
        fixar_seed(42);rede=construir(f['configuracao']);rede.eval()
        x=torch.randn(32,6,14,device='cuda');x[:,0]=torch.arange(14,device='cuda')*86400+1500000000
        x[:,1:5]=x[:,1:5]*100+50000;x[:,5]=abs(x[:,5])*.0001
        y=torch.full((32,),50000.,device='cuda');grads=[];outs=[]
        for _ in range(20):
            rede.zero_grad(set_to_none=True);v=rede(x);torch.sqrt(((v-y)**2).mean()+1e-8).backward()
            outs.append(v.detach().cpu().numpy().copy());grads.append({n:w.grad.detach().cpu().numpy().copy() for n,w in rede.named_parameters() if w.grad is not None})
        diferentes={n:max(float(abs(g[n]-grads[0][n]).max()) for g in grads[1:]) for n in grads[0]}
        diferentes={n:v for n,v in diferentes.items() if v!=0}
        pesos={}
        for ep in (1,2):
            ca=torch.load(p/f'ajustes/seed_42/checkpoints/epoca_{ep:04d}.pt',map_location='cpu',weights_only=True)['pesos']
            cb=torch.load(p/f'ajustes/controle_42/checkpoints/epoca_{ep:04d}.pt',map_location='cpu',weights_only=True)['pesos']
            pesos[str(ep)]={'iguais':all(torch.equal(ca[n],cb[n]) for n in ca),'max_abs':max(float(abs(ca[n]-cb[n]).max()) for n in ca)}
        r['sonda_artificial']={'repeticoes':20,'mesmos_pesos_entradas_alvos':True,'passos_otimizador':0,'forward_exato':all(np.array_equal(outs[0],v) for v in outs),
             'gradientes_divergentes':diferentes,'deterministic_enabled':torch.are_deterministic_algorithms_enabled(),
             'warn_only':torch.is_deterministic_algorithms_warn_only_enabled(),'pesos_iguais_inicio_treinos':pesos}
    dest=RAIZ/'registros/cryptomamba_diario/conferencias'/agora().replace(':','').replace('+','_')
    dest.mkdir(parents=True,exist_ok=False);salvar_json(dest/'diagnostico.json',r)
    print(json.dumps({'recibo':str(dest.relative_to(RAIZ)),'resultados':r},ensure_ascii=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--gpu',action='store_true');executar(p.parse_args().gpu)
