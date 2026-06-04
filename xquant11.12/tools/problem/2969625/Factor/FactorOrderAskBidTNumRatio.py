from System.Factor import Factor
import numpy as np


class FactorOrderAskBidTNumRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

    def calculate(self):
        askNumArray = self._getLastTickData("AskNum")
        bidNumArray = self._getLastTickData("BidNum")
        askNum = np.nansum(askNumArray)
        bidNum = np.nansum(bidNumArray)
        factorValue = askNum / bidNum if bidNum > 1e-6 else 0.

        self._addFactorValue(factorValue)



