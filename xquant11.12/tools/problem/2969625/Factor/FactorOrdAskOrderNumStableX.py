import numpy as np
from System.Factor import Factor


class FactorOrdAskOrderNumStableX(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__sLag = self._getParameter("ShortLag")

        self._addIntermediate("OrderList", [])

    def calculate(self):
        orderList = self.getIntermediate("OrderList")
        orderData = self._getLastTickData("Orders")
        if orderData is not None:
            bsFlag = self._getOrderData("BSFlag", orderData)
            orderList.append((bsFlag == 2).sum())
        else:
            orderList.append(0)

        orderSlice = np.array(orderList[-self.__lag:])
        if len(orderSlice) < 5:
            factorValue = 0.
        else:
            orderStd = np.nanstd(orderSlice)
            if orderStd > 1e-4:
                factorValue =  - (orderSlice[-1] - np.nanmean(orderSlice[-self.__sLag:])) / orderStd * 100
            else:
                lastFactorValue = self.getLastFactorValue()
                if lastFactorValue is not None:
                    factorValue = lastFactorValue
                else:
                    factorValue = 0.

        self._addFactorValue(factorValue)








