import numpy as np
from System.Factor import Factor


class FactorVolumeMAGrowthFlexible(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__maLag = self._getParameter("MALag")
        self.__lookBack = 2 * self.__maLag

    def calculate(self):
        volumeArray = self._getAllTodayTickData("Volume")
        
        slowMAVolume = np.nanmean(volumeArray[-self.__lookBack:])
        fastMAVolume = np.nanmean(volumeArray[-self.__maLag:])

        if fastMAVolume < 0 or slowMAVolume <= 0:
            value = 0.0
        else:
            value = fastMAVolume / slowMAVolume

        self._addFactorValue(value)

