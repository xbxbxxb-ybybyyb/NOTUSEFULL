import numpy as np
from System.Factor import Factor


class FactorBuyOrderAmtRel(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.lag1 = self._getParameter("Lag1")
        self.lag2 = self._getParameter("Lag2")

        self._addIntermediate("meanBuyOrderAmt", [])

    def calculate(self):
        maxPrice = self._getLastTickData("MaxPrice")
        askPList = self._getLastNTickData("AskPrice", self.lag2)
        askP1List = [p[0] if p[0] > 0 else maxPrice for p in askPList]

        minAskP1Idx = len(askP1List) - np.argmin(askP1List)

        orders = self._getLastNTickData("Orders", max(self.lag1, minAskP1Idx))
        totalBuyOrderAmt = 0
        for order in orders:
            if order is not None:
                orderType = self._getOrderData("OrderType", order)
                orderBS = self._getOrderData("BSFlag", order)
                price = self._getOrderData("Price", order)
                volume = self._getOrderData("Volume", order)
                for i in range(orderType.shape[0]):
                    if orderType[i] == 2 and orderBS[i] == 1:
                        totalBuyOrderAmt += price[i] * volume[i]

        meanBuyOrderAmt = self.getIntermediate("meanBuyOrderAmt")
        meanBuyOrderAmt.append(totalBuyOrderAmt / len(orders))

        fv = self.relative(meanBuyOrderAmt, self.lag1, self.lag2)

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
