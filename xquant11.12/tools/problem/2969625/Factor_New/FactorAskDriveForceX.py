import numpy as np
from System.Factor import Factor


class FactorAskDriveForceX(Factor):
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
        self._addIntermediate("emaAskDriveForceList", [])
        self._nor_volume = None

    def calculate(self):
        if self._nor_volume < 1e-6:
            volumeList = self._getAllTodayTickData("Volume")
            if volumeList[0] < 1e-4:
                self._nor_volume = np.nanmean(volumeList[:5])
            else:
                self._nor_volume = volumeList[0]

        emaAskDriveForceList = self.getIntermediate("emaAskDriveForceList")
        _, askDriveForce = self.__driveForce.getLastFactorValue()

        askDriveForceRatio =  - askDriveForce / self._nor_volume if self._nor_volume > 1e-6 else 0
        factorValue = self._EMA_calculate(askDriveForceRatio, emaAskDriveForceList, self.__lag)
        emaAskDriveForceList.append(factorValue)

        self._addFactorValue(factorValue)

    def _onNewDay(self):
        hisVolume = self._getAllHistoricalTickData("Volume")
        self._nor_volume = np.nanmean(hisVolume)

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])
