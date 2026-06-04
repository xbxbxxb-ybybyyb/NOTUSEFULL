#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorTopDownVolumeRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")

        self._addIntermediate("LastPriceList", [])
        self._addIntermediate("VolumeList", [])

    def calculate(self):
        lastPrice = self._getLastTickData("LastPrice")
        volume = self._getLastTickData("Volume")
        lastPriceList = self.getIntermediate("LastPriceList")
        volumeList = self.getIntermediate("VolumeList")

        if len(lastPriceList) == 0:
            hisLastPrice = self._getAllHistoricalTickData("LastPrice")
            hisVolume = self._getAllHistoricalTickData("Volume")
            lastPriceList.extend(hisLastPrice)
            volumeList.extend(hisVolume)

        lastPriceList.append(lastPrice)
        volumeList.append(volume)

        lastPriceSlice = np.array(lastPriceList[-self.__window:])
        volumeSlice = np.array(volumeList[-self.__window:])
        volumeTop = np.nansum(volumeSlice[lastPriceSlice > np.nanpercentile(lastPriceSlice, 80)])
        volumeDown = np.nansum(volumeSlice[lastPriceSlice < np.nanpercentile(lastPriceSlice, 20)])

        if volumeTop != 0:
            factorValue = volumeDown / volumeTop
        else:
            lastFactorValue = self.getLastFactorValue()
            if lastFactorValue is not None:
                factorValue = lastFactorValue
            else:
                factorValue = 0.

        self._addFactorValue(factorValue)

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])




