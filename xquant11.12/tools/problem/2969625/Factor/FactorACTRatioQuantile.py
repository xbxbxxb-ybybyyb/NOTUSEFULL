import numpy as np
from System.Factor import Factor


class FactorACTRatioQuantile(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lookback = self._getParameter("LookBack")
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("ACTList", [])

    def calculate(self):
        import datetime as dt
        time = self._getLastTickData("Timestamp")
        time = dt.datetime.strftime(dt.datetime.fromtimestamp(time),'%H%M%S')
        if time == '093917':
            print('!')
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

        actArray = np.array(actList[-self.__lookback:])
        if len(actArray) < 1:
            factorValue = 0.
        else:
            factorValue = sum(actArray < actArray[-1]) / len(actArray)

        if np.isnan(factorValue):
            factorValue = 0.

        factorValueList = self.getFactorValueList()
        factorValue = self._EMA_calculate(factorValue, factorValueList, self.__lag)

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

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])

