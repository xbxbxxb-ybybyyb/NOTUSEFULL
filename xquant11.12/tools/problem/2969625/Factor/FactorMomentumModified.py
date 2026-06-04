import math
import numpy as np
from System.Factor import Factor


class FactorMomentumModified(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.__EMAMidPriceLag = self._getParameter("EMAMidPriceLag")
        self.__MAAmountLag = self._getParameter("MAAmountLag")
        self.__lag = self._getParameter("Lag")
        self.__eps = 1e-5

        self.__emaMidPrice = self._getFactor(
            {
                "ClassName": "EMA",
                "Parameters": {
                    "Lag": self.__EMAMidPriceLag,
                    "OriginalData": {
                        "ClassName": "MidPrice"
                    }
                }
            }
        )

    def calculate(self):
        emaPriceList = self.__emaMidPrice.getFactorValueList()
        historyAmountArray = self._getAllTickData("Amount")
        length = min(len(emaPriceList), self.__lag)

        isNotValid = (bool(sum([price < 0.01 for price in emaPriceList[-length:]]))
                      or (historyAmountArray[-length:] < 0).any())

        if isNotValid:
            factorValue = 0
        else:
            lastFactorSpeed = (emaPriceList[-1] / emaPriceList[-length] - 1) / (length / 20)
            amount = math.log((np.nansum(historyAmountArray[-length:]) + self.__eps)
                              / (np.nansum(historyAmountArray[-self.__MAAmountLag:]) + self.__eps))
            factorValue = lastFactorSpeed * amount

        self._addFactorValue(factorValue)
