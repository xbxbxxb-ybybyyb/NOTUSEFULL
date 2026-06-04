import numpy as np
from System.Factor import Factor


class FactorAggressiveQtyRatioZScore(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.AggressiveOrderQty = self._getFactor({"ClassName": "AggressiveOrderQty"})

    def calculate(self):
        fv = self.zscore([x[0] - x[1] for x in self.AggressiveOrderQty.getFactorValueList()], 5, 60)

        self._addFactorValue(fv)

    @staticmethod
    def zscore(l1, w1, w2):
        std1 = np.nanstd(l1[-w2:])
        if std1 == 0 or np.isnan(std1):
            return 0
        else:
            return (np.nanmean(l1[-w1:]) - np.nanmean(l1[-w2:])) / std1
