import numpy as np
from System.Factor import Factor


class VWAPPrice2(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )

    def calculate(self):
        volumeArray = self._getAllTodayTickData("Volume")
        amountArray = self._getAllTodayTickData("Amount")
        lastVWAPPrice = self.getLastFactorValue()
        midPrice = self.__midPrice.getLastFactorValue()

        totalVolume = np.nansum(volumeArray)
        totalAmount = np.nansum(amountArray)

        if totalVolume > 0:
            factorValue = totalAmount / totalVolume
        elif lastVWAPPrice is not None and lastVWAPPrice > 0:
            factorValue = lastVWAPPrice
        else:
            factorValue = midPrice

        self._addFactorValue(factorValue)
