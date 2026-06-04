import math
import numpy as np
from System.Factor import Factor


class FactorMAVolumeDistanceModified(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__MAFastLag = self._getParameter("MAFastLag")
        self.__MASlowLag = self._getParameter("MASlowLag")
        self.__eps = 1e-5

    def calculate(self):
        fastVolume = self._getLastNTodayTickData("Volume", self.__MAFastLag)
        slowVolume = self._getLastNTickData("Volume", self.__MASlowLag)
        lastMAVolume = np.nanmean(fastVolume)
        slowMAVolume = np.nanmean(slowVolume)

        if lastMAVolume < 0 or slowMAVolume < 0:
            factorValue = 0
        else:
            factorValue = math.log((lastMAVolume + self.__eps) / (slowMAVolume + self.__eps))

        self._addFactorValue(factorValue)
