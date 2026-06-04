import numpy as np
from System.Factor import Factor


class FactorSellActiveDownVolumeZScoreR(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.__lag = self._getParameter("Lag")
        self.SellActiveDownVolume = self._getFactor(
            {
                "ClassName": "SellActiveDownVolume",
                "Parameters": {
                    "Lag": self.__lag
                }
            }
        )

    def calculate(self):
        factorValue = self.zscore(self.SellActiveDownVolume.getFactorValueList(), 5, 60)
        self._addFactorValue(-factorValue)

    @staticmethod
    def zscore(l1, w1, w2):
        std1 = np.nanstd(l1[-w2:])
        if std1 == 0 or np.isnan(std1):
            return 0
        else:
            return (np.nanmean(l1[-w1:]) - np.nanmean(l1[-w2:])) / std1
