"""Comissão no ativo recebido no Spot; colateral e PnL separados nos futuros."""
import math
from dataclasses import dataclass


@dataclass
class Conta:
    saldo: float
    futuro: bool
    quantidade: float = 0.
    preco_medio: float = 0.

    def patrimonio(self, preco):
        return self.saldo + self.quantidade * (preco-self.preco_medio if self.futuro else preco)

    def negociar(self, delta, preco, taxa, reduce_only=False):
        if not all(math.isfinite(x) for x in [self.saldo, self.quantidade, delta, preco, taxa]) or preco <= 0 or not 0 <= taxa < 1:
            raise ValueError('Conta/ordem nao finita ou preco/taxa invalido.')
        anterior = self.quantidade
        if reduce_only and (not self.futuro or anterior*delta >= 0 or abs(delta)>abs(anterior)+1e-12):
            raise ValueError('reduceOnly nao pode abrir/inverter posicao.')
        custo = abs(delta)*preco*taxa
        realizado = 0.
        nova = anterior+delta
        if not self.futuro:
            debito = delta*preco + (custo if delta < 0 else 0.)
            if nova < -1e-12 or self.saldo-debito < -1e-8:
                raise ValueError('Spot nao permite saldo negativo ou venda descoberta.')
            self.saldo -= debito
            if delta > 0:
                nova -= delta*taxa
        else:
            if anterior*delta < 0:
                realizado = min(abs(anterior),abs(delta))*math.copysign(1.,anterior)*(preco-self.preco_medio)
            if abs(nova) < 1e-12:
                self.preco_medio = 0.
            elif anterior == 0 or anterior*nova < 0:
                self.preco_medio = preco
            elif anterior*delta > 0:
                self.preco_medio = (abs(anterior)*self.preco_medio+abs(delta)*preco)/abs(nova)
            self.saldo += realizado-custo
        # Evita que 0,101 seja armazenado como 0,10099999 e perca um lote ao fechar.
        self.quantidade = 0. if abs(nova)<1e-12 else round(nova,12)
        return custo, realizado
