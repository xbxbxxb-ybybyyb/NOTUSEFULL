import numpy as np
from System.Factor import Factor


class FactorOrderAskPressureQuantile(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__sLag = self._getParameter("SmoothLag")
        self.__sliceNum = self._getParameter("SliceNum")
        self.__sliceRatio = [i / 10 for i in range(1, self.__sliceNum + 1)]
        self.__weightRatio = np.array([2 * i - 1 for i in range(self.__sliceNum, 0, -1)])
        self.__weightRatio = self.__weightRatio / np.sum(self.__weightRatio)

        self._addIntermediate("PressureList", [])

    def calculate(self):
        lastPrice = self._getLastTickData("LastPrice")
        askNum = self._getLastTickData("AskNum")
        bidNum = self._getLastTickData("BidNum")
        askPrice = self._getLastTickData("AskPrice")

        maxNum = max(np.nansum(askNum), np.nansum(bidNum))
        NumSlice = [maxNum * i for i in self.__sliceRatio]

        askEqualPriceList = [lastPrice]
        for i in NumSlice:
            askEqualPriceList.append(self.__getEqualPrice(i, askPrice, askNum))

        askPressure = np.nansum(np.diff(np.log1p(askEqualPriceList)) * self.__weightRatio) * 1000

        pressureList = self.getIntermediate("PressureList")
        pressureList.append(askPressure)

        pressureSlice = np.array(pressureList[-self.__lag:])

        if len(pressureSlice) < 1:
            factorValue = 0.
        else:
            factorValue = sum(pressureSlice < pressureSlice[-1]) / len(pressureSlice)

        factorValueList = self.getFactorValueList()
        factorValue = self._EMA_calculate(factorValue, factorValueList, self.__sLag)

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

    @staticmethod
    def __getEqualPrice(num, priceList, numList):
        i = 0
        cum_num = 0
        while i < len(numList) and cum_num < num:
            cum_num += numList[i]
            i += 1
        return priceList[i - 1]

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])
