import numpy as np
from System.Factor import Factor


class FactorOrderBidNumQuantile(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__sLag = self._getParameter("SmoothLag")

        self._addIntermediate("BidNumList", [])

    def calculate(self):
        bidNumArray = self._getLastTickData("BidNum")
        bidNum = np.nansum(bidNumArray)
        bidNumList = self.getIntermediate("BidNumList")
        bidNumList.append(bidNum)

        bidNumSlice = np.array(bidNumList[-self.__lag:])
        if len(bidNumSlice) == 0:
            factorValue = 0
        else:
            factorValue = sum(bidNumSlice < bidNumSlice[-1]) / len(bidNumSlice)

        factorValueList = self.getFactorValueList()
        factorValue = self._EMA_calculate(factorValue, factorValueList, self.__sLag)

        self._addFactorValue(factorValue)

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])


