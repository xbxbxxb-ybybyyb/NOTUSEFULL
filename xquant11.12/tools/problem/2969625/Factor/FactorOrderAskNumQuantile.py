import numpy as np
from System.Factor import Factor


class FactorOrderAskNumQuantile(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__sLag = self._getParameter("SmoothLag")

        self._addIntermediate("AskNumList", [])

    def calculate(self):
        askNumArray = self._getLastTickData("AskNum")
        askNum = np.nansum(askNumArray)
        askNumList = self.getIntermediate("AskNumList")
        askNumList.append(askNum)

        askNumSlice = np.array(askNumList[-self.__lag:])
        if len(askNumSlice) == 0:
            factorValue = 0
        else:
            factorValue = sum(askNumSlice < askNumSlice[-1]) / len(askNumSlice)

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



