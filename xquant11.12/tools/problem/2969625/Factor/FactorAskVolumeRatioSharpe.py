#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorAskVolumeRatioSharpe(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("AskVolumeRatioList", [])

    def calculate(self):
        askVolumeRatioList = self.getIntermediate("AskVolumeRatioList")
        transaction = self._getLastTickData("Transactions")
        if transaction is not None:
            bsFlag = self._getTransactionData("BSFlag", transaction)
            volume = self._getTransactionData("Volume", transaction)
            askVolume = np.nansum(volume[bsFlag == 2])
            totalVolume = np.nansum(volume[(bsFlag == 1) | (bsFlag == 2)])
            askVolumeRatio = askVolume / totalVolume if totalVolume != 0 else 0.
            askVolumeRatioList.append(askVolumeRatio)
        else:
            askVolumeRatioList.append(None)
        filterAskVolumeRatioList = list(filter(lambda x: x is not None, askVolumeRatioList))

        askVolumeRatioSlice = np.array(filterAskVolumeRatioList[-self.__lag:])
        if len(askVolumeRatioSlice) < 1:
            factorValue = 0.
        else:
            factorValue = np.nanmean(askVolumeRatioSlice) / np.nanstd(askVolumeRatioSlice) if np.nanstd(askVolumeRatioSlice) != 0 else 0

        self._addFactorValue(factorValue)




