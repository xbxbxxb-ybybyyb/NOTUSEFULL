import numpy as np
from System.Factor import Factor


class FactorPankouCrossEntropy(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lastPrice = None
        self.__lastPankou = None
        self.__priceRange = np.arange(-100, 100).astype(int)

    def calculate(self):
        lastPrice = self._getLastNTodayTickData("LastPrice", 1)[-1]
        askVolume = self._getLastNTodayTickData("AskVolume", 1)[-1]
        askPrice = self._getLastNTodayTickData("AskPrice", 1)[-1]
        bidVolume = self._getLastNTodayTickData("BidVolume", 1)[-1]
        bidPrice = self._getLastNTodayTickData("BidPrice", 1)[-1]

        currentPankou = sorted(list(zip(askPrice, askVolume)) + list(zip(bidPrice, bidVolume)))

        if self.__lastPrice is None and self.__lastPankou is None:
            self.__lastPrice = lastPrice
            self.__lastPankou = currentPankou

        priceBins = (np.round(self.__lastPrice * 100) + self.__priceRange) / 100

        lastPankouInfo = self.__getPankouInfo(self.__lastPankou, priceBins)
        currentPankouInfo = self.__getPankouInfo(currentPankou, priceBins)

        self.__lastPrice = lastPrice
        self.__lastPankou = currentPankou

        Q = lastPankouInfo / sum(lastPankouInfo)
        P = currentPankouInfo / sum(currentPankouInfo)

        value = sum(Q * np.log(Q / P))

        self._addFactorValue(value)

    @staticmethod
    def __getPankouInfo(pankou, priceBins):
        pankouInfo = np.ones((200,))
        for price, volume in pankou:
            pankouInfo[priceBins == price] = volume
        return pankouInfo
