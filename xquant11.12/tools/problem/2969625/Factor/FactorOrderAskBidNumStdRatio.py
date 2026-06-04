import numpy as np
from System.Factor import Factor


class FactorOrderAskBidNumStdRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("BidNumList", [])
        self._addIntermediate("AskNumList", [])

    def calculate(self):
        askNum = self._getLastTickData("AskNum")
        bidNum = self._getLastTickData("BidNum")
        bidNumList = self.getIntermediate("BidNumList")
        askNumList = self.getIntermediate("AskNumList")

        bidNumList.append(np.nansum(bidNum))
        askNumList.append(np.nansum(askNum))

        bidNumSlice = np.array(bidNumList[-self.__lag:])
        askNumSlice = np.array(askNumList[-self.__lag:])
        if len(bidNumSlice) <= 1:
            factorValue = 0.
        else:
            factorValue = np.nanstd(bidNumSlice) / np.nanstd(askNumSlice) if np.nanstd(askNumSlice) > 1e-6 else 0.
        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)



