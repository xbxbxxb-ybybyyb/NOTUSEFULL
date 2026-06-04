#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorMeanVolumeStdRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("BidMeanVolumeList", [])
        self._addIntermediate("AskMeanVolumeList", [])

    def calculate(self):
        bidMeanVolumeList = self.getIntermediate("BidMeanVolumeList")
        askMeanVolumeList = self.getIntermediate("AskMeanVolumeList")
        transaction = self._getLastTickData("Transactions")
        if transaction is not None:
            bsFlag = self._getTransactionData("BSFlag", transaction)
            volume = self._getTransactionData("Volume", transaction)
            bidMeanVolumeList.append(np.nansum(volume[bsFlag == 1]) / (bsFlag == 1).sum() if (bsFlag == 1).sum() != 0 else 0.)
            askMeanVolumeList.append(np.nansum(volume[bsFlag == 2]) / (bsFlag == 2).sum() if (bsFlag == 2).sum() != 0 else 0.)
        else:
            bidMeanVolumeList.append(None)
            askMeanVolumeList.append(None)
        filterBidMeanVolumeList = list(filter(lambda x: x is not None, bidMeanVolumeList))
        filterAskMeanVolumeList = list(filter(lambda x: x is not None, askMeanVolumeList))

        bidMeanVolumeSlice = np.array(filterBidMeanVolumeList[-self.__lag:])
        askMeanVolumeSlice = np.array(filterAskMeanVolumeList[-self.__lag:])
        if len(bidMeanVolumeSlice) <= 1:
            factorValue = 0.
        else:
            factorValue = np.nanstd(bidMeanVolumeSlice) / np.nanstd(askMeanVolumeSlice) if np.nanstd(askMeanVolumeSlice) != 0 else 0.
        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)





