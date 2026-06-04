import numpy as np
from System.Factor import Factor


class FactorVolumeVolRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__lookBack = self._getParameter("LookBack")

        self._addIntermediate("bidVolume", [])
        self._addIntermediate("askVolume", [])

    def calculate(self):
        bidV0 = self._getLastTickData("BidVolume")[0]
        askV0 = self._getLastTickData("AskVolume")[0]

        bidVolumeList = self.getIntermediate("bidVolume")
        #bidVolume = self._EMA_calculate(bidV0, bidVolumeList, self.__lag)
        bidVolumeList.append(bidV0)
        askVolumeList = self.getIntermediate("askVolume")
        #askVolume = self._EMA_calculate(askV0, askVolumeList, self.__lag)
        askVolumeList.append(askV0)

        if len(bidVolumeList) <= 1:
            value = 0.
        else:
            bidP0Std = np.nanstd(bidVolumeList[-self.__lookBack:], ddof=1)
            askP0Std = np.nanstd(askVolumeList[-self.__lookBack:], ddof=1)
            if askP0Std == 0:
                value = 0.
            else:
                value = bidP0Std / askP0Std

        self._addFactorValue(value)

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])

