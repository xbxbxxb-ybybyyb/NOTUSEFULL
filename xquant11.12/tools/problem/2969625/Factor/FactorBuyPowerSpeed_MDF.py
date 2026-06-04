import math
import numpy as np
from System.Factor import Factor


class FactorBuyPowerSpeed_MDF(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__MAAmountLag = self._getParameter("MAAmountLag")
        self.__orderPressureLag = self._getParameter("OrderPressureLag")
        self.__eps = 1e-5

        self.__emaOrderPressure = self._getFactor(
            {
                "ClassName": "EMA",
                "Parameters": {
                    "Lag": self.__orderPressureLag,
                    "OriginalData": {
                        "ClassName": "OrderEvaluate2"
                    }
                }
            }
        )

    def calculate(self):
        accBidAmount = self.__emaOrderPressure.getLastFactorValue()[0]
        MAAmount = np.nanmean(self._getLastNTickData("Amount", self.__MAAmountLag))

        ceiling = self._getLastTickData("HighPrice")
        floor = self._getLastTickData("LowPrice")
        lastPrice = self._getLastTickData("LastPrice")
        price_ratio = (lastPrice - floor) / (ceiling - floor) if (ceiling - floor) > 0.01 else 0

        if accBidAmount < 1e-6 or MAAmount < 1e-6:
            factorValue = 0
        else:
            factorValue =  - price_ratio * math.log(accBidAmount / MAAmount + self.__eps)

        self._addFactorValue(factorValue)
