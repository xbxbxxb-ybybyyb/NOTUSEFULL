import numpy as np
from System.Factor import Factor


class FactorEMAPressureRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__orderEvaluateEMALag = self._getParameter("OrderEvaluateEMALag")

        self.__emaOrderEvaluate2 = self._getFactor(
            {
                "ClassName": "EMA",
                "Parameters": {
                    "Lag": self.__orderEvaluateEMALag,
                    "OriginalData": {
                        "ClassName": "OrderEvaluate2"
                    }
                }
            }
        )

    def calculate(self):
        pressureBuy, pressureSell = self.__emaOrderEvaluate2.getLastFactorValue()

        if pressureBuy <= 0 or pressureSell <= 0:
            value = 0.0
        else:
            value = np.log(pressureBuy) - np.log(pressureSell)

        self._addFactorValue(value)

