import numpy as np
from System.Factor import Factor


class FactorSellActiveVolumeRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.__lag = self._getParameter("Lag")
        self.__sellActiveVolume = self._getFactor(
            {
                "ClassName": "SellActiveVolume",
                "Parameters": {
                    "Lag": self.__lag
                }
            }
        )

    def calculate(self):
        sellActiveVolume = self.__sellActiveVolume.getLastFactorValue()
        volume = np.mean(self._getLastNTickData("Volume", self.__lag))
        factorValue = sellActiveVolume / volume if volume > 1e-6 else 0
        self._addFactorValue(factorValue)
