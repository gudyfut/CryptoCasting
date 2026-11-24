"""Identidade do ambiente oficial, separada de métricas de mercado."""
import platform
import importlib
import importlib.metadata
import inspect
from pathlib import Path
from infraestrutura.artefatos import sha256


def conferir():
    import torch
    if platform.system() != 'Linux' or not torch.cuda.is_available():
        raise RuntimeError('Qualificação/execução requer WSL/Linux e CUDA; sem fallback.')
    from mamba_ssm import Mamba
    arquivos = {'mamba': Path(inspect.getfile(Mamba))}
    for m in ('mamba_ssm.ops.selective_scan_interface', 'selective_scan_cuda', 'causal_conv1d_cuda'):
        arquivos[m] = Path(importlib.import_module(m).__file__)
    return {'python': platform.python_version(), 'torch': str(torch.__version__), 'cuda': torch.version.cuda,
            'host': platform.node(), 'gpu': torch.cuda.get_device_name(),
            'implementacao_instalada': {m: sha256(p) for m, p in arquivos.items()},
            'pacotes': {m: importlib.metadata.version(m) for m in ('mamba_ssm', 'causal_conv1d', 'numpy', 'pandas', 'statsmodels', 'pyarrow')}}
