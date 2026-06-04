from System.Factor import Factor
import numpy as np


class FactorAskWeightedVolumeRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__svlag = self._getParameter("ShortVolumeLag")
        self.__lvlag = self._getParameter("LongVolumeLag")

        self._addIntermediate("AskWeightedVolume", [])

    def calculate(self):

        askwv_list = self.getIntermediate("AskWeightedVolume")
        askv = self._getLastTickData("AskVolume")
        w = np.linspace(0.1, 1, len(askv))[::-1]
        askwv = np.dot(askv, w) / np.nansum(w)
        askwv_list.append(askwv)

        lm = np.nanmean(askwv_list[-self.__lvlag:])
        if lm != 0:
            if len(askwv_list) <= self.__svlag:
                sm = np.nanmean(askwv_list[-(len(askwv_list)//2):])
            else:
                sm = np.nanmean(askwv_list[-self.__svlag:])
            factorValue = sm / lm
        else:
            lastValue = self.getLastFactorValue()
            if lastValue is not None:
                factorValue = lastValue
            else:
                factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
