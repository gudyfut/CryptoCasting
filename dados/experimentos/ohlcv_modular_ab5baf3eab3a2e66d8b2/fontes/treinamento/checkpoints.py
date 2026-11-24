"""Cada melhora é imutável; seleção aponta arquivo íntegro e contrato completo."""
from pathlib import Path
from infraestrutura.artefatos import salvar_json, ler_json, sha256, conferir_arquivos
from modelos.neurais import empacotar_pesos, restaurar_pesos


def guardar(destino, rede, vinculo, epoca, mse):
    import torch
    destino = Path(destino)
    pasta = destino / 'checkpoints'
    pasta.mkdir(parents=True, exist_ok=True)
    nome = f'epoca_{epoca:03d}.pt'
    p = pasta / nome
    if p.exists():
        raise FileExistsError('Checkpoint de época já existe; não sobrescrever.')
    pacote = {'versao': 1, 'vinculo': vinculo, 'epoca': epoca, 'mse_validacao': mse,
              'modelo': empacotar_pesos(rede)}
    parcial = p.with_suffix('.parcial')
    if parcial.exists():
        raise FileExistsError('Checkpoint parcial exige nova tentativa.')
    torch.save(pacote, parcial)
    parcial.replace(p)
    recibo = {'arquivo': 'checkpoints/' + nome, 'sha256': sha256(p), 'epoca': epoca,
              'mse_validacao': mse, 'vinculo': vinculo}
    salvar_json(destino / 'selecao.json', recibo)
    return recibo


def carregar(destino, rede, vinculo):
    import torch
    destino = Path(destino)
    r = ler_json(destino / 'selecao.json')
    if r['vinculo'] != vinculo:
        raise ValueError('Checkpoint pertence a outra execução/célula/receita.')
    conferir_arquivos(destino, {r['arquivo']: r['sha256']})
    p = torch.load(destino / r['arquivo'], map_location='cpu', weights_only=True)
    if (p['versao'] != 1 or p['vinculo'] != vinculo or p['epoca'] != r['epoca']
            or p['mse_validacao'] != r['mse_validacao']):
        raise ValueError('Metadados de seleção divergentes.')
    restaurar_pesos(rede, p['modelo'])
    rede.eval()
    return r
