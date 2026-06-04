import numpy as np
from System.Factor import Factor


class FactorPankouBidPressure(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__sliceNum = self._getParameter("SliceNum")
        self.__weightRatio = np.array([2 * i - 1 for i in range(self.__sliceNum, 0, -1)])
        self.__weightRatio = self.__weightRatio / np.sum(self.__weightRatio)

    def calculate(self):
        lastPrice = self._getLastTickData("LastPrice")
        askVolume = self._getLastTickData("AskVolume")
        bidVolume = self._getLastTickData("BidVolume")
        bidPrice = self._getLastTickData("BidPrice")

        sliceRatio = [i / len(askVolume) for i in range(1, self.__sliceNum + 1)]
        maxVolume = max(np.nansum(askVolume), np.nansum(bidVolume))
        volumeSlice = [maxVolume * i for i in sliceRatio]

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
        while i < len(volumeList) and cum_vol < volume:
            cum_vol += volumeList[i]
            i += 1
        return priceList[i - 1]
