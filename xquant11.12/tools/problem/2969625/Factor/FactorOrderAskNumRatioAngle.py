import numpy as np
from scipy.fftpack import fft
from System.Factor import Factor


class FactorOrderAskNumRatioAngle(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__sLag = self._getParameter("SmoothLag")

        self._addIntermediate("AskNumRatioList", [])

    def calculate(self):
        askNumArray = self._getLastTickData("AskNum")
        bidNumArray = self._getLastTickData("BidNum")

        askNum = np.nansum(askNumArray * np.arange(len(askNumArray), 0, -1))
        bidNum = np.nansum(bidNumArray * np.arange(len(bidNumArray), 0, -1))
        askNumRatio = askNum / (bidNum + askNum) if bidNum + askNum > 1e-6 else 0.

        askNumRatioList = self.getIntermediate("AskNumRatioList")
        askNumRatioList.append(askNumRatio)
        askVolumeRatioSlice = np.array(askNumRatioList[-self.__lag:])
        if len(askVolumeRatioSlice) > 5:
            lookBack = self.__sLag if self.__sLag < len(askVolumeRatioSlice) else int(min(16, len(askVolumeRatioSlice) / 3))
            factorValue = np.nanmean(np.angle(fft(askVolumeRatioSlice))[-lookBack:])
        else:
            factorValue = 0.

        self._addFactorValue(factorValue)



