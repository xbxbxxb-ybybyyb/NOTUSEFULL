import numpy as np
from System.Factor import Factor


class FactorAskNumStable(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__sLag = self._getParameter("ShortLag")

        self._addIntermediate("AskNumList", [])

    def calculate(self):
        askNumArray = self._getLastTickData("AskNum")
        askNum = np.nansum(askNumArray)
        askNumList = self.getIntermediate("AskNumList")
        askNumList.append(askNum)

        askNumSlice = np.array(askNumList[-self.__lag:])
        askNumStd = np.nanstd(askNumSlice)
        if askNumStd > 1e-6:
            factorValue = (askNumSlice[-1] - np.nanmean(askNumSlice[-self.__sLag:])) / askNumStd
        else:
            factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)



