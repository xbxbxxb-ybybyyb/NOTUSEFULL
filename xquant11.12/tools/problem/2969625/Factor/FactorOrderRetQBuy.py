import numpy as np
from System.Factor import Factor


class FactorOrderRetQBuy(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.midP = self._getFactor({"ClassName": "MidPrice"})
        self._addIntermediate("buyQtyList", [])

    def calculate(self):
        buyQtyList = self.getIntermediate("buyQtyList")

        preClose = self._getLastTickData("PreviousClose")
        midPList = np.array([preClose] + self.midP.getFactorValueList())
        rets = midPList[1:] / midPList[:-1] - 1

        buyQty = 0
        order = self._getLastTickData("Orders")
        if order is not None:
            orderBS = self._getOrderData("BSFlag", order)
            orderQty = self._getOrderData("Volume", order)
            orderType = self._getOrderData("OrderType", order)
            for j in range(len(orderBS)):
                if orderType[j] in [2, 10] and orderBS[j] == 1:
                    buyQty += orderQty[j]
        buyQtyList.append(buyQty)

        buyQty = np.array(buyQtyList)
        buyQtyQ = np.mean(buyQty[-1] > buyQty)
        retQ = np.mean(rets[-1] > rets)

        fv = retQ * buyQtyQ

        self._addFactorValue(fv)
