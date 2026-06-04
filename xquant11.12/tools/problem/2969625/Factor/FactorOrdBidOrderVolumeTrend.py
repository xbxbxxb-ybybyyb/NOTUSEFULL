import numpy as np
from System.Factor import Factor


class FactorOrdBidOrderVolumeTrend(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("OrderList", [])

    def calculate(self):
        orderList = self.getIntermediate("OrderList")
        orderData = self._getLastTickData("Orders")
        if orderData is not None:
            bsFlag = self._getOrderData("BSFlag", orderData)
            volume = self._getOrderData("Volume", orderData)
            orderList.append(volume[bsFlag == 1].sum())
        else:
            orderList.append(None)

        filterOrderList = list(filter(lambda x: x is not None, orderList))

        orderSlice = np.array(filterOrderList[-self.__lag:])

        if len(orderSlice) > 1:
            factorValue = np.corrcoef(orderSlice, np.arange(len(orderSlice)))[0, 1]
        else:
            factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)






