import numpy as np
from System.Factor import Factor


class FactorOrderBookBidVolumeShift(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__decay = self._getParameter("Decay")

        self._addIntermediate("BidVolumeList", [])
        self._addIntermediate("BidVolumeRatioList", [])

    def calculate(self):
        bidVolume = self._getLastNTodayTickData("BidVolume", 1)[-1]
        decayRatio = np.array([self.__decay ** i for i in range(len(bidVolume))])

        bidVol = np.nansum(bidVolume * decayRatio)

        bidVolList = self.getIntermediate("BidVolumeList")
        bidVol = self._EMA_calculate(bidVol, bidVolList, self.__lag)
        bidVolList.append(bidVol)

        bidVolRatio = 0.
        if len(bidVolList) > 1:
            if bidVolList[-1] > 0 and bidVolList[-2] > 0:
                bidVolRatio = np.log(bidVolList[-1] / bidVolList[-2])

        bidVolRatioList = self.getIntermediate("BidVolumeRatioList")
        bidVolRatio = self._EMA_calculate(bidVolRatio, bidVolRatioList, self.__lag)
        bidVolRatioList.append(bidVolRatio)

        self._addFactorValue(bidVolRatio)

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])

