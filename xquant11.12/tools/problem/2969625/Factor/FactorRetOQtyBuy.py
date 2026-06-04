import numpy as np
from System.Factor import Factor


class FactorRetOQtyBuy(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.midP = self._getFactor({"ClassName": "MidPrice"})
        self.lag1 = self._getParameter("Lag1")
        self.lag2 = self._getParameter("Lag2")
        self._addIntermediate("buyQtyList", [])

    def calculate(self):
        midPList = self.midP.getFactorValueList()
        idxMin = np.argmin(midPList[-self.lag2:])
        idxMax = np.argmax(midPList[-self.lag2:])

        if idxMin < idxMax:
            ret = midPList[-self.lag2:][idxMax] / midPList[-self.lag2:][idxMin] - 1
        else:
            ret = midPList[-self.lag2:][idxMin] / midPList[-self.lag2:][idxMax] - 1

        buyQtyList = self.getIntermediate("buyQtyList")

        buyOrder = 0
        order = self._getLastTickData("Orders")
        if order is not None:
            orderBS = self._getOrderData("BSFlag", order)
            orderQty = self._getOrderData("Volume", order)
            orderType = self._getOrderData("OrderType", order)
            for j in range(len(orderBS)):
                if orderType[j] in [2, 10] and orderBS[j] == 1:
                    buyOrder += orderQty[j]
        buyQtyList.append(buyOrder)
        buyOrderRel = self.relative(buyQtyList, self.lag1, self.lag2)

        fv = buyOrderRel * ret * 100
        if np.isnan(fv):
            fv = 0

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
