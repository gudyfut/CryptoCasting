"""Escolha por validação exclusivamente; empates mantêm a primeira época."""
from dataclasses import dataclass
import math


@dataclass
class SelecaoEpoca:
    paciencia: int
    melhor: float = math.inf
    epoca: int = 0
    espera: int = 0
    ultima: int = 0

    def observar(self, epoca, mse_validacao):
        if self.paciencia < 1 or epoca != self.ultima + 1 or not math.isfinite(mse_validacao) or mse_validacao < 0:
            raise ValueError('Época/MSE/paciência inválidos.')
        self.ultima = epoca
        melhorou = mse_validacao < self.melhor
        if melhorou:
            self.melhor, self.epoca, self.espera = float(mse_validacao), epoca, 0
        else:
            self.espera += 1
        return melhorou

    @property
    def parar(self):
        return self.espera >= self.paciencia


def escolher_arima(candidatos):
    validos = [c for c in candidatos if c['status'] == 'valido']
    if not validos:
        raise ValueError('Nenhuma ordem ARIMA válida; não substituir silenciosamente.')
    return min(validos, key=lambda c: (c['mse_validacao'], c['ordem'][0] + c['ordem'][2], c['ordem'][0], c['ordem'][2]))
