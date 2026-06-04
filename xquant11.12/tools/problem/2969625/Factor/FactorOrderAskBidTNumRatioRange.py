from System.Factor import Factor
import numpy as np


class FactorOrderAskBidTNumRatioRange(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("NumRatioList", [])

    def calculate(self):
        askNumArray = self._getLastTickData("AskNum")
        bidNumArray = self._getLastTickData("BidNum")
        askNum = np.nansum(askNumArray)
        bidNum = np.nansum(bidNumArray)
        numRatio = askNum / bidNum if bidNum > 1e-4 else 0
        numRatioList = self.getIntermediate("NumRatioList")
        numRatioList.append(numRatio)

        numRatioSlice = np.array(numRatioList[-self.__lag:])
        factorValue = np.nanmax(numRatioSlice) - np.nanmin(numRatioSlice)

        self._addFactorValue(factorValue)



