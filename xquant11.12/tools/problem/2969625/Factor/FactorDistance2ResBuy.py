import numpy as np
from System.Factor import Factor


class FactorDistance2ResBuy(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.ResPrice = self._getFactor({"ClassName": "ResPrice"})

    def calculate(self):
        askP = self._getLastTickData("AskPrice")
        maxP = self._getLastTickData("MaxPrice")

        askP0 = askP[0] if askP[0] > 1e-6 else maxP

        bidRes = np.mean([x[1] for x in self.ResPrice.getFactorValueList()[-40:][:5]])

        factorValue = 1 - askP0 / bidRes

        self._addFactorValue(factorValue)
