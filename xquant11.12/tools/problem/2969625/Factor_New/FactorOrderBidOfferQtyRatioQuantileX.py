import numpy as np
from System.Factor import Factor


class FactorOrderBidOfferQtyRatioQuantileX(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__sLag = self._getParameter("sLag")

        self._addIntermediate("OrderQtyRatioList", [])

    def calculate(self):
        bidQty = self._getLastTickData("BidQty")
        offerQty = self._getLastTickData("OfferQty")
        totalQty = bidQty + offerQty
        if totalQty > 1e-4:
            qtyRatio = bidQty / totalQty - 0.5
        else:
            qtyRatio = 0.

        orderQtyRatioList = self.getIntermediate("OrderQtyRatioList")
        orderQtyRatioList.append(qtyRatio)

        orderQtyRatioSlice = np.array(orderQtyRatioList[-self.__lag:])
        if len(orderQtyRatioSlice) < 5:
            factorValue = 0.
        else:
            factorValue = np.sum(orderQtyRatioSlice < orderQtyRatioSlice[-1]) / len(orderQtyRatioSlice) - 0.5

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

