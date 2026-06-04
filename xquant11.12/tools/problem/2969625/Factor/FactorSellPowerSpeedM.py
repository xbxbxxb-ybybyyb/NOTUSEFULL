import math
import numpy as np
from System.Factor import Factor


class FactorSellPowerSpeedM(Factor):
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
        accAskAmount = self.__emaOrderPressure.getLastFactorValue()[1]
        MAAmount = np.nanmean(self._getLastNTickData("Amount", self.__MAAmountLag))
        emaOrderPressure = self.__emaOrderPressure.getFactorValueList()

        if accAskAmount < 0 or MAAmount <= 0 or len(emaOrderPressure) < 10:
            factorValue = 1.4
        else:
            factorValue = -math.log(accAskAmount / MAAmount + self.__eps)

        self._addFactorValue(factorValue)
