"""Sondas posteriores de checkpoints: inferência/gradientes, sem optimizer ou treino.

Hooks removem ramos apenas em memória para medir contribuição, sem escolher
política, recalibrar previsões publicadas ou produzir novos backtests.
"""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import torch
from mamba_ssm import Mamba
from infraestrutura.artefatos import RAIZ, ler_json, sha256, conferir_arquivos, salvar_json
from entradas_modelo.padronizacao_diaria import preparar_com_escalas
from experimentos.cryptomamba_reproducivel.modelo import construir
from treinamento.otimizacao import fixar_seed


def prever(rede, x):
    rede.eval()
    with torch.inference_mode():
        return np.concatenate([rede(torch.as_tensor(x[i:i+32],device='cuda')).cpu().numpy() for i in range(0,len(x),32)]).astype(float)


def grupo(nome):
    if nome.endswith('A_log'): return 'A_log'
    if nome.endswith('.D'): return 'D'
    if '.op.' in nome: return 'outros_mamba'
    if '.norm.' in nome: return 'layernorm'
    return 'lineares'


def normas(rede):
    saida={}
    for nome,p in rede.named_parameters():
        g=saida.setdefault(grupo(nome),{'quadrados':0.,'n':0,'pequenos':0})
        a=p.detach().double()
        g['quadrados']+=float((a*a).sum());g['n']+=p.numel();g['pequenos']+=int((a.abs()<1e-6).sum())
    return {k:{'norma':v['quadrados']**.5,'rms':(v['quadrados']/v['n'])**.5,'n':v['n'],'fracao_abs_menor_1e6':v['pequenos']/v['n']} for k,v in saida.items()}


def estat(y,p):
    return {'media':float(p.mean()),'desvio':float(p.std()),'min':float(p.min()),'max':float(p.max()),'mse':float(np.mean((y-p)**2)),
            'correlacao':float(np.corrcoef(y,p)[0,1]) if p.std()>0 else None,'compras':int((p>.002).sum()),'vendas':int((p<-.002).sum())}


