#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorVolumeRatioQuantile(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("BidVolumeRatioList", [])
        self._addIntermediate("AskVolumeRatioList", [])

    def calculate(self):
        bidVolumeRatioList = self.getIntermediate("BidVolumeRatioList")
        askVolumeRatioList = self.getIntermediate("AskVolumeRatioList")
        transaction = self._getLastTickData("Transactions")
        if transaction is not None:
            bsFlag = self._getTransactionData("BSFlag", transaction)
            volume = self._getTransactionData("Volume", transaction)
            bidVolume = np.nansum(volume[bsFlag == 1])
            askVolume = np.nansum(volume[bsFlag == 2])
            totalVolume = np.nansum(volume[(bsFlag == 1) | (bsFlag == 2)])
            bidVolumeRatio = bidVolume / totalVolume if totalVolume > 1e-4 else 0.
            askVolumeRatio = askVolume / totalVolume if totalVolume > 1e-4 else 0.
            bidVolumeRatioList.append(bidVolumeRatio)
            askVolumeRatioList.append(askVolumeRatio)
        else:
            bidVolumeRatioList.append(0)
            askVolumeRatioList.append(0)

        bidVolumeRatioSlice = np.array(bidVolumeRatioList[-self.__lag:])
        askVolumeRatioSlice = np.array(askVolumeRatioList[-self.__lag:])
        if len(bidVolumeRatioSlice) < 5:
            factorValue = 0.
        else:
            factorValue = np.sum(bidVolumeRatioSlice < bidVolumeRatioSlice[-1]) / len(bidVolumeRatioSlice) - \
                          np.sum(askVolumeRatioSlice < askVolumeRatioSlice[-1]) / len(askVolumeRatioSlice)

        self._addFactorValue(factorValue)




