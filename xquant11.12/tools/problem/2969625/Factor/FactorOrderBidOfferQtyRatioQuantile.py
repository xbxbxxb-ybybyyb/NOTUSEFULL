import numpy as np
from System.Factor import Factor


class FactorOrderBidOfferQtyRatioQuantile(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__sLag = self._getParameter("SmoothLag")

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
        factorValue = sum(orderQtyRatioSlice < orderQtyRatioSlice[-1]) / len(orderQtyRatioSlice)

        factorValueList = self.getFactorValueList()
        factorValue = self._EMA_calculate(factorValue, factorValueList, self.__sLag)

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])

    @staticmethod
    def __process_last_n_qty(x, lag):
        x_new = np.clip(np.diff(x), a_min=0, a_max=np.inf)
        if len(x_new) < lag:
            x_new = np.hstack((0, x_new))
        return x_new

