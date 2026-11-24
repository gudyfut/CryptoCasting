"""Treinamento reprodutível; a função recebe apenas treino e validação."""
import json
import math
import time
from pathlib import Path
import numpy as np
import torch
from infraestrutura.artefatos import agora, ler_json, salvar_json, sha256
from treinamento.otimizacao import fixar_seed
from .modelo import LSTMDiaria


def inferir(rede, x, dispositivo='cuda', lote=32):
    rede.eval()
    with torch.inference_mode():
        return np.concatenate([rede(torch.as_tensor(x[i:i+lote], device=dispositivo)).cpu().numpy()
                               for i in range(0, len(x), lote)]).astype(np.float64)


def ajustar(treino, validacao, cfg, seed, destino, vinculo, dispositivo='cuda', epocas=None):
    d = Path(destino)
    d.mkdir(parents=True, exist_ok=False)
    (d/'checkpoints').mkdir()
    total = cfg['epocas'] if epocas is None else epocas
    salvar_json(d/'inicio.json', dict(utc=agora(), seed=seed, vinculo=vinculo,
                                      configuracao=cfg, epocas=total, dispositivo=dispositivo))
    fixar_seed(seed)
    rede = LSTMDiaria().to(dispositivo)
    ot = torch.optim.Adam(rede.parameters(), lr=cfg['taxa'], weight_decay=cfg['weight_decay'])
    agenda = torch.optim.lr_scheduler.StepLR(ot, cfg['scheduler_passo'], gamma=cfg['scheduler_gamma'])
    x = torch.as_tensor(treino['x'], device=dispositivo)
    y = torch.as_tensor(treino['y'], dtype=torch.float32, device=dispositivo)
    gerador = torch.Generator().manual_seed(seed)
    inicio = time.monotonic()
    melhor = math.inf
    for epoca in range(1, total+1):
        if time.monotonic()-inicio > cfg['limite_segundos_por_ajuste']:
            raise TimeoutError('Limite por ajuste alcançado; preservar a tentativa.')
        rede.train()
        ordem = torch.randperm(len(x), generator=gerador).numpy()
        soma = 0.0
        taxa = ot.param_groups[0]['lr']
        for i in range(0, len(ordem), cfg['lote']):
            ix = ordem[i:i+cfg['lote']]
            ot.zero_grad(set_to_none=True)
            pred = rede(x[ix])
            if pred.shape != y[ix].shape:
                raise ValueError('Alvo e previsão com dimensões diferentes.')
            perda = torch.sqrt(torch.mean((pred-y[ix])**2)+cfg['epsilon_raiz'])
            if not torch.isfinite(perda):
                raise ValueError('Perda não finita.')
            perda.backward()
            if not all(torch.isfinite(p.grad).all().item() for p in rede.parameters() if p.grad is not None):
                raise ValueError('Gradiente não finito.')
            ot.step()
            soma += float(perda.detach())*len(ix)
        prev = inferir(rede, validacao['x'], dispositivo)
        rmse = float(np.sqrt(np.mean((prev-validacao['y'])**2)))
        if not np.isfinite(rmse):
            raise ValueError('Validação não finita.')
        if rmse < melhor:
            melhor = rmse
            melhor_prev = prev.copy()
            arquivo = d/'checkpoints'/f'epoca_{epoca:04d}.pt'
            torch.save(dict(pesos={k:v.detach().cpu() for k,v in rede.state_dict().items()},
                            epoca=epoca, vinculo=vinculo), arquivo)
            salvar_json(d/'selecao.json', dict(epoca=epoca, rmse_validacao=rmse,
                        checkpoint=arquivo.relative_to(d).as_posix(), sha256=sha256(arquivo)))
        agenda.step()
        linha = dict(epoca=epoca, perda_treino_rmse_lotes=soma/len(x),
                     rmse_global_validacao_retorno=rmse, taxa=taxa, segundos=time.monotonic()-inicio)
        with (d/'epocas.jsonl').open('a', encoding='utf-8') as f:
            f.write(json.dumps(linha)+'\n')
        salvar_json(d/'progresso.json', dict(utc=agora(), situacao='treinando', epoca=epoca,
                                            total=total, segundos=time.monotonic()-inicio))
        if epoca == 1 or epoca % 25 == 0:
            print('EPOCA', seed, epoca, '/', total, 'RMSE_V', rmse, flush=True)
    sel = ler_json(d/'selecao.json')
    assert sha256(d/sel['checkpoint']) == sel['sha256']
    ck = torch.load(d/sel['checkpoint'], map_location='cpu', weights_only=True)
    rede.load_state_dict(ck['pesos'], strict=True)
    np.testing.assert_array_equal(inferir(rede, validacao['x'], dispositivo), melhor_prev)
    np.savez_compressed(d/'validacao.npz', previsoes=melhor_prev,
                        **{k:v for k,v in validacao.items() if k != 'x'})
    resultado = dict(utc=agora(), situacao='concluido', seed=seed, epocas=total,
                     epoca_escolhida=sel['epoca'], checkpoint=sel, recarga_exata=True,
                     parametros=sum(p.numel() for p in rede.parameters()),
                     segundos=time.monotonic()-inicio, vinculo=vinculo)
    salvar_json(d/'conclusao.json', resultado)
    salvar_json(d/'progresso.json', resultado)
    return resultado
