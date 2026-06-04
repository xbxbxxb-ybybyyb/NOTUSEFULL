import numpy as np
from System.Factor import Factor


class FactorOrderAskPressureX(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__sliceNum = self._getParameter("SliceNum")
        self.__sliceRatio = [i / 10 for i in range(1, self.__sliceNum + 1)]
        self.__weightRatio = np.array([2 * i - 1 for i in range(self.__sliceNum, 0, -1)])
        self.__weightRatio = self.__weightRatio / np.sum(self.__weightRatio)

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

        factorValue = np.nansum(np.diff(np.log1p(askEqualPriceList)) * self.__weightRatio) * 1000

        self._addFactorValue(factorValue)

    @staticmethod
    def __getEqualPrice(num, priceList, numList):
        i = 0
        cum_num = 0
        while i < len(numList) and cum_num < num:
            cum_num += numList[i]
            i += 1
        return priceList[i - 1]
