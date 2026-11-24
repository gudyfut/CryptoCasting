"""Ajuste isolado; checkpoints por melhora e recarga exata antes de publicar."""
import math
import time
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from infraestrutura.artefatos import salvar_json, ler_json, sha256, agora
from treinamento.otimizacao import fixar_seed
from .rede import Rede, editar_cabeca

def metricas(y, p):
    y, p = np.asarray(y, float), np.asarray(p, float)
    assert y.shape == p.shape and np.isfinite(y).all() and np.isfinite(p).all()
    e = p-y
    mse = math.fsum(float(v)**2 for v in e)/len(e)
    nz = y != 0
    rec = [float(np.mean(np.sign(p[y*s > 0]) == s)) for s in [-1,1] if (y*s>0).any()]
    return {'n': len(e), 'mse': mse, 'rmse': math.sqrt(mse),
        'mae': math.fsum(abs(float(v)) for v in e)/len(e),
        'mse_naive': math.fsum(float(v)**2 for v in y)/len(y),
        'vies': float(e.mean()), 'sd_previsao': float(p.std()), 'sd_alvo': float(y.std()),
        'acuracia_direcional': float(np.mean(np.sign(p[nz]) == np.sign(y[nz]))),
        'balanced_accuracy': float(np.mean(rec))}

def prever(rede, dados, indices):
    rede.eval()
    valores = []
    with torch.inference_mode():
        for i in range(0, len(indices), 64):
            x = torch.as_tensor(dados.janelas(indices[i:i+64]), device='cuda')
            z = rede(x)
            assert z.shape == (len(x),) and torch.isfinite(z).all()
            valores.extend(z.cpu().numpy().astype(float)*dados.ys+dados.ym)
    return np.array(valores)

def atualizar(rede, opt, x, y, perda):
    opt.zero_grad(set_to_none=True)
    soma = 0.
    for i in range(0, len(x), 32):
        p = rede(x[i:i+32]); real = y[i:i+32]
        assert p.shape == real.shape
        v = (torch.nn.functional.mse_loss(p, real, reduction='sum') if perda == 'mse'
             else 2*torch.nn.functional.huber_loss(p, real, reduction='sum', delta=1.))
        assert torch.isfinite(v)
        (v/len(x)).backward(); soma += float(v.detach().cpu())
    norma = float(torch.nn.utils.clip_grad_norm_(rede.parameters(), 1., error_if_nonfinite=True))
    opt.step()
    return soma, norma

def salvar_pesos(p, rede, vinculo):
    if p.exists():
        raise FileExistsError(str(p))
    torch.save({'vinculo': vinculo, 'pesos': {k:v.detach().cpu().clone() for k,v in rede.state_dict().items()}}, p)
    return sha256(p)

def carregar_pesos(p, h, rede, vinculo):
    assert sha256(p) == h
    q = torch.load(p, map_location='cpu', weights_only=True)
    assert q['vinculo'] == vinculo
    rede.load_state_dict(q['pesos'], strict=True)
    rede.eval()

