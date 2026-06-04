from System.Factor import Factor
import numpy as np


class FactorAskOrderKM(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("OrderAskVolume", [])

    def calculate(self):

        orderAskVolume = self.getIntermediate("OrderAskVolume")
        ordersArray = self._getLastTickData("Orders")

        if ordersArray is not None:
            bsFlag = self._getOrderData("BSFlag", ordersArray)
            volume = self._getOrderData("Volume", ordersArray)
            orderAskVolume.append(np.nansum(volume[bsFlag == 2]))
        else:
            orderAskVolume.append(0.)

        L = min(len(orderAskVolume), self.__lag)
        localOrderAskVolume = orderAskVolume[-L:]

        if L < 5:
            if len(self.getFactorValueList()) == 0:
                factorValue = 0
            else:
                factorValue = self.getLastFactorValue()
        else:
            # orderAskVolDif = np.diff(orderAskVolume)
            factorValue = -np.corrcoef(np.arange(len(localOrderAskVolume)), localOrderAskVolume)[0][1]
            if np.isnan(factorValue):
                factorValue = 0

        self._addFactorValue(factorValue)
