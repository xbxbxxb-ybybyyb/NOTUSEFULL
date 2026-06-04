import math
import numpy as np
from System.Factor import Factor


class FactorSellPower(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__MAAmountLag = self._getParameter("MAAmountLag")
        self.__eps = 1e-5

        self.__orderEvaluate = self._getFactor(
            {
                "ClassName": "OrderEvaluate2",
            }
        )

    def calculate(self):
        accAskAmount = self.__orderEvaluate.getLastFactorValue()[1]
        MAAmount = np.nanmean(self._getLastNTickData("Amount", self.__MAAmountLag))

        if accAskAmount < 0 or MAAmount <= 0:
            factorValue = 0
        else:
            factorValue = math.log(accAskAmount / MAAmount + self.__eps)

        self._addFactorValue(factorValue)
