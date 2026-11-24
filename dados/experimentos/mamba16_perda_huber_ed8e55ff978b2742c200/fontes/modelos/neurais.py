"""Fábrica, validação e inferência neural; nenhum otimizador ou ciclo de treino."""
from copy import deepcopy
from dataclasses import asdict
import numpy as np
from infraestrutura.artefatos import RAIZ, ler_json
from .contratos import montar_resultado


def carregar_configuracao(caminho=None):
    c = ler_json(caminho or RAIZ / 'configuracoes/modelos_ohlcv24_001.json')
    if (set(c) != {'versao', 'backend', 'dispositivo', 'normalizacao_bloco', 'mamba', 'lstm'}
            or c['versao'] != 1 or c['backend'] != 'oficial' or c['dispositivo'] != 'cuda'
            or c['normalizacao_bloco'] != 'pre_layernorm'):
        raise ValueError('Configuração neural desconhecida; exige oficial/CUDA/pré-LN.')
    for nome in ('mamba', 'lstm'):
        p = c[nome]
        chaves = {'largura', 'camadas', 'dropout'}
        if nome == 'mamba':
            chaves |= {'estado', 'convolucao', 'expansao'}
        if set(p) != chaves:
            raise ValueError(f'Parâmetros desconhecidos ou ausentes: {nome}')
        for k in chaves - {'dropout'}:
            if type(p[k]) is not int or p[k] <= 0:
                raise ValueError(f'Parâmetro inteiro positivo obrigatório: {nome}/{k}')
        if type(p['dropout']) not in (int, float) or not 0 <= p['dropout'] < 1:
            raise ValueError('Dropout deve estar em [0,1).')
        if nome == 'mamba' and (p['convolucao'] not in (2, 3, 4) or p['estado'] > 256):
            raise ValueError('Dimensões não suportadas pelos kernels CUDA deste contrato.')
    return c


def conferir_tensor(x, especificacao):
    import torch
    if (not isinstance(x, torch.Tensor) or x.ndim != 3 or x.shape[0] == 0
            or tuple(x.shape[1:]) != (especificacao.contexto, especificacao.dimensao_entrada)):
        raise ValueError('Entrada deve ter formato [lote, contexto, canais] declarado.')
    if x.dtype != torch.float32 or x.device.type != 'cuda' or not torch.isfinite(x).all():
        raise ValueError('Entrada exige float32 finito em CUDA; sem fallback.')


def criar_rede(nome, especificacao, caminho_configuracao=None):
    import torch
    c = carregar_configuracao(caminho_configuracao)
    if nome not in ('mamba', 'lstm'):
        raise ValueError('Família neural desconhecida.')
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA indisponível; nenhum modelo alternativo será usado.')
    if nome == 'mamba':
        from .mamba import RedeMamba
        rede = RedeMamba(especificacao, c['mamba'])
    else:
        from .lstm import RedeLSTM
        rede = RedeLSTM(especificacao, c['lstm'])
    rede.especificacao = especificacao
    rede.familia = nome
    rede.configuracao_modelo = deepcopy(c)
    return rede.to(device='cuda', dtype=torch.float32).eval()


def inferir_normalizado(rede, lote):
    import torch
    if rede.especificacao != lote.especificacao:
        raise ValueError('Rede e lote têm contratos/canais/escalas diferentes.')
    if rede.training:
        raise ValueError('Inferência exige eval(); não alterar modo silenciosamente.')
    if lote.entradas.dtype != np.float32:
        raise ValueError('Lote deve preservar float32, sem conversão silenciosa.')
    x = torch.as_tensor(lote.entradas, device='cuda')
    conferir_tensor(x, lote.especificacao)
    with torch.inference_mode():
        y = rede(x)
    if y.shape != (len(x),) or not torch.isfinite(y).all():
        raise ValueError('Rede deve produzir um escalar finito por origem.')
    return y.cpu().numpy().astype(np.float64)


def prever_neural(rede, consumo, pedido, tamanho_lote=64):
    if type(tamanho_lote) is not int or tamanho_lote <= 0:
        raise ValueError('Tamanho de lote inválido.')
    from .contratos import PedidoPrevisao
    valores = []
    for inicio in range(0, len(pedido.origens), tamanho_lote):
        sub = PedidoPrevisao(pedido.identidade, pedido.particao, pedido.origens.iloc[inicio:inicio + tamanho_lote].reset_index(drop=True))
        z = inferir_normalizado(rede, consumo.lote_neural(sub))
        valores.extend(consumo.decodificar_saida_neural(sub, z))
    return montar_resultado(pedido, valores)


def empacotar_pesos(rede):
    """Somente pesos e contrato. Não afirma que a rede tenha sido treinada."""
    return {'familia': rede.familia, 'especificacao': asdict(rede.especificacao),
            'configuracao': deepcopy(rede.configuracao_modelo),
            'pesos': {k: v.detach().cpu().clone() for k, v in rede.state_dict().items()}}


def restaurar_pesos(rede, pacote):
    if (set(pacote) != {'familia', 'especificacao', 'configuracao', 'pesos'}
            or pacote['familia'] != rede.familia or pacote['especificacao'] != asdict(rede.especificacao)
            or pacote['configuracao'] != rede.configuracao_modelo):
        raise ValueError('Pesos incompatíveis com família, configuração ou contrato de entradas.')
    rede.load_state_dict(pacote['pesos'], strict=True)
