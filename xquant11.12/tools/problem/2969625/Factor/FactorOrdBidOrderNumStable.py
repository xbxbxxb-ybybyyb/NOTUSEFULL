import numpy as np
from System.Factor import Factor


class FactorOrdBidOrderNumStable(Factor):
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
            orderList.append((bsFlag == 1).sum())
        else:
            orderList.append(None)

        filterOrderList = list(filter(lambda x: x is not None, orderList))

        orderSlice = np.array(filterOrderList[-self.__lag:])

        orderStd = np.nanstd(orderSlice)
        if orderStd > 1e-6:
            factorValue = (orderSlice[-1] - np.nanmean(orderSlice[-self.__sLag:])) / orderStd
        else:
            factorValue = 0

        self._addFactorValue(factorValue)







