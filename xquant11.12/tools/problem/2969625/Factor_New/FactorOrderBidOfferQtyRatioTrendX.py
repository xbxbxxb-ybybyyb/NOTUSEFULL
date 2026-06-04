import numpy as np
from System.Factor import Factor


class FactorOrderBidOfferQtyRatioTrendX(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

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
            factorValue = 3.8
        else:
            factorValue = np.corrcoef(orderQtyRatioSlice, np.arange(len(orderQtyRatioSlice)))[0, 1] * 100

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)

