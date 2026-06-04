import numpy as np
from System.Factor import Factor


class FactorOrdBidNumTrend(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("BidNumList", [])

    def calculate(self):
        bidNumList = self.getIntermediate("BidNumList")

        orderData = self._getLastTickData("Orders")
        if orderData is not None:
            bsFlag = self._getOrderData("BSFlag", orderData)
            bidNumList.append((bsFlag == 1).sum())
        else:
            bidNumList.append(None)

        filterBidNumList = list(filter(lambda x: x is not None, bidNumList))
        bidNumSlice = np.array(filterBidNumList[-self.__lag:])

        if len(bidNumSlice) > 1:
            factorValue = np.corrcoef(bidNumSlice, np.arange(len(bidNumSlice)))[0, 1]
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)





