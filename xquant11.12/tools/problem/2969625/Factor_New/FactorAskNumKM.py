from System.Factor import Factor
import numpy as np


class FactorAskNumKM(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__Lag = self._getParameter("Lag")
        self._addIntermediate("AskNumList", [])

    def calculate(self):
        askNumList = self.getIntermediate("AskNumList")
        ordersArray = self._getLastTickData("Orders")

        if ordersArray is not None:
            bsFlag = self._getOrderData("BSFlag", ordersArray)
            askNumList.append(np.sum(bsFlag == 2))
        else:
            askNumList.append(0)

        askNums = askNumList[-self.__Lag:]
        L = len(askNums)

        if L < 5:
            if len(self.getFactorValueList()) == 0:
                factorValue = 0
            else:
                factorValue = self.getLastFactorValue()
        else:
            factorValue = -np.corrcoef(np.arange(len(askNums)), askNums)[0][1]
            if np.isnan(factorValue):
                factorValue = 0

        self._addFactorValue(factorValue)