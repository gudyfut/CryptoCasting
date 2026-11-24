"""Saldo Spot e colateral de futuros: nocional vendido não vira caixa livre."""
from dataclasses import dataclass


@dataclass
class Conta:
    saldo: float
    futuro: bool
    quantidade: float = 0.0
    preco_medio: float = 0.0

    def patrimonio(self, preco):
        if self.futuro:
            return self.saldo + self.quantidade*(preco-self.preco_medio)
        return self.saldo + self.quantidade*preco

    def negociar(self, delta, preco, taxa):
        comissao = abs(delta)*preco*taxa
        realizado = 0.0
        anterior = self.quantidade
        nova = anterior+delta
        if abs(nova) < 1e-12:
            nova = 0.0
        if not self.futuro:
            if nova < -1e-12 or self.saldo-delta*preco-comissao < -1e-8:
                raise ValueError('Spot nao admite divida ou venda descoberta.')
            self.saldo -= delta*preco+comissao
        else:
            if anterior*delta < 0:
                encerrada = min(abs(anterior), abs(delta))
                realizado = encerrada*(1 if anterior>0 else -1)*(preco-self.preco_medio)
            if nova == 0:
                self.preco_medio = 0.0
            elif anterior == 0 or anterior*nova < 0:
                self.preco_medio = preco
            elif anterior*delta > 0:
                self.preco_medio = (abs(anterior)*self.preco_medio+abs(delta)*preco)/abs(nova)
            self.saldo += realizado-comissao
        self.quantidade = nova
        return comissao, realizado