def ajustar(dados, receita, seed, destino, vinculo, limite_segundos=2700, epocas=100, paciencia=10):
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=False)
    (destino/'checkpoints').mkdir()
    salvar_json(destino/'inicio.json', {'utc': agora(), 'vinculo': vinculo, 'receita': receita,
                                      'seed': seed, 'limite_segundos': limite_segundos})
    salvar_json(destino/'escalas.json', dados.escalas)
    fixar_seed(seed)
    rede = Rede(receita, dados.matriz.shape[1]).cuda()
    grupos = [{'params': [], 'weight_decay': receita['decay']}, {'params': [], 'weight_decay': 0.}]
    nomes = [[], []]
    for n, p in rede.named_parameters():
        g = int(getattr(p, '_no_weight_decay', False))
        grupos[g]['params'].append(p); nomes[g].append(n)
    grupos = [g for g in grupos if g['params']]
    cls = torch.optim.AdamW if receita['otimizador'] == 'AdamW' else torch.optim.Adam
    opt = cls(grupos, lr=receita['taxa'], betas=(.9,.999), eps=1e-8)
    sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, factor=.5, patience=2, min_lr=.000025) if receita['scheduler']=='plateau' else None
    salvar_json(destino/'otimizador.json', {'classe': receita['otimizador'], 'decay': receita['decay'],
                                         'nomes_com_decay': nomes[0], 'nomes_isentos': nomes[1]})
    ix = dados.indices['treino']; val = dados.indices['validacao']
    x = torch.as_tensor(dados.janelas(ix), device='cuda')
    y = torch.as_tensor(((dados.y[ix]-dados.ym)/dados.ys).astype(np.float32), device='cuda')
    gen = torch.Generator().manual_seed(seed)
    inicio = time.monotonic(); melhor = math.inf; espera = 0; historico = []
    torch.cuda.reset_peak_memory_stats()
    for epoca in range(1, epocas+1):
        rede.train(); ordem = torch.randperm(len(y), generator=gen).to('cuda')
        soma = 0.; grad = []
        taxa = opt.param_groups[0]['lr']
        for i in range(0, len(y), 64):
            if time.monotonic()-inicio > limite_segundos:
                raise TimeoutError('Limite do ajuste; tentativa preservada e nao usada como concluida.')
            j = ordem[i:i+64]
            valor, norma = atualizar(rede, opt, x[j], y[j], receita['perda'])
            soma += valor; grad.append(norma)
        p = prever(rede, dados, val)
        mse = metricas(dados.y[val], p)['mse']
        melhora = mse < melhor
        if melhora:
            melhor, espera = mse, 0
            arquivo = destino/'checkpoints'/f'epoca_{epoca:03}.pt'
            h = salvar_pesos(arquivo, rede, vinculo)
            selecao = {'arquivo': str(arquivo.relative_to(destino)), 'sha256': h, 'epoca': epoca, 'mse': mse}
            salvar_json(destino/'selecao.json', selecao)
        else:
            espera += 1
        historico.append({'epoca': epoca, 'mse_validacao': mse, 'perda_treino': soma/len(y),
            'melhorou': melhora, 'taxa': taxa, 'norma_gradiente_media': float(np.mean(grad)),
            'fracao_clipping': float(np.mean(np.array(grad)>1)), 'segundos': time.monotonic()-inicio})
        salvar_json(destino/'epocas.json', historico)
        print(f'{destino.parent.name}/{destino.name} epoca={epoca} mse_val={mse:.10g} espera={espera}', flush=True)
        if sched:
            sched.step(mse)
        if espera >= paciencia:
            break
    del x, y
    carregar_pesos(destino/selecao['arquivo'], selecao['sha256'], rede, vinculo)
    antes = prever(rede, dados, val)
    assert metricas(dados.y[val], antes)['mse'] == selecao['mse']
    if receita['ganho_saida'] != 1.:
        editar_cabeca(rede, receita['ganho_saida'], dados.ym, dados.ys)
        depois = prever(rede, dados, val)
        np.testing.assert_allclose(depois, antes*receita['ganho_saida'], rtol=2e-5, atol=2e-8)
    final = destino/'checkpoints/final.pt'
    hf = salvar_pesos(final, rede, vinculo)
    outra = Rede(receita, dados.matriz.shape[1]).cuda()
    carregar_pesos(final, hf, outra, vinculo)
    resultado = {'utc': agora(), 'seed': seed, 'bloco': dados.bloco, 'receita': receita,
        'epoca': selecao['epoca'], 'epocas_executadas': len(historico),
        'parametros': sum(p.numel() for p in rede.parameters()), 'recarga_exata': True,
        'segundos': time.monotonic()-inicio, 'checkpoint_final_sha256': hf,
        'memoria_cuda_maxima_bytes': torch.cuda.max_memory_allocated()}
    for parte, ids in dados.indices.items():
        if parte == 'treino':
            ids = ids[np.linspace(0, len(ids)-1, min(2048,len(ids))).astype(int)]
        p = prever(rede, dados, ids); pp = prever(outra, dados, ids)
        np.testing.assert_array_equal(p, pp)
        q = dados.tabela.iloc[ids].copy(); q['previsao'] = p
        q.to_parquet(destino/f'previsoes_{parte}.parquet', index=False)
        resultado['treino_amostra_fixa' if parte=='treino' else parte] = metricas(dados.y[ids], p)
    with torch.inference_mode():
        ids = val[np.linspace(0,len(val)-1,min(128,len(val))).astype(int)]
        z = rede.representar(torch.as_tensor(dados.janelas(ids),device='cuda')).cpu().numpy()
        resultado['diagnostico'] = {'sd_representacao_media': float(z.std(0).mean()),
            'norma_pesos_saida': float(rede.saida.weight.norm().cpu()),
            'fracao_clipping_ultima_epoca': historico[-1]['fracao_clipping']}
    salvar_json(destino/'resultado.json', resultado)
    salvar_json(destino/'conclusao.json', {'utc': agora(), 'status': 'concluido',
        'arquivos': {p.relative_to(destino).as_posix():sha256(p) for p in destino.rglob('*') if p.is_file()}})
    del rede, outra, opt
    torch.cuda.empty_cache()
    return resultado

def conferir_controle(a, b):
    a,b = Path(a),Path(b)
    ra,rb = ler_json(a/'resultado.json'),ler_json(b/'resultado.json')
    assert ra['epoca'] == rb['epoca']
    dif = abs(ra['validacao']['mse']-rb['validacao']['mse'])/ra['validacao']['mse']
    assert dif <= 1e-4
    maximos = {}
    for parte in ['validacao'] + (['teste'] if 'teste' in ra else []):
        qa,qb = pd.read_parquet(a/f'previsoes_{parte}.parquet'),pd.read_parquet(b/f'previsoes_{parte}.parquet')
        pd.testing.assert_frame_equal(qa.drop(columns='previsao'),qb.drop(columns='previsao'))
        maximos[parte] = float(np.max(np.abs(qa.previsao-qb.previsao)))
        assert maximos[parte] <= 1e-5
    return {'mesma_epoca': True, 'diferenca_relativa_mse': dif, 'maxima_diferenca': maximos}
