import numpy as np
from System.Factor import Factor


class FactorMinuteDisToHigh(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):
        close = self._getLastMinuteData("ClosePrice")
        high = np.nanmax(self._getLastNMinuteData("ClosePrice", self.__lag))

        if close > 1e-4 and high > 1e-4:
            factorValue = (close / high - 1) * 100
        else:
            lastFactorValue = self.getLastFactorValue()
            if lastFactorValue is not None:
                factorValue = lastFactorValue
            else:
                factorValue = 0.

        self._addFactorValue(factorValue)


