#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorPVolumeStdRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("BidVolumeList", [])
        self._addIntermediate("AskVolumeList", [])

    def calculate(self):
        bidVolumeList = self.getIntermediate("BidVolumeList")
        askVolumeList = self.getIntermediate("AskVolumeList")
        bidVolumeArray = self._getLastTickData("BidVolume")
        askVolumeArray = self._getLastTickData("AskVolume")
        bidVolume, askVolume = self.__compute_side_volume(bidVolumeArray), self.__compute_side_volume(askVolumeArray)
        bidVolumeList.append(bidVolume)
        askVolumeList.append(askVolume)

        bidVolumeSlice = np.array(bidVolumeList[-self.__lag:])
        askVolumeSlice = np.array(askVolumeList[-self.__lag:])
        if len(bidVolumeSlice) <= 1:
            factorValue = 0.
        else:
            factorValue = np.nanstd(bidVolumeSlice) / np.nanstd(askVolumeSlice) if np.nanstd(askVolumeSlice) > 1e-6 else 0.
        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)

    @staticmethod
    def __compute_side_volume(volumeArray):
        non_zero_volume = volumeArray[volumeArray != 0]
        if len(non_zero_volume) <= 1:
            return np.nansum(non_zero_volume)
        else:
            weight = np.linspace(0, 1, len(non_zero_volume))
            weight = weight[::-1] / np.nansum(weight)
            return np.nansum(non_zero_volume * weight)





