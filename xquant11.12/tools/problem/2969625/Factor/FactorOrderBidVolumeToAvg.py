from System.Factor import Factor
import numpy as np


class FactorOrderBidVolumeToAvg(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self._addIntermediate("OrdersBidVolume", [])

    def calculate(self):
        ordersArray = self._getLastTickData("Orders")
        ordersBidVolumeList = self.getIntermediate("OrdersBidVolume")

        if ordersArray is not None:
            bsFlag = self._getOrderData("BSFlag", ordersArray)
            volume = self._getOrderData("Volume", ordersArray)
            bidVolume = np.nansum(volume[bsFlag == 1])
        else:
            bidVolume = 0
        ordersBidVolumeList.append(bidVolume)

        L = min(len(ordersBidVolumeList), self.__lag)
        if L < 5:
            if len(self.getFactorValueList()) == 0:
                factorValue = 0
            else:
                factorValue = self.getLastFactorValue()
        else:
            meanBidVolume = np.mean(np.array(ordersBidVolumeList[-L:]))
            if meanBidVolume < 0.1:
                factorValue = 0
            else:
                factorValue = bidVolume / meanBidVolume - 1

        self._addFactorValue(factorValue)


