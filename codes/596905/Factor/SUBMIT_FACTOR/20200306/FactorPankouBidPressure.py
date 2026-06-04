import numpy as np
from System.Factor import Factor


class FactorPankouBidPressure(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__sliceNum = self._getParameter("SliceNum")
        self.__sliceRatio = [i / 10 for i in range(1, self.__sliceNum + 1)]
        self.__weightRatio = np.array([2 * i - 1 for i in range(self.__sliceNum, 0, -1)])
        self.__weightRatio = self.__weightRatio / np.sum(self.__weightRatio)

    def calculate(self):
        lastPrice = self._getLastNTodayTickData("LastPrice", 1)[-1]
        askVolume = self._getLastNTodayTickData("AskVolume", 1)[-1]
        askPrice = self._getLastNTodayTickData("AskPrice", 1)[-1]
        bidVolume = self._getLastNTodayTickData("BidVolume", 1)[-1]
        bidPrice = self._getLastNTodayTickData("BidPrice", 1)[-1]

        maxVolume = max(np.nansum(askVolume), np.nansum(bidVolume))
        volumeSlice = [maxVolume * i for i in self.__sliceRatio]

        bidEqualPriceList = [lastPrice]
        for i in volumeSlice:
            bidEqualPriceList.append(self.__getEqualPrice(i, bidPrice, bidVolume))

        bidPressure = np.nansum(np.diff(np.log1p(bidEqualPriceList)) * self.__weightRatio) * 1000

        value = bidPressure

        self._addFactorValue(value)

    @staticmethod
    def __getEqualPrice(volume, priceList, volumeList):
        i = 0
        cum_vol = 0
        while i < 10 and cum_vol < volume:
            cum_vol += volumeList[i]
            i += 1
        return priceList[i - 1]
