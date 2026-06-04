import numpy as np
from System.Factor import Factor


class FactorBidNumStable(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__sLag = self._getParameter("ShortLag")

        self._addIntermediate("BidNumList", [])

    def calculate(self):
        bidNumArray = self._getLastTickData("BidNum")
        bidNum = np.nansum(bidNumArray)
        bidNumList = self.getIntermediate("BidNumList")
        bidNumList.append(bidNum)

        bidNumSlice = np.array(bidNumList[-self.__lag:])
        bidNumStd = np.nanstd(bidNumSlice)
        if bidNumStd > 1e-6:
            factorValue = (bidNumSlice[-1] - np.nanmean(bidNumSlice[-self.__sLag:])) / bidNumStd
        else:
            factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)



