"""Mesmos módulos e inicialização; somente posição da LayerNorm muda."""
from previsao24.redes import RedeMamba


class RedeMambaPreNormalizada(RedeMamba):
    def forward(self, x):
        x = self.projecao(x)
        for bloco, norma in zip(self.blocos, self.normas):
            x = x + bloco(norma(x))
        return self.saida(self.norma_final(self.dropout(x))[:, -1, :]).squeeze(-1)


def criar(nome, c):
    if nome != 'mamba' or c['backend'] != 'oficial':
        raise ValueError('Este ciclo aceita exclusivamente Mamba oficial.')
    posicao = c['normalizacao_mamba']
    if posicao == 'pre':
        return RedeMambaPreNormalizada(c['mamba'])
    if posicao == 'pos':
        return RedeMamba(c['mamba'])
    raise ValueError('Posição da normalização não reconhecida.')
