import numpy as np
from System.Factor import Factor


class FactorAskDepth(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

    def calculate(self):
        price = self._getLastTickData("AskPrice")
        p0, p1 = price[0], price[-1]
        if p0 < 1e-4 or p1 < 1e-4:
            lastfv = self.getLastFactorValue()
            if lastfv is None:
                factorValue = 0
            else:
                factorValue = lastfv
        else:
            factorValue = - (p0 / p1 - 1) * 1000

        self._addFactorValue(factorValue)