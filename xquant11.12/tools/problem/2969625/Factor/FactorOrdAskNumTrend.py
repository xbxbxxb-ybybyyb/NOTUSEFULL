import numpy as np
from System.Factor import Factor


class FactorOrdAskNumTrend(Factor):
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
            askNumList.append(None)

        filterAskNumList = list(filter(lambda x: x is not None, askNumList))
        askNumSlice = np.array(filterAskNumList[-self.__lag:])

        if len(askNumSlice) > 1:
            factorValue = np.corrcoef(askNumSlice, np.arange(len(askNumSlice)))[0, 1]
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)





