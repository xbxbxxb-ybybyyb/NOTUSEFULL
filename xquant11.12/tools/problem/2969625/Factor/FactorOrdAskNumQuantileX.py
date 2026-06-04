import numpy as np
from System.Factor import Factor


class FactorOrdAskNumQuantileX(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")
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

        askNumSlice = np.array(askNumList[-self.__window:])

        if len(askNumSlice) < 5:
            quantile = 0
        else:
            quantile = - np.sum(askNumSlice < askNumSlice[-1]) / len(askNumSlice) + 0.5

        factorValueList = self.getFactorValueList()
        factorValue = self._EMA_calculate(quantile, factorValueList, self.__lag)

        self._addFactorValue(factorValue)

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])