def executar():
    ptr=ler_json(RAIZ/'registros/padronizacao_diaria/execucao.json');p=RAIZ/ptr['pasta'];f=ler_json(p/'congelamento.json');c=f['configuracao']
    assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
    assert not ler_json(p/'processo.json')['ativo']
    fechamento=ler_json(p/'fechamento.json');conferir_arquivos(p,fechamento['arquivos'])
    # Todas as fontes utilizadas correspondem aos bytes congelados.
    for arq in (p/'fontes').rglob('*.py'):
        rel=arq.relative_to(p/'fontes')
        assert sha256(RAIZ/rel)==sha256(arq),str(rel)
    dados,esc=preparar_com_escalas(pd.read_parquet(RAIZ/f['diario']['pasta']/'diario.parquet'),c)
    assert esc==f['escalas']
    stamp=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%S.%fZ')
    dest=RAIZ/'registros/padronizacao_diaria/diagnosticos'/stamp;dest.mkdir(parents=True)
    resultado={'utc':stamp,'execucao':ptr,'codigo_sha256':sha256(Path(__file__)), 'atualizacoes_de_pesos':0,'carteiras_novas':0,'seeds':{},'populacoes':{}}
    media_treino=float(dados['treino']['y'].mean())
    for fase,z in dados.items():
        resultado['populacoes'][fase]={'n':len(z['y']),'media_alvo':float(z['y'].mean()),'desvio_alvo':float(z['y'].std()),
            'mse_zero':float(np.mean(z['y']**2)),'mse_media_treino':float(np.mean((z['y']-media_treino)**2)),
            'min_canais':z['x'].min(axis=(0,2)).tolist(),'max_canais':z['x'].max(axis=(0,2)).tolist()}
    previsoes_plot={}
    for seed in c['seeds']:
        fixar_seed(seed);rede=construir(c);norma_inicial=normas(rede)
        d=p/'ajustes'/f'seed_{seed}';sel=ler_json(d/'selecao.json');ck=torch.load(d/sel['checkpoint'],map_location='cpu',weights_only=True)
        assert sha256(d/sel['checkpoint'])==sel['sha256'];rede.load_state_dict(ck['pesos'],strict=True);rede.eval()
        antes={k:v.detach().cpu().clone() for k,v in rede.state_dict().items()}
        r={'epoca':sel['epoca'],'checkpoint_sha256':sel['sha256'],'normas_iniciais':norma_inicial,'normas_selecionadas':normas(rede),'fases':{},'ativacoes':{}}
        for fase,z in dados.items():
            pred=prever(rede,z['x']);r['fases'][fase]=estat(z['y'],pred)
            if fase!='treino':np.testing.assert_array_equal(pred,np.load(p/'publicacao/previsoes'/f'{fase}_{seed}.npz')['previsoes_retorno'])
            # Intervenção mecânica: zerar saída de cada Mamba, mantendo caminho residual.
            hooks=[m.register_forward_hook(lambda m,a,o:torch.zeros_like(o)) for m in rede.modules() if isinstance(m,Mamba)]
            sem=prever(rede,z['x'])
            for h in hooks:h.remove()
            r['fases'][fase]['sem_ramos_mamba']={'max_diferenca':float(abs(pred-sem).max()),'rms_diferenca':float(np.sqrt(np.mean((pred-sem)**2))), 'desvio':float(sem.std()),'media':float(sem.mean())}
            # Inferências perturbadas não são novos modelos nem testes de desempenho.
            idx=np.linspace(0,len(z['x'])-1,32,dtype=int);x=z['x'][idx].copy();base=pred[idx]
            sens={}
            for j,canal in enumerate(c['canais']):
                alterado=x.copy();alterado[:,j,:]=0
                sens[canal]=float(np.sqrt(np.mean((prever(rede,alterado)-base)**2)))
            r['fases'][fase]['rms_perturbacao_canal_zero_zscore']=sens
            if fase=='teste':previsoes_plot[str(seed)]=pred
            # Ativações dos 12 blocos em 32 janelas espaçadas.
            hooks=[];ativ={}
            for nome,m in rede.named_modules():
                if isinstance(m,Mamba):
                    def registrar(m,a,o,nome=nome):
                        ativ[nome]={'forma':list(a[0].shape),'rms_entrada':float(a[0].square().mean().sqrt()),'rms_saida':float(o.square().mean().sqrt())}
                    hooks.append(m.register_forward_hook(registrar))
            prever(rede,x)
            for h in hooks:h.remove()
            r['ativacoes'][fase]=ativ
        # Gradientes diagnósticos de seis lotes fixos do treino, sem optimizer.step.
        acum={};n=len(dados['treino']['x'])
        for inicio in np.linspace(0,n-32,6,dtype=int):
            rede.zero_grad(set_to_none=True)
            x=torch.as_tensor(dados['treino']['x'][inicio:inicio+32],device='cuda');y=torch.as_tensor(dados['treino']['y'][inicio:inicio+32],device='cuda',dtype=torch.float32)
            pred=rede(x);assert pred.shape==y.shape==(32,)
            perda=torch.sqrt(torch.mean((pred-y)**2)+c['treinamento']['epsilon_raiz']);perda.backward()
            for nome,t in rede.named_parameters():
                g=acum.setdefault(grupo(nome),{'grad2':0.,'l2_2':0.,'sem_grad':0})
                if t.grad is None:g['sem_grad']+=1;continue
                assert torch.isfinite(t.grad).all()
                g['grad2']+=float(t.grad.double().square().sum())/6
                g['l2_2']+=float((.001*t.detach().double()).square().sum())/6
        r['gradientes_seis_lotes']={k:{'norma_grad_rms':v['grad2']**.5,'norma_l2':v['l2_2']**.5,'sem_grad':v['sem_grad'],'razao_l2_grad':(v['l2_2']/v['grad2'])**.5 if v['grad2'] else None} for k,v in acum.items()}
        for k,v in rede.state_dict().items():assert torch.equal(antes[k],v.detach().cpu()),k
        hist=[json.loads(l) for l in (d/'epocas.jsonl').read_text().splitlines()]
        assert len(hist)==1000 and np.argmin([l['rmse_global_validacao_retorno'] for l in hist])+1==sel['epoca']
        r['historico']={'selecionada':hist[sel['epoca']-1],'primeira':hist[0],'ultima':hist[-1],
           'blocos100':[{'inicio':i+1,'min_val':min(l['rmse_global_validacao_retorno'] for l in hist[i:i+100]),'taxa':hist[i]['taxa']} for i in range(0,1000,100)]}
        resultado['seeds'][str(seed)]=r
        print('SEED_CONFERIDA',seed,flush=True)
        del rede;torch.cuda.empty_cache()
    conferir_arquivos(p,fechamento['arquivos'])
    resultado['integridade_antes_depois']=True
    resultado['limites']='Sondas condicionadas aos checkpoints; nenhum ajuste de pesos, seleção de política ou backtest. Perturbações de canais podem sair da distribuição e não estimam importância causal. Gradientes medidos no checkpoint não reconstituem trajetórias do Adam. Comparar norma de L2 e gradiente não equivale a medir passo Adam.'
    salvar_json(dest/'diagnostico.json',resultado)
    np.savez_compressed(dest/'series.npz',origens=dados['teste']['origens_ms'],alvo=dados['teste']['y'],**previsoes_plot)
    print(json.dumps({'destino':dest.as_posix()},ensure_ascii=False),flush=True)


