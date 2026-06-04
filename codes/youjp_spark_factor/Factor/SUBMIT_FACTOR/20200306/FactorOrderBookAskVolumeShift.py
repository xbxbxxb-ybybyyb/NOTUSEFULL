import numpy as np
from System.Factor import Factor


class FactorOrderBookAskVolumeShift(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__decay = self._getParameter("Decay")
        self.__decayRatio = np.array([self.__decay ** i for i in range(10)])

        self._addIntermediate("askVolume", [])
        self._addIntermediate("askVolumeRatio", [])

    def calculate(self):
        askVolume = self._getLastNTodayTickData("AskVolume", 1)[-1]

        askVol = np.nansum(askVolume * self.__decayRatio)

        askVolList = self.getIntermediate("askVolume")
        askVol = self._EMA_calculate(askVol, askVolList, self.__lag)
        askVolList.append(askVol)

        askVolRatio = 0.
        if len(askVolList) > 1:
            if askVolList[-1] > 0 and askVolList[-2] > 0:
                askVolRatio = np.log(askVolList[-1] / askVolList[-2])


        askVolRatioList = self.getIntermediate("askVolumeRatio")
        askVolRatio = self._EMA_calculate(askVolRatio, askVolRatioList, self.__lag)
        askVolRatioList.append(askVolRatio)

        self._addFactorValue(askVolRatio)

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])

