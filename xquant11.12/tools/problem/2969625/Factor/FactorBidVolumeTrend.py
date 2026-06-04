#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorBidVolumeTrend(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("BidVolumeList", [])

    def calculate(self):
        bidVolumeList = self.getIntermediate("BidVolumeList")
        transaction = self._getLastTickData("Transactions")
        if transaction is not None:
            bsFlag = self._getTransactionData("BSFlag", transaction)
            volume = self._getTransactionData("Volume", transaction)
            bidVolume = np.nansum(volume[bsFlag == 1])
            bidVolumeList.append(bidVolume)
        else:
            bidVolumeList.append(None)
        filterBidVolumeList = list(filter(lambda x: x is not None, bidVolumeList))

        bidVolumeSlice = np.array(filterBidVolumeList[-self.__lag:])
        if len(bidVolumeSlice) > 1:
            factorValue = np.corrcoef(bidVolumeSlice, np.arange(len(bidVolumeSlice)))[0, 1]
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)




