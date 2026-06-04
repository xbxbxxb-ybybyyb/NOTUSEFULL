import numpy as np
from System.Factor import Factor


class FactorPAVShiftInc(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.window = self._getParameter("Window")
        self.lag = self._getParameter("Lag")
        self.decay = self._getParameter("Decay")
        self.decayRatio = np.array([self.decay ** i for i in range(10)])

        self._addIntermediate("VolumeList", [])
        self._addIntermediate("VolumeRatioList", [])

    def calculate(self):
        volume = self._getLastTickData("AskVolume")
        vol = np.nansum(volume * self.decayRatio)

        volList = self.getIntermediate("VolumeList")
        vol = self._EMA_calculate(vol, volList, self.window)
        volList.append(vol)

        volRatio = - np.log((volList[-1] + 10) / (volList[-2] + 10)) if len(volList) >= self.window / 2 else 0.
        volRatio = np.clip(volRatio, -2, 2)

        volRatioList = self.getIntermediate("VolumeRatioList")
        volRatioList.append(volRatio)

        factorValue = (volRatioList[-1] - np.nanmean(volRatioList[-self.lag:])) * 1000

        self._addFactorValue(factorValue)

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])

