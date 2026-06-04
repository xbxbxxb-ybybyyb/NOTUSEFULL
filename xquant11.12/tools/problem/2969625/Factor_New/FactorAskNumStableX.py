import numpy as np
from System.Factor import Factor


class FactorAskNumStableX(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__sLag = self._getParameter("sLag")

        self._addIntermediate("AskNumList", [])

    def calculate(self):
        askNumList = self.getIntermediate("AskNumList")
        askNumArray = self._getLastTickData("AskNum")
        askNum = np.nansum(askNumArray)
        askNumList.append(askNum)

        askNumSlice = np.array(askNumList[-self.__lag:])
        if len(askNumSlice) < 5:
            factorValue = 0.
        else:
            askNumStd = np.nanstd(askNumSlice)
            if askNumStd > 1e-6:
                factorValue = - (askNumSlice[-1] - np.nanmean(askNumSlice[-self.__sLag:])) / askNumStd * 100
            else:
                lastFactorValue = self.getLastFactorValue()
                if lastFactorValue is not None:
                    factorValue = lastFactorValue
                else:
                    factorValue = 0.

        self._addFactorValue(factorValue)



