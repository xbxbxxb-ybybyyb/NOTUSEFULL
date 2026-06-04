import numpy as np
import math
from System.Factor import Factor


class FactorAskDriveForce_MDF(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__level = self._getParameter("Level")
        self.__lag = self._getParameter("Lag")
        self.__weights = np.arange(1, self.__lag + 1)

        self.__driveForce = self._getFactor(
            {
                "ClassName": "OrderDriveForce",
                "Parameters": {
                    "Level": self.__level
                }
            }
        )
        self._addIntermediate("AskDriveForceRatioList", [])

    def calculate(self):
        volumeList = self._getAllTodayTickData("Volume")
        if volumeList[0] == 0:
            volume = np.nanmean(volumeList[:5])
        else:
            volume = volumeList[0]
        _, askDriveForce = self.__driveForce.getLastFactorValue()
        askDriveForceRatioList = self.getIntermediate("AskDriveForceRatioList")
        askDriveForceRatio = askDriveForce / volume if volume != 0 else 0
        askDriveForceRatioList.append(askDriveForceRatio)

        localAskDriveForceRatioArray = np.array(askDriveForceRatioList[-self.__lag:])
        L = len(localAskDriveForceRatioArray)
        localWeights = self.__weights[-L:]

        factorValue = np.nansum(localAskDriveForceRatioArray * localWeights) / np.nansum(localWeights)
        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])
