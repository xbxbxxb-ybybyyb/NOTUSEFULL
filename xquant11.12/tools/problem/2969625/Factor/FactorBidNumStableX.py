import numpy as np
from System.Factor import Factor


class FactorBidNumStableX(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__sLag = self._getParameter("sLag")

        self._addIntermediate("BidNumList", [])

    def calculate(self):
        bidNumArray = self._getLastTickData("BidNum")
        bidNum = np.nansum(bidNumArray)
        bidNumList = self.getIntermediate("BidNumList")
        bidNumList.append(bidNum)

        bidNumSlice = np.array(bidNumList[-self.__lag:])
        if len(bidNumSlice) < 5:
            factorValue = 0.
        else:
            bidNumStd = np.nanstd(bidNumSlice)
            if bidNumStd > 1e-6:
                factorValue = (bidNumSlice[-1] - np.nanmean(bidNumSlice[-self.__sLag:])) / bidNumStd * 100
            else:
                lastFactorValue = self.getLastFactorValue()
                if lastFactorValue is not None:
                    factorValue = lastFactorValue
                else:
                    factorValue = 0

        self._addFactorValue(factorValue)



