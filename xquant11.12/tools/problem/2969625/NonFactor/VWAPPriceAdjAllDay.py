import numpy as np
from System.Factor import Factor


class VWAPPriceAdjAllDay(Factor):
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
        length = len(volumeArray)

        adjust_ratio = np.arange(length, 0, -1) / sum(np.arange(length, 0, -1))
        totalVolume = np.nansum(volumeArray * adjust_ratio[:length])
        totalAmount = np.nansum(amountArray * adjust_ratio[:length])
        if totalVolume > 0:
            factorValue = totalAmount / totalVolume
        elif lastVWAPPrice is not None and lastVWAPPrice > 0:
            factorValue = lastVWAPPrice
        else:
            factorValue = midPrice

        self._addFactorValue(factorValue)
