import numpy as np
from System.Factor import Factor


class FactorDistance2ResSell(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.ResPrice = self._getFactor({"ClassName": "ResPrice"})

    def calculate(self):
        bidP = self._getLastTickData("BidPrice")
        minP = self._getLastTickData("MinPrice")

        bidP0 = bidP[0] if bidP[0] > 1e-6 else minP

        askRes = np.mean([x[0] for x in self.ResPrice.getFactorValueList()[-40:][:5]])

        factorValue = 1 - bidP0 / askRes

        self._addFactorValue(factorValue)
