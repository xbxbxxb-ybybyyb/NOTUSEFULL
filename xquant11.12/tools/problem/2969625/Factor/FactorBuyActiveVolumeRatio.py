import numpy as np
from System.Factor import Factor


class FactorBuyActiveVolumeRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.__lag = self._getParameter("Lag")
        self.__buyActiveVolume = self._getFactor(
            {
                "ClassName": "BuyActiveVolume",
                "Parameters": {
                    "Lag": self.__lag
                }
            }
        )

    def calculate(self):
        buyActiveVolume = self.__buyActiveVolume.getLastFactorValue()
        volume = np.mean(self._getLastNTickData("Volume", self.__lag))
        factorValue = buyActiveVolume / volume if volume > 0 else 0
        self._addFactorValue(factorValue)
