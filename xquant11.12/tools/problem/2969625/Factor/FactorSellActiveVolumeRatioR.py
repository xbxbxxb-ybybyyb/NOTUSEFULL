import numpy as np
from System.Factor import Factor


class FactorSellActiveVolumeRatioR(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.__lag = self._getParameter("Lag")
        self.SellActiveVolume = self._getFactor(
            {
                "ClassName": "SellActiveVolume",
                "Parameters": {
                    "Lag": self.__lag
                }
            }
        )

    def calculate(self):
        sellActiveVolume = self.SellActiveVolume.getLastFactorValue()
        volumeList = self._getLastNTickData("Volume", 20)
        if len(volumeList) >= 5:
            factorValue = (sellActiveVolume - np.mean(volumeList)) / np.std(volumeList) if np.std(volumeList) > 1e-6 else 0
        else:
            factorValue = 0

        self._addFactorValue(-factorValue)
