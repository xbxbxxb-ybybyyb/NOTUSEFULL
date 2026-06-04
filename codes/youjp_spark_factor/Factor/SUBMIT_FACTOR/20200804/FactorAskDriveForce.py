import numpy as np
import math
from System.Factor import Factor


class FactorAskDriveForce(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__level = self._getParameter("Level")
        self.__lag = self._getParameter("Lag")

        self.__driveForce = self._getFactor(
            {
                "ClassName": "OrderDriveForce",
                "Parameters": {
                    "Level": self.__level
                }
            }
        )

    def calculate(self):
        volumeList = self._getAllTodayTickData("Volume")
        if volumeList[0] == 0:
            volume = np.nanmean(volumeList[:5])
        else:
            volume = volumeList[0]
        _, askDriveForce = self.__driveForce.getLastFactorValue()
        emaAskDriveForceList = self.getFactorValueList()
        askDriveForceRatio = askDriveForce / volume if volume !=0 else 0
        factorValue = self._EMA_calculate(askDriveForceRatio, emaAskDriveForceList, self.__lag)

        self._addFactorValue(factorValue)

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])