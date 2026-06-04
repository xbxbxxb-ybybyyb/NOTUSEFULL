import numpy as np
from System.Factor import Factor


class FactorPankouPressureTrend(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__sliceNum = self._getParameter("SliceNum")
        self.__weightRatio = np.array([2 * i - 1 for i in range(self.__sliceNum, 0, -1)])
        self.__weightRatio = self.__weightRatio / np.sum(self.__weightRatio)

        self._addIntermediate("PanKouPressureList", [])

    def calculate(self):
        lastPrice = self._getLastTickData("LastPrice")
        askVolume = self._getLastTickData("AskVolume")
        askPrice = self._getLastTickData("AskPrice")
        bidVolume = self._getLastTickData("BidVolume")
        bidPrice = self._getLastTickData("BidPrice")

        sliceRatio = [i / 10 for i in range(1, self.__sliceNum + 1)]
        maxVolume = max(np.nansum(askVolume), np.nansum(bidVolume))
        volumeSlice = [maxVolume * i for i in sliceRatio]

        askEqualPriceList = [lastPrice]
        bidEqualPriceList = [lastPrice]
        for i in volumeSlice:
            askEqualPriceList.append(self.__getEqualPrice(i, askPrice, askVolume))
            bidEqualPriceList.append(self.__getEqualPrice(i, bidPrice, bidVolume))

        askPressure = np.nansum(np.diff(np.log1p(askEqualPriceList)) * self.__weightRatio) * 1000
        bidPressure = np.nansum(np.diff(np.log1p(bidEqualPriceList)) * self.__weightRatio) * 1000

        pankouPressureList = self.getIntermediate("PanKouPressureList")
        pankouPressureList.append(askPressure + bidPressure)

        pankouPressureSlice = np.array(pankouPressureList[-self.__lag:])
        if len(pankouPressureSlice) > 1:
            factorValue = np.corrcoef(pankouPressureSlice, np.arange(len(pankouPressureSlice)))[0, 1] * 100
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)

    @staticmethod
    def __getEqualPrice(volume, priceList, volumeList):
        i = 0
        cum_vol = 0
        while i < len(volumeList) and cum_vol < volume:
            cum_vol += volumeList[i]
            i += 1
        return priceList[i - 1]
