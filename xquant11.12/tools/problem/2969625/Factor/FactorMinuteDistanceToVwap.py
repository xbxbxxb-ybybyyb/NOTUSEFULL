from System.Factor import Factor
import numpy as np


class FactorMinuteDistanceToVwap(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("Vwaps", [])

    def calculate(self):

        vwapList = self.getIntermediate("Vwaps")

        closep = self._getLastMinuteData("ClosePrice")
        amount = self._getLastNMinuteData("Amount", self.__lag)
        volume = self._getLastNMinuteData("Volume", self.__lag)

        if np.nansum(volume) > 1e-6:
            vwapList.append(np.nansum(amount) / np.nansum(volume))
        else:
            if vwapList:  # 如果有前一个用前一个代替
                vwapList.append(vwapList[-1])
            else:
                vwapList.append(closep)

        factorValue = ((closep / vwapList[-1]) - 1) * 1e2

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)
