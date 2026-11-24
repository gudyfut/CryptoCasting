"""Qualificação exclusiva Mamba: pares, CUDA, atualização, repetição e recarga."""
import warnings
import numpy as np
import torch
from previsao24.arquivos import RAIZ, agora, ler_json, salvar_json
from previsao24.treino import fixar_seed
from experimento_penalizacao.qualificacao import ambiente
from experimento_penalizacao.otimizador import criar_otimizador, descrever_grupos
from .redes import criar


def executar(c, destino, referencia):
    registro = {'status': 'em_andamento', 'inicio_utc': agora(), 'ambiente': ambiente(), 'casos': []}
    salvar_json(destino / 'qualificacao.json', registro)
    try:
        anterior = ler_json(RAIZ / referencia['preparacao_caminho'] / 'qualificacao.json')['ambiente']
        for k in ('python', 'torch', 'cuda', 'gpu', 'versoes', 'mamba_fonte_sha256'):
            if registro['ambiente'][k] != anterior[k]:
                raise ValueError(f'Ambiente diverge do comparador: {k}')
        if not torch.cuda.is_available():
            raise RuntimeError('CUDA obrigatório.')
        t = c['treino']
        for w in c['contextos']:
            for posicao in ('pos', 'pre'):
                configuracao = {**c, 'normalizacao_mamba': posicao}
                repeticoes = []
                with warnings.catch_warnings(record=True) as avisos:
                    warnings.simplefilter('always')
                    for repeticao in range(2):
                        fixar_seed(20261020)
                        rede = criar('mamba', configuracao).cuda()
                        iniciais = {n: v.detach().clone() for n, v in rede.named_parameters()}
                        x = torch.randn(64, w, 1, device='cuda')
                        y = torch.randn(64, device='cuda')
                        otimizador = criar_otimizador(rede, t)
                        for passo in range(3):
                            rede.train()
                            otimizador.zero_grad(set_to_none=True)
                            for i in (0, 32):
                                perda = torch.nn.functional.mse_loss(rede(x[i:i+32]), y[i:i+32], reduction='sum') / 64
                                if not torch.isfinite(perda):
                                    raise ValueError('Perda não finita.')
                                perda.backward()
                            if any(p.grad is None or not torch.isfinite(p.grad).all() for p in rede.parameters()):
                                raise ValueError('Gradiente ausente/não finito.')
                            torch.nn.utils.clip_grad_norm_(rede.parameters(), t['clipping'], error_if_nonfinite=True)
                            otimizador.step()
                        if not any(not torch.equal(p, iniciais[n]) for n, p in rede.named_parameters()):
                            raise ValueError('Nenhum parâmetro atualizado.')
                        rede.eval()
                        with torch.inference_mode():
                            previsto = rede(x).cpu().numpy()
                            alterado = rede(x * 2).cpu().numpy()
                        if np.array_equal(previsto, alterado):
                            raise ValueError('Modelo insensível à mudança da entrada sintética.')
                        cp = destino / f'sintetico_mamba_W{w}_{posicao}_{repeticao}.pt'
                        torch.save(rede.state_dict(), cp)
                        nova = criar('mamba', configuracao).cuda()
                        nova.load_state_dict(torch.load(cp, map_location='cuda', weights_only=True))
                        nova.eval()
                        with torch.inference_mode():
                            recarga = nova(x).cpu().numpy()
                        np.testing.assert_array_equal(previsto, recarga)
                        assert previsto.shape == (64,) and np.isfinite(previsto).all()
                        repeticoes.append(previsto)
                        del rede, nova, otimizador, x, y, iniciais
                    diferenca = float(np.max(np.abs(repeticoes[0] - repeticoes[1])))
                    if diferenca > 1e-6:
                        raise ValueError('Repetição sintética excedeu 1e-6.')
                registro['casos'].append({'contexto': w, 'posicao': posicao, 'recarga_exata': True,
                    'atualizacao': True, 'sensibilidade_entrada': True, 'diferenca_repeticao': diferenca,
                    'avisos': [str(a.message) for a in avisos]})
                salvar_json(destino / 'qualificacao.json', registro)
                print(f'QUALIFICADO Mamba W{w} {posicao}', flush=True)
        registro['grupos'] = descrever_grupos(criar('mamba', {**c, 'normalizacao_mamba': 'pre'}), t)
        registro.update(status='aprovado', fim_utc=agora())
    except Exception as erro:
        registro.update(status='falha', fim_utc=agora(), erro=repr(erro))
        raise
    finally:
        salvar_json(destino / 'qualificacao.json', registro)
    return registro
