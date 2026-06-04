import numpy as np
from System.Factor import Factor


class AvePrice(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )

    def calculate(self):
        totalAmount = np.sum(self._getAllTodayTickData("Amount"))
        totalVolume = np.sum(self._getAllTodayTickData("Volume"))

        if totalVolume > 0:
            factorValue = totalAmount / totalVolume
        else:
            factorValue = self.__midPrice.getLastFactorValue()

        self._addFactorValue(factorValue)
