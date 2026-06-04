
import numpy as np
from System.Factor import Factor


class FactorOrdAskOrderVolumeTrendM(Factor):
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
            orderList.append(volume[bsFlag == 2].sum())
        else:
            orderList.append(0.)

        orderSlice = np.array(orderList[-self.__lag:])

        if len(orderSlice) < 5:
            factorValue = 
        else:
            factorValue = - np.corrcoef(orderSlice, np.arange(len(orderSlice)))[0, 1] * 100

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)






