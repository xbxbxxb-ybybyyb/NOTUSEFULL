import numpy as np
from System.Factor import Factor


class FactorPankouCrossEntropy(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__size = self._getParameter("Size")
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("PankouList", [])
        self.__priceRange = np.arange(-self.__size, self.__size).astype(int)

    def calculate(self):
        PankouList = self.getIntermediate("PankouList")
        lastPrice = self._getLastNTickData("LastPrice", 2)
        askVolume = self._getLastTickData("AskVolume")
        askPrice = self._getLastTickData("AskPrice")
        bidVolume = self._getLastTickData("BidVolume")
        bidPrice = self._getLastTickData("BidPrice")

        currentPankou = sorted(list(zip(askPrice, askVolume)) + list(zip(bidPrice, bidVolume)))
        PankouList.append(currentPankou)

        if len(lastPrice) > 1:
            priceBins = (np.round(lastPrice[-2] * 100) + self.__priceRange) / 100
            priceBins = priceBins[priceBins > 0]

            lastPankouInfo = self.__getPankouInfo(PankouList[-2], priceBins)
            currentPankouInfo = self.__getPankouInfo(currentPankou, priceBins)

            Q = lastPankouInfo / sum(lastPankouInfo)
            P = currentPankouInfo / sum(currentPankouInfo)

            factorValue = sum(P * np.log(P / Q))

            factorValueList = self.getFactorValueList()
            factorValue = self._EMA_calculate(factorValue, factorValueList, self.__lag)
        else:
            factorValue = 0.

        self._addFactorValue(factorValue)

    def __getPankouInfo(self, pankou, priceBins):
        pankouInfo = np.ones(len(priceBins, ))
        for price, volume in pankou:
            pankouInfo[priceBins == price] = volume
        return pankouInfo

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])
