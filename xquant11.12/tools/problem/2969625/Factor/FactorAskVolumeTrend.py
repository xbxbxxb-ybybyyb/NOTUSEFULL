#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorAskVolumeTrend(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

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
        if len(askVolumeSlice) > 1:
            factorValue = np.corrcoef(askVolumeSlice, np.arange(len(askVolumeSlice)))[0, 1]
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)





