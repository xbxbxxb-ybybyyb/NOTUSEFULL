import numpy as np
from System.Factor import Factor


class FactorPriceToAskMaxStd(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("RetList", [])

    def calculate(self):
        askNum = self._getLastTickData("AskNum")
        askPrice = self._getLastTickData("AskPrice")
        lastPrice = self._getLastTickData("LastPrice")

        maxPrice = askPrice[np.argmax(askNum)]
        ret = (lastPrice / maxPrice - 1) * 1000 if maxPrice > 1e-6 else 0
        retList = self.getIntermediate("RetList")
        retList.append(ret)
        retSlice = np.array(retList[-self.__lag:])
        factorValue = np.nanstd(retSlice)

        self._addFactorValue(factorValue)



