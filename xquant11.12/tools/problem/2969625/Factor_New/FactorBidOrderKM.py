from System.Factor import Factor
import numpy as np


class FactorBidOrderKM(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self._addIntermediate("OrderBidVolume", [])

    def calculate(self):
        orderBidVolume = self.getIntermediate("OrderBidVolume")
        ordersArray = self._getLastTickData("Orders")

        if ordersArray is not None:
            bsFlag = self._getOrderData("BSFlag", ordersArray)
            volume = self._getOrderData("Volume", ordersArray)
            orderBidVolume.append(np.nansum(volume[bsFlag == 1]))
        else:
            orderBidVolume.append(0)

        L = min(len(orderBidVolume), self.__lag)
        localOrderBidVolume = orderBidVolume[-L:]

        if L < 5:
            if len(self.getFactorValueList()) == 0:
                factorValue = 0
            else:
                factorValue = self.getLastFactorValue()
        else:
            factorValue = np.corrcoef(np.arange(len(localOrderBidVolume)), localOrderBidVolume)[0][1]
            if np.isnan(factorValue):
                factorValue = 0

        self._addFactorValue(factorValue)

