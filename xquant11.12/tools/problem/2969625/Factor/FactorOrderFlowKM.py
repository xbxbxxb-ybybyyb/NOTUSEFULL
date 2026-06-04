from System.Factor import Factor
import numpy as np


class FactorOrderFlowKM(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("OrderAskVolume", [])
        self._addIntermediate("OrderBidVolume", [])

    def calculate(self):
        orderAskVolume = self.getIntermediate("OrderAskVolume")
        orderBidVolume = self.getIntermediate("OrderBidVolume")
        ordersArray = self._getLastTickData("Orders")

        if ordersArray is not None:
            bsFlag = self._getOrderData("BSFlag", ordersArray)
            volume = self._getOrderData("Volume", ordersArray)
            orderAskVolume.append(np.nansum(volume[bsFlag == 2]))
            orderBidVolume.append(np.nansum(volume[bsFlag == 1]))
        else:
            orderAskVolume.append(0)
            orderBidVolume.append(0)

        L = min(len(orderAskVolume), self.__lag)

        if L < 5:
            if len(self.getFactorValueList()) == 0:
                factorValue = 0
            else:
                factorValue = self.getLastFactorValue()
        else:
            orderAVArray = np.array(orderAskVolume[-L:])
            orderBVArray = np.array(orderBidVolume[-L:])
            orderFlowArray = orderBVArray - orderAVArray
            # orderFlowDif = np.diff(orderFlowArray)
            factorValue = np.corrcoef(np.arange(len(orderFlowArray)), orderFlowArray)[0][1]
            if np.isnan(factorValue):
                factorValue = 0

        self._addFactorValue(factorValue)
