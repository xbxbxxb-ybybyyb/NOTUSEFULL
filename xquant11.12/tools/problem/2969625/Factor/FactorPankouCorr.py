import numpy as np
from System.Factor import Factor


class FactorPankouCorr(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):
        askVolume = self._getLastTickData("AskVolume")
        askPrice = self._getLastTickData("AskPrice")
        bidVolume = self._getLastTickData("BidVolume")
        bidPrice = self._getLastTickData("BidPrice")

        bidCorr = np.corrcoef(bidVolume, bidPrice)[0, 1]
        askCorr = np.corrcoef(askVolume, askPrice)[0, 1]
        if np.isnan(bidCorr) and np.isnan(askCorr):
            factorValue = 0.
        elif np.isnan(bidCorr):
            factorValue = - askCorr
        elif np.isnan(askCorr):
            factorValue = bidCorr
        else:
            factorValue = bidCorr - askCorr

        factorValueList = self.getFactorValueList()
        factorValue = self._EMA_calculate(factorValue, factorValueList, self.__lag)

        self._addFactorValue(factorValue)

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])

