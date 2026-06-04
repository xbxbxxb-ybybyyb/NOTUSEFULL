import numpy as np
from System.Factor import Factor

class FactorPriceWeightedVolumeRatio_30(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__bias = self._getParameter("Bias")

    def calculate(self):
        askPrice = self._getLastTickData("AskPrice")[:5]
        bidPrice = self._getLastTickData("BidPrice")[:5]
        askPrice_norm = (askPrice - askPrice[-1]) / (askPrice[0] - askPrice[-1]) if abs(askPrice[0] - askPrice[-1]) > 0.01 else 0
        bidPrice_norm = (bidPrice - bidPrice[-1]) / (bidPrice[0] - bidPrice[-1]) if abs(bidPrice[0] - bidPrice[-1]) > 0.01 else 0
        askVolume = self._getLastTickData("AskVolume")[:5]
        bidVolume = self._getLastTickData("BidVolume")[:5]
        askVolume_weighted = np.sum(askVolume * askPrice_norm)
        bidVolume_weighted = np.sum(bidVolume * bidPrice_norm)
        if askVolume_weighted == 0:
            volumeRatio = 1
        elif bidVolume_weighted == 0:
            volumeRatio = 0
        else:
            volumeRatio = bidVolume_weighted / (askVolume_weighted + bidVolume_weighted)

        ceiling = self._getLastTickData("HighPrice")
        floor = self._getLastTickData("LowPrice")
        lastPrice = self._getLastTickData("LastPrice")
        priceRatio = (lastPrice - floor) / (ceiling - floor) if (ceiling - floor) > 0.01 else 0

        factorValue = - priceRatio * (1 - self.__bias) + volumeRatio * self.__bias

        self._addFactorValue(factorValue)