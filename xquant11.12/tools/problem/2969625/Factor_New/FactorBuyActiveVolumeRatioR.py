import numpy as np
from System.Factor import Factor


class FactorBuyActiveVolumeRatioR(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.__lag = self._getParameter("Lag")
        self.BuyActiveVolume = self._getFactor(
            {
                "ClassName": "BuyActiveVolume",
                "Parameters": {
                    "Lag": self.__lag
                }
            }
        )

    def calculate(self):
        buyActiveVolume = self.BuyActiveVolume.getLastFactorValue()
        volumeList = self._getLastNTickData("Volume", 20)
        if len(volumeList) >= 5:
            factorValue = (buyActiveVolume - np.mean(volumeList)) / np.std(volumeList) if np.std(volumeList) > 1e-6 else 0
        else:
            factorValue =  0

        self._addFactorValue(factorValue)
