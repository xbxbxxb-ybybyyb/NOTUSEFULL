import numpy as np
from System.Factor import Factor


class FactorBidDepth(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("bidP0List", [])
    def calculate(self):
        price = self._getLastTickData("BidPrice")
        p0, p1 = price[0], price[-1]
        if p0 < 1e-4 or p1 < 1e-4:
            lastfv = self.getLastFactorValue()
            if lastfv is None:
                factorValue = 0
            else:
                factorValue = lastfv
        else:
            factorValue = 10 / (abs(p0 - p1) * p0) if abs(p0 - p1) > 1e-4 else 0

        self._addFactorValue(factorValue)