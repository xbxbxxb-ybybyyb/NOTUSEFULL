#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorAskVolumeQuantile(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__sLag = self._getParameter("SmoothLag")

        self._addIntermediate("AskVolumeList", [])

    def calculate(self):
        askVolumeList = self.getIntermediate("AskVolumeList")
        transaction = self._getLastTickData("Transactions")
        if transaction is not None:
            bsFlag = self._getTransactionData("BSFlag", transaction)
            volume = self._getTransactionData("Volume", transaction)
            askVolume = np.nansum(volume[bsFlag == 2])
            askVolumeList.append(askVolume)
        else:
            askVolumeList.append(None)
        filterAskVolumeList = list(filter(lambda x: x is not None, askVolumeList))

        askVolumeSlice = np.array(filterAskVolumeList[-self.__lag:])
        if len(askVolumeSlice) == 0:
            factorValue = 0
        else:
            factorValue = sum(askVolumeSlice < askVolumeSlice[-1]) / len(askVolumeSlice)

        factorValueList = self.getFactorValueList()
        factorValue = self._EMA_calculate(factorValue, factorValueList, self.__sLag)

        self._addFactorValue(factorValue)

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])




