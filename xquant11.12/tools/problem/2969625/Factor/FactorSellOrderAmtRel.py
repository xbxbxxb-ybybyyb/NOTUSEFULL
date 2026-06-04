import numpy as np
from System.Factor import Factor


class FactorSellOrderAmtRel(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.lag1 = self._getParameter("Lag1")
        self.lag2 = self._getParameter("Lag2")

        self._addIntermediate("meanSellOrderAmt", [])

    def calculate(self):
        minPrice = self._getLastTickData("MinPrice")
        bidPList = self._getLastNTickData("BidPrice", self.lag2)
        bidP1List = [p[0] if p[0] > 0 else minPrice for p in bidPList]

        maxBidP1Idx = len(bidP1List) - np.argmax(bidP1List)

        orders = self._getLastNTickData("Orders", max(self.lag1, maxBidP1Idx))
        totalSellOrderAmt = 0
        for order in orders:
            if order is not None:
                orderType = self._getOrderData("OrderType", order)
                orderBS = self._getOrderData("BSFlag", order)
                price = self._getOrderData("Price", order)
                volume = self._getOrderData("Volume", order)
                for i in range(orderType.shape[0]):
                    if orderType[i] == 2 and orderBS[i] == 2:
                        totalSellOrderAmt += price[i] * volume[i]

        meanSellOrderAmt = self.getIntermediate("meanSellOrderAmt")
        meanSellOrderAmt.append(totalSellOrderAmt / len(orders))

        fv = self.relative(meanSellOrderAmt, self.lag1, self.lag2)

        self._addFactorValue(fv)

    @staticmethod
    def relative(l, w1, w2):
        length = len(l)
        ratio = w1 / w2
        w1 = min(max(1, int(length * ratio)), w1)

        mean2 = np.nanmean(l[-w2:])

        if mean2 == 0 or np.isnan(mean2):
            return 0
        else:
            return np.nanmean(l[-w1:]) / mean2
