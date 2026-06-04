import numpy as np
from System.Factor import Factor


class FactorOrderBookAskVolumeShiftX(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")
        self.__lag = self._getParameter("Lag")
        self.__decay = self._getParameter("Decay")
        self.__decayRatio = np.array([self.__decay ** i for i in range(10)])

        self._addIntermediate("AskVolumeList", [])
        self._addIntermediate("AskVolumeRatioList", [])

    def calculate(self):
        askVolume = self._getLastTickData("AskVolume")
        askVol = np.nansum(askVolume * self.__decayRatio)

        askVolList = self.getIntermediate("AskVolumeList")
        askVol = self._EMA_calculate(askVol, askVolList, self.__window)
        askVolList.append(askVol)

        askVolRatio = - np.log((askVolList[-1] + 10) / (askVolList[-2] + 10)) if len(askVolList) >= self.__window / 2 else 0.
        askVolRatio = np.clip(askVolRatio, -2, 2) * 1000

        askVolRatioList = self.getIntermediate("AskVolumeRatioList")
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

