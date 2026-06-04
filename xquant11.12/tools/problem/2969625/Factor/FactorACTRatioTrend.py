import numpy as np
from System.Factor import Factor


class FactorACTRatioTrend(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("ACTList", [])

    def calculate(self):
        askVolume = self._getLastTickData("AskVolume")
        askPrice = self._getLastTickData("AskPrice")
        bidVolume = self._getLastTickData("BidVolume")
        bidPrice = self._getLastTickData("BidPrice")

        askAmount = self.compute_side_volume(askVolume * askPrice)
        bidAmount = self.compute_side_volume(bidVolume * bidPrice)
        act = 0
        if askAmount + bidAmount > 1e-4:
            act = (bidAmount - askAmount) / (bidAmount + askAmount)
        actList = self.getIntermediate("ACTList")
        actList.append(act)

        actArray = np.array(actList[-self.__lag:])
        if len(actArray) > 1:
            factorValue = np.corrcoef(actArray, np.arange(len(actArray)))[0, 1]
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)

    @staticmethod
    def compute_side_volume(volumeArray):
        non_zero_volume = volumeArray[volumeArray != 0]
        if len(non_zero_volume) <= 1:
            return np.nansum(non_zero_volume)
        else:
            weight = np.linspace(0, 1, len(non_zero_volume))
            weight = weight[::-1] / np.nansum(weight)
            return np.nansum(non_zero_volume * weight)

