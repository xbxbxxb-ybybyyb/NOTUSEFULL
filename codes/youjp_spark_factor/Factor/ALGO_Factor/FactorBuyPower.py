import math
import numpy as np
from System.Factor import Factor


class FactorBuyPower(Factor):
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
        accBidAmount = self.__orderEvaluate.getLastFactorValue()[0]
        MAAmount = np.nanmean(self._getLastNTickData("Amount", self.__MAAmountLag))

        if accBidAmount < 0 or MAAmount <= 0:
            factorValue = 0
        else:
            factorValue = math.log(accBidAmount / MAAmount + self.__eps)

        self._addFactorValue(factorValue)
