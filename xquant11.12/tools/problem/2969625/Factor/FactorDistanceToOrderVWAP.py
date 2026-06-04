from System.Factor import Factor
import numpy as np


class FactorDistanceToOrderVWAP(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )
        self._addIntermediate("OrderTotVolume", [])
        self._addIntermediate("OrderTotAmount", [])

    def calculate(self):
        orderTotVolume = self.getIntermediate("OrderTotVolume")
        orderTotAmount = self.getIntermediate("OrderTotAmount")
        ordersArray = self._getLastTickData("Orders")

        if ordersArray is not None:
            prices = self._getOrderData("Price", ordersArray)
            volume = self._getOrderData("Volume", ordersArray)
            orderTotVolume.append(np.nansum(volume))
            orderTotAmount.append(np.nansum(volume*prices))
        else:
            orderTotVolume.append(0)
            orderTotAmount.append(0)

        L = min(len(orderTotVolume), self.__lag)
        if L < 5:
            if len(self.getFactorValueList()) == 0:
                factorValue = 0
            else:
                factorValue = self.getLastFactorValue()
        else:
            if np.sum(orderTotVolume) < 0.1:
                factorValue = 0
            else:
                midPrice = self.__midPrice.getLastFactorValue()
                if (midPrice < 0.1) or (sum(orderTotVolume[-L:]) < 0.1):
                    factorValue = 0
                else:
                    factorValue = (sum(orderTotAmount[-L:])/sum(orderTotVolume[-L:])/midPrice - 1)*1000

        self._addFactorValue(factorValue)

