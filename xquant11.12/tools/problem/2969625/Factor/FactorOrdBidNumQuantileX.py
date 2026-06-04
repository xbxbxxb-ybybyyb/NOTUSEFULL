import numpy as np
from System.Factor import Factor


class FactorOrdBidNumQuantileX(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__window = self._getParameter("Window")

        self._addIntermediate("BidNumList", [])

    def calculate(self):
        bidNumList = self.getIntermediate("BidNumList")

        orderData = self._getLastTickData("Orders")
        if orderData is not None:
            bsFlag = self._getOrderData("BSFlag", orderData)
            bidNumList.append((bsFlag == 1).sum())
        else:
            bidNumList.append(0)
            
        bidNumSlice = np.array(bidNumList[-self.__lag:])

        if len(bidNumSlice) < 5:
            quantile = 0
        else:
            quantile = np.sum(bidNumSlice < bidNumSlice[-1]) / len(bidNumSlice) - 0.5

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



