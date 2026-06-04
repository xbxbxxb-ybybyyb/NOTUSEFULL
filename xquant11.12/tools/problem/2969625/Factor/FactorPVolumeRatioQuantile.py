#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorPVolumeRatioQuantile(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__emaLag = self._getParameter("EMALag")

        self._addIntermediate("BidVolumeRatioList", [])
        self._addIntermediate("AskVolumeRatioList", [])

    def calculate(self):
        bidVolumeRatioList = self.getIntermediate("BidVolumeRatioList")
        askVolumeRatioList = self.getIntermediate("AskVolumeRatioList")
        bidVolume = self._getLastTickData("BidVolume")[0]
        askVolume = self._getLastTickData("AskVolume")[0]
        totalVolume = bidVolume + askVolume
        bidVolumeRatio = bidVolume / totalVolume if totalVolume != 0 else 0.
        askVolumeRatio = askVolume / totalVolume if totalVolume != 0 else 0.
        bidVolumeRatioList.append(bidVolumeRatio)
        askVolumeRatioList.append(askVolumeRatio)

        bidVolumeRatioSlice = np.array(bidVolumeRatioList[-self.__lag:])
        askVolumeRatioSlice = np.array(askVolumeRatioList[-self.__lag:])
        if len(bidVolumeRatioSlice) < 1:
            quantile = 0.
        else:
            quantile = sum(bidVolumeRatioSlice < bidVolumeRatioSlice[-1]) / len(bidVolumeRatioSlice) - \
                          sum(askVolumeRatioSlice < askVolumeRatioSlice[-1]) / len(askVolumeRatioSlice)

        factorValueList = self.getFactorValueList()
        factorValue = self._EMA_calculate(quantile, factorValueList, self.__emaLag)

        self._addFactorValue(factorValue)

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])




