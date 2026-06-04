import numpy as np
from System.Factor import Factor


class FactorMinuteVwapCross(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__sLag = self._getParameter("ShortLag")
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("VwapList", [])

    def calculate(self):
        volume = self._getLastMinuteData("Volume")
        amount = self._getLastMinuteData("Amount")
        price = self._getLastMinuteData("ClosePrice")
        vwap = self.compute_vwap(volume, amount, price)

        vwapList = self.getIntermediate("VwapList")
        vwapList.append(vwap)

        numerator = np.nanmean(vwapList[-self.__sLag:])
        denominator = np.nanmean(vwapList[-self.__lag:])

        if numerator > 1e-4 and denominator > 1e-4 and vwap > 1e-4:
            factorValue = (numerator / denominator + vwap / numerator + denominator / vwap - 3) * 1e5
        else:
            lastFactorValue = self.getLastFactorValue()
            if lastFactorValue is not None:
                factorValue = lastFactorValue
            else:
                factorValue = 0

        self._addFactorValue(factorValue)

    def compute_vwap(self, volume, amount, price):
        vwap = amount / volume if volume > 1e-4 else price
        return vwap

