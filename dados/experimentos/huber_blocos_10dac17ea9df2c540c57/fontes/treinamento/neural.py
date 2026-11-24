"""Ajuste e seleção não solicitam teste; avaliação vem após recarga do melhor."""
import time
import numpy as np
from infraestrutura.artefatos import salvar_json, agora
from modelos.neurais import criar_rede, prever_neural
from .otimizacao import fixar_seed, criar_otimizador, atualizar_lote
from .selecao import SelecaoEpoca
from . import checkpoints


def ajustar(consumo, familia, seed, cfg, configuracao_modelos, destino, vinculo):
    import torch
    fixar_seed(seed)
    rede = criar_rede(familia, consumo.especificacao, configuracao_modelos)
    otimizador, grupos = criar_otimizador(rede, cfg)
    salvar_json(destino / 'grupos_otimizador.json', grupos)
    # Cache somente de treino. Mantém os canais, janela e escala do consumidor.
    pedido = consumo.solicitar('treino')
    lotes = []
    for i in range(0, len(pedido.origens), 256):
        sub = consumo.solicitar('treino', np.arange(i, min(i + 256, len(pedido.origens))))
        lotes.append(consumo.lote_neural(sub).entradas)
    x = torch.as_tensor(np.concatenate(lotes), device='cuda')
    y = torch.as_tensor(consumo.alvos_supervisionados(pedido), device='cuda')
    del lotes
    val = consumo.solicitar('validacao')
    yval = consumo.alvos_supervisionados(val, padronizados=False)
    selecao = SelecaoEpoca(cfg['paciencia'])
    gerador = torch.Generator().manual_seed(seed)
    inicio = time.perf_counter()
    historico = []
    torch.cuda.reset_peak_memory_stats()
    for epoca in range(1, cfg['epocas'] + 1):
        rede.train()
        ordem = torch.randperm(len(y), generator=gerador).to('cuda')
        soma = 0.
        for i in range(0, len(y), cfg['batch']):
            indices = ordem[i:i + cfg['batch']]
            soma += atualizar_lote(rede, otimizador, x[indices], y[indices], cfg['microbatch'], cfg['clipping'])
        rede.eval()
        previsao = prever_neural(rede, consumo, val, cfg['batch']).previsao.to_numpy()
        mse = float(np.mean((previsao - yval)**2))
        melhorou = selecao.observar(epoca, mse)
        if melhorou:
            checkpoints.guardar(destino, rede, vinculo, epoca, mse)
        historico.append({'epoca': epoca, 'mse_treino_padronizado': soma / len(y),
                          'mse_validacao': mse, 'melhorou': melhorou, 'utc': agora(),
                          'segundos': time.perf_counter() - inicio})
        salvar_json(destino / 'epocas.json', historico)
        print(f'{familia} seed={seed} época={epoca} mse_val={mse:.9g} espera={selecao.espera}', flush=True)
        if selecao.parar:
            break
    checkpoints.carregar(destino, rede, vinculo)
    refeito = prever_neural(rede, consumo, val, cfg['batch']).previsao.to_numpy()
    if float(np.mean((refeito - yval)**2)) != selecao.melhor:
        raise ValueError('Checkpoint não reproduziu MSE usado na seleção.')
    recibo = {'modelo': familia, 'seed': seed, 'epoca_selecionada': selecao.epoca,
              'epocas_executadas': len(historico), 'parametros': sum(p.numel() for p in rede.parameters()),
              'segundos': time.perf_counter() - inicio, 'memoria_cuda_maxima_bytes': torch.cuda.max_memory_allocated()}
    salvar_json(destino / 'ajuste.json', recibo)
    return rede, recibo
