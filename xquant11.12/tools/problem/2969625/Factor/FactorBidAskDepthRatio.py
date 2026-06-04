import numpy as np
from System.Factor import Factor


class FactorBidAskDepthRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

    def calculate(self):
        askPrice = self._getLastTickData("AskPrice")
        bidPrice = self._getLastTickData("BidPrice")
        if askPrice[0] < 1e-4:
            ap0, ap1 = self._getLastTickData('MaxPrice'), self._getLastTickData('LastPrice')
        else:
            ap0, ap1 = askPrice[0], askPrice[4]
        askDepth = abs(ap0 - ap1) / ap0 if ap0 > 1e-4 and ap1 > 1e-4 else 0
        if bidPrice[0] < 1e-4:
            bp0, bp1 = self._getLastTickData('MinPrice'), self._getLastTickData('LastPrice')
        else:
            bp0, bp1 = bidPrice[0], bidPrice[4]
        bidDepth = 1 / (abs(bp0 - bp1) * bp0) if bp0 > 1e-4 and bp1 > 1e-4 else 0
        factorValue = askDepth * bidDepth * 1000

        self._addFactorValue(factorValue)