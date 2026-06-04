#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorNetVolumeSharpe(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("BidVolumeList", [])
        self._addIntermediate("AskVolumeList", [])

    def calculate(self):
        bidVolumeList = self.getIntermediate("BidVolumeList")
        askVolumeList = self.getIntermediate("AskVolumeList")
        transaction = self._getLastTickData("Transactions")
        if transaction is not None:
            bsFlag = self._getTransactionData("BSFlag", transaction)
            volume = self._getTransactionData("Volume", transaction)
            bidVolume = np.nansum(volume[bsFlag == 1])
            askVolume = np.nansum(volume[bsFlag == 2])
            bidVolumeList.append(bidVolume)
            askVolumeList.append(askVolume)

        tradeVolumeDiffSlice = np.array(bidVolumeList[-self.__lag:]) - np.array(askVolumeList[-self.__lag:])
        if len(tradeVolumeDiffSlice) <= 1:
            factorValue = 0.
        else:
            factorValue = np.nanmean(tradeVolumeDiffSlice) / np.nanstd(tradeVolumeDiffSlice) if np.nanstd(tradeVolumeDiffSlice) != 0 else 0
        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)





