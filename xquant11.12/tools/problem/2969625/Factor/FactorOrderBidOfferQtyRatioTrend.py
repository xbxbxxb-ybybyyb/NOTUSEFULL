import numpy as np
from System.Factor import Factor


class FactorOrderBidOfferQtyRatioTrend(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("OrderQtyRatioList", [])

    def calculate(self):
        bidQty = self._getLastNTickData("BidQty", 2)
        bidQty = self.__process_last_n_qty(bidQty, 1)[-1]
        offerQty = self._getLastNTickData("OfferQty", 2)
        offerQty = self.__process_last_n_qty(offerQty, 1)[-1]

        if offerQty > 0:
            qtyRatio = bidQty / offerQty
        else:
            qtyRatio = 1.

        orderQtyRatioList = self.getIntermediate("OrderQtyRatioList")
        orderQtyRatioList.append(qtyRatio)

        orderQtyRatioSlice = np.array(orderQtyRatioList[-self.__lag:])
        if len(orderQtyRatioSlice) > 1:
            factorValue = np.corrcoef(orderQtyRatioSlice, np.arange(len(orderQtyRatioSlice)))[0, 1]
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)

    @staticmethod
    def __process_last_n_qty(x, lag):
        x_new = np.clip(np.diff(x), a_min=0, a_max=np.inf)
        if len(x_new) < lag:
            x_new = np.hstack((0, x_new))
        return x_new