def trajetoria():
    """Checkpoints já salvos e decomposição afim, sem inferir épocas não salvas."""
    from experimentos.alvo_retorno_diario.entradas import preparar as preparar_original
    stamp=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%S.%fZ')
    dest=RAIZ/'registros/padronizacao_diaria/diagnosticos'/stamp;dest.mkdir(parents=True)
    rastros={};arquivos={};saida={'utc':stamp,'codigo_sha256':sha256(Path(__file__)),'trajetorias':{},'atualizacoes_de_pesos':0,'carteiras_novas':0}
    for versao,registro in [('referencia','retomada_alvo_diario'),('padronizado','padronizacao_diaria')]:
        ptr=ler_json(RAIZ/'registros'/registro/'execucao.json');p=RAIZ/ptr['pasta'];f=ler_json(p/'congelamento.json');c=f['configuracao']
        assert sha256(p/'congelamento.json')==ptr['congelamento_sha256']
        diario=pd.read_parquet(RAIZ/f['diario']['pasta']/'diario.parquet')
        dados=preparar_com_escalas(diario,c)[0] if versao=='padronizado' else preparar_original(diario,c)
        saida['trajetorias'][versao]={}
        for seed in c['seeds']:
            fixar_seed(seed);rede=construir(c);inicial={k:v.detach().cpu().clone() for k,v in rede.state_dict().items()}
            d=p/'ajustes'/f'seed_{seed}';sel=ler_json(d/'selecao.json');etapas=[('inicial',None)]
            checkpoints=sorted((d/'checkpoints').glob('*.pt'))
            if versao=='referencia':checkpoints=[checkpoints[0],d/sel['checkpoint']]
            etapas += [(arq.stem,arq) for arq in checkpoints]
            linhas=[]
            idx=np.linspace(0,len(dados['treino']['x'])-1,32,dtype=int);x=dados['treino']['x'][idx]
            for nome,arq in etapas:
                if arq:
                    arquivos[arq.relative_to(RAIZ).as_posix()]=sha256(arq)
                    rede.load_state_dict(torch.load(arq,map_location='cpu',weights_only=True)['pesos'],strict=True)
                else:rede.load_state_dict(inicial,strict=True)
                rede.eval();pred=prever(rede,x)
                ativ=[];hs=[]
                def registrar(m,a,o):ativ.append({'rms_saida_float64':float(o.double().square().mean().sqrt()),'max_saida':float(o.abs().max())})
                for m in rede.modules():
                    if isinstance(m,Mamba):hs.append(m.register_forward_hook(registrar))
                prever(rede,x)
                for h in hs:h.remove()
                hs=[m.register_forward_hook(lambda m,a,o:torch.zeros_like(o)) for m in rede.modules() if isinstance(m,Mamba)]
                sem=prever(rede,x)
                for h in hs:h.remove()
                linha={'checkpoint':nome,'normas':normas(rede),'max_delta_sem_mamba':float(abs(pred-sem).max()),'rms_delta_sem_mamba':float(np.mean((pred-sem)**2)**.5),'rms_saidas_blocos':[a['rms_saida_float64'] for a in ativ],'max_saidas_blocos':[a['max_saida'] for a in ativ]}
                if nome=='inicial':
                    rede.zero_grad(set_to_none=True);y=torch.as_tensor(dados['treino']['y'][idx],device='cuda',dtype=torch.float32)
                    loss=torch.sqrt(((rede(torch.as_tensor(x,device='cuda'))-y)**2).mean()+1e-8);loss.backward()
                    grads={}
                    for n,t in rede.named_parameters():
                        g=grads.setdefault(grupo(n),{'grad2':0.,'l2_2':0.})
                        g['grad2']+=float(t.grad.double().square().sum());g['l2_2']+=float((.001*t.detach().double()).square().sum())
                    linha['gradiente_inicial_lote_fixo']={k:{'grad':v['grad2']**.5,'l2':v['l2_2']**.5} for k,v in grads.items()}
                linhas.append(linha)
            # Decomposição exata do caminho residual linear selecionado.
            rede.load_state_dict(torch.load(d/sel['checkpoint'],map_location='cpu',weights_only=True)['pesos'],strict=True)
            w=np.eye(14);b=np.zeros(14)
            for bloco in rede.nucleo.blocks:
                linear=bloco[-1];a=linear.weight.detach().cpu().double().numpy();bias=linear.bias.detach().cpu().double().numpy()
                w=a@w;b=a@b+bias
            cw=rede.nucleo.post_process[1].weight.detach().cpu().double().numpy().reshape(6)
            cb=float(rede.nucleo.post_process[1].bias.detach().cpu()[0]);coef=cw[:,None]*w[0][None,:];intercepto=float(cw.sum()*b[0]+cb)
            dec={'intercepto':intercepto,'coeficientes':coef.tolist(),'fases':{}}
            for fase,z in dados.items():
                contribuicoes=np.einsum('nct,ct->nc',z['x'].astype(float),coef);linear=contribuicoes.sum(axis=1)+intercepto
                pred=prever(rede,z['x']);dec['fases'][fase]={'max_residuo_afim':float(abs(pred-linear).max()),'media_prevista':float(pred.mean()),'media_contribuicao_canais':dict(zip(c['canais'],contribuicoes.mean(axis=0).tolist())),'desvio_contribuicao_canais':dict(zip(c['canais'],contribuicoes.std(axis=0).tolist()))}
                if fase!='treino':np.testing.assert_array_equal(pred,np.load(p/'publicacao/previsoes'/f'{fase}_{seed}.npz')['previsoes_retorno'])
            saida['trajetorias'][versao][str(seed)]={'sondas_treino32':linhas,'decomposicao_residual':dec}
            print('TRAJETORIA',versao,seed,len(linhas),flush=True)
            del rede;torch.cuda.empty_cache()
    for arq,h in arquivos.items():assert sha256(RAIZ/arq)==h,arq
    saida['checkpoints_preservados']=arquivos
    saida['limites']='Gradientes sem atualizações. Trajetória parcial apenas nos checkpoints de melhora salvos. Sondas iniciais e por época usam 32 janelas de treino fixas; decomposição afim usa todas as fases, sem ajuste de coeficientes: derivados dos pesos existentes. Resíduo afim float64 versus rede float32 inclui arredondamento e contribuição não linear. Não é desempenho de modelo treinado sem regularização.'
    salvar_json(dest/'trajetoria.json',saida)
    (dest/'fonte_sondas.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps({'destino':dest.as_posix()}),flush=True)


if __name__=='__main__':
    import sys
    trajetoria() if '--trajetoria' in sys.argv else executar()
