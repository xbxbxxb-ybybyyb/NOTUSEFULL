import numpy as np
from System.Factor import Factor


class FactorPriceToAskMaxM(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("NumList", [])

    def calculate(self):
        askNum = self._getLastTickData("AskNum")
        numList = self.getIntermediate("NumList")
        numList.append(np.nansum(askNum))

        lastPriceList = self._getLastNTickData("LastPrice", self.__lag)
        maxPrice = lastPriceList[np.argmax(numList[-self.__lag:])]

        if maxPrice > 1e-4:
            factorValue = - (lastPriceList[-1] / maxPrice - 1) * 1000
        else:
            lastFactorValue = self.getLastFactorValue()
            if lastFactorValue is not None:
                factorValue = lastFactorValue
            else:
                factorValue = 0.

        self._addFactorValue(factorValue)



