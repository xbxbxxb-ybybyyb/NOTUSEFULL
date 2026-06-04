#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorBidVolumeQuantile(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__sLag = self._getParameter("SmoothLag")

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
        if len(bidVolumeSlice) == 0:
            factorValue = 0
        else:
            factorValue = sum(bidVolumeSlice < bidVolumeSlice[-1]) / len(bidVolumeSlice)

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






