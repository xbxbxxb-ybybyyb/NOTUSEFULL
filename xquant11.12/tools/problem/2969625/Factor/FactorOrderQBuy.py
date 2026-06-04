import numpy as np
from System.Factor import Factor


class FactorOrderQBuy(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.midP = self._getFactor({"ClassName": "MidPrice"})
        self.lag = self._getParameter("Lag")
        self._addIntermediate("buyQtyList", [])

    def calculate(self):
        preClose = self._getLastTickData("PreviousClose")
        midPList = np.array([preClose] + self.midP.getFactorValueList())
        rets = midPList[1:] / midPList[:-1] - 1

        buyQtyList = self.getIntermediate("buyQtyList")

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

        buyQtyList = np.array(buyQtyList)

        retPerQ = rets / buyQtyList
        retPerQ[np.isinf(retPerQ)] = np.nan
        retPerQ = retPerQ[-self.lag:]
        retPerQ = retPerQ[retPerQ >= 0]
        fv = np.nanmean(retPerQ) * buyQtyList[-1] * 10000
        if np.isnan(fv):
            fv = 0

        self._addFactorValue(fv)
