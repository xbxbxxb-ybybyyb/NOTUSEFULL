import numpy as np
from System.Factor import Factor


class FactorSellActiveVolumeZScore(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.__lag = self._getParameter("Lag")
        self.__lag2 = self._getParameter("Lag2")
        self.sellActiveVolume = self._getFactor(
            {
                "ClassName": "SellActiveVolume",
                "Parameters": {
                    "Lag": self.__lag
                }
            }
        )

    def calculate(self):
        sellActiveVolume = self.sellActiveVolume.getFactorValueList()
        factorValue = self.zscoreTS(sellActiveVolume, self.__lag2)
        self._addFactorValue(factorValue)

    @staticmethod
    def zscoreTS(l1, w1):
        std1 = np.nanstd(l1)
        if std1 == 0 or np.isnan(std1):
            return 0
        else:
            return (l1[-1] - np.nanmean(l1[-w1:])) / std1