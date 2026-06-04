import numpy as np
from System.Factor import Factor


class FactorOrderAskNumToNumTrades(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

    def calculate(self):
        askNumArray = self._getLastTickData("AskNum")
        askNum = np.nansum(askNumArray)
        numTrades = self._getLastTickData("NumTrades")
        factorValue = numTrades / askNum if askNum > 1e-6 else 0.

        self._addFactorValue(factorValue)



