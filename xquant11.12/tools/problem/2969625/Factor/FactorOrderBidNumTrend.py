import numpy as np
from System.Factor import Factor


class FactorOrderBidNumTrend(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("BidNumList", [])

    def calculate(self):
        bidNumArray = self._getLastTickData("BidNum")
        bidNum = np.nansum(bidNumArray)
        bidNumList = self.getIntermediate("BidNumList")
        bidNumList.append(bidNum)

        bidNumSlice = np.array(bidNumList[-self.__lag:])
        if len(bidNumSlice) > 1:
            factorValue = np.corrcoef(bidNumSlice, np.arange(len(bidNumSlice)))[0, 1]
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)



