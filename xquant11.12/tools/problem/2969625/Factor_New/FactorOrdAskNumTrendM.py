
import numpy as np
from System.Factor import Factor


class FactorOrdAskNumTrendM(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("AskNumList", [])

    def calculate(self):
        askNumList = self.getIntermediate("AskNumList")

        orderData = self._getLastTickData("Orders")
        if orderData is not None:
            bsFlag = self._getOrderData("BSFlag", orderData)
            askNumList.append((bsFlag == 2).sum())
        else:
            askNumList.append(0)

        askNumSlice = np.array(askNumList[-self.__lag:])

        if len(askNumSlice) < 5:
            factorValue = 0.
        else:
            factorValue = - np.corrcoef(askNumSlice, np.arange(len(askNumSlice)))[0, 1] * 100

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)





