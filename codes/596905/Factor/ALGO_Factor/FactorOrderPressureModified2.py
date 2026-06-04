import math
from System.Factor import Factor


class FactorOrderPressureModified2(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
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
        pressureBuy, pressureSell = self.__emaOrderPressure.getLastFactorValue()

        if pressureBuy < 0 or pressureSell < 0:
            factorValue = 0
        else:
            factorValue = math.log(pressureBuy + self.__eps) - math.log(pressureSell + self.__eps)

        self._addFactorValue(factorValue)
