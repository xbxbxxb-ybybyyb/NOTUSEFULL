import numpy as np

from System.Factor import Factor


class FactorOrderBookBidVolumeShiftX(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")
        self.__lag = self._getParameter("Lag")
        self.__decay = self._getParameter("Decay")
        self.__decayRatio = np.array([self.__decay ** i for i in range(10)])

        self._addIntermediate("BidVolumeList", [])
        self._addIntermediate("BidVolumeRatioList", [])

    def calculate(self):
        bidVolume = self._getLastTickData("BidVolume")
        bidVol = np.nansum(bidVolume * self.__decayRatio)

        bidVolList = self.getIntermediate("BidVolumeList")
        bidVol = self._EMA_calculate(bidVol, bidVolList, self.__window)
        bidVolList.append(bidVol)

        bidVolRatio = np.log((bidVolList[-1] + 10) / (bidVolList[-2] + 10)) if len(bidVolList) >= self.__window / 2 else 0.
        bidVolRatio = np.clip(bidVolRatio, -2, 2) * 1000

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

