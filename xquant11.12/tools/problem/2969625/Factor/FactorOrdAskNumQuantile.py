import numpy as np
from System.Factor import Factor


class FactorOrdAskNumQuantile(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__window = self._getParameter("Window")

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
            quantile = sum(askNumSlice < askNumSlice[-1]) / len(askNumSlice)
        else:
            quantile = 0.

        factorValueList = self.getFactorValueList()
        factorValue = self._EMA_calculate(quantile, factorValueList, self.__window)

        self._addFactorValue(factorValue)

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])



