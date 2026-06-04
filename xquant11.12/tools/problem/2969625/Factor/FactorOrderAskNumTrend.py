import numpy as np
from System.Factor import Factor


class FactorOrderAskNumTrend(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("AskNumList", [])

    def calculate(self):
        askNumArray = self._getLastTickData("AskNum")
        askNum = np.nansum(askNumArray)
        askNumList = self.getIntermediate("AskNumList")
        askNumList.append(askNum)

        askNumSlice = np.array(askNumList[-self.__lag:])
        if len(askNumSlice) > 1:
            factorValue = np.corrcoef(askNumSlice, np.arange(len(askNumSlice)))[0, 1]
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)



