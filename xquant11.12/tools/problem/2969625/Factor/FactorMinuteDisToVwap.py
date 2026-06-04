import numpy as np
from System.Factor import Factor


class FactorMinuteDisToVwap(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):
        volume = self._getLastMinuteData("Volume")
        amount = self._getLastMinuteData("Amount")
        price = self._getLastMinuteData("ClosePrice")
        volumeAcc = np.nansum(self._getLastNMinuteData("Volume", self.__lag))
        amountAcc = np.nansum(self._getLastNMinuteData("Amount", self.__lag))
        vwap = self.compute_vwap(volume, amount, price)
        vwapAcc = self.compute_vwap(volumeAcc, amountAcc, price)

        if vwap > 1e-4 and vwapAcc > 1e-4:
            factorValue = (vwap / vwapAcc - 1) * 100
        else:
            lastFactorValue = self.getLastFactorValue()
            if lastFactorValue is not None:
                factorValue = lastFactorValue
            else:
                factorValue = 0.

        self._addFactorValue(factorValue)

    def compute_vwap(self, volume, amount, price):
        vwap = amount / volume if volume > 1e-4 else price
        return vwap

