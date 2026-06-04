import numpy as np
from System.Factor import Factor


class FactorMinuteDisToAccLow(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

    def calculate(self):
        close = self._getLastMinuteData("ClosePrice")
        low = np.nanmin(self._getAllTodayMinuteData("ClosePrice"))

        if close > 1e-4 and low > 1e-4:
            factorValue = (close / low - 1) * 100
        else:
            lastFactorValue = self.getLastFactorValue()
            if lastFactorValue is not None:
                factorValue = lastFactorValue
            else:
                factorValue = 0.

        self._addFactorValue(factorValue)


