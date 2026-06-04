import numpy as np
from System.Factor import Factor


class FactorMinuteRetGap(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("RetList", [])

    def calculate(self):
        volume = self._getLastMinuteData("Volume")
        amount = self._getLastMinuteData("Amount")
        price = self._getLastMinuteData("ClosePrice")
        volumeAcc = np.nansum(self._getAllTodayMinuteData("Volume"))
        amountAcc = np.nansum(self._getAllTodayMinuteData("Amount"))

        vwap = self.compute_vwap(volume, amount, price)
        vwapAcc = self.compute_vwap(volumeAcc, amountAcc, price)

        ret = (vwap / vwapAcc - 1) * 100 if vwapAcc > 1e-4 else 0.
        retList = self.getIntermediate("RetList")
        retList.append(ret)

        retArray = np.array(retList[-self.__lag:])
        factorValue = np.nanmax(retArray) - np.nanmin(retArray)

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)

    def compute_vwap(self, volume, amount, price):
        vwap = amount / volume if volume > 1e-4 else price
        return vwap

