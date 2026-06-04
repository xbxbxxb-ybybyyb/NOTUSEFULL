import numpy as np
from System.Factor import Factor


class FactorOrdAskBidNetAggressiveRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__netAggressive = self._getFactor(
            {
                "ClassName": "OrdAskBidNetAggressive"
            }
        )
        self._addIntermediate("OrderVolumeList", [])

    def calculate(self):
        netAggressiveList = self.__netAggressive.getFactorValueList()
        orderVolumeList = self.getIntermediate("OrderVolumeList")

        orderData = self._getLastTickData("Orders")
        orderVolume = np.nansum(self._getOrderData("Volume", orderData)) if orderData is not None else 0
        orderVolumeList.append(orderVolume)

        netAggressiveMean = np.nanmean(netAggressiveList[-self.__lag:])
        orderVolumeMean = np.nanmean(orderVolumeList[-self.__lag:])

        factorValue = netAggressiveMean / orderVolumeMean if orderVolumeMean > 1e-6 else 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)






