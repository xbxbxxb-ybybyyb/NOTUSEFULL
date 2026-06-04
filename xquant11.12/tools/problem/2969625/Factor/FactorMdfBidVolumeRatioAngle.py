#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from scipy.fftpack import fft
from System.Factor import Factor


class FactorMdfBidVolumeRatioAngle(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__sLag = self._getParameter("SmoothLag")

        self._addIntermediate("BidVolumeRatioList", [])

    def calculate(self):
        bidVolumeRatioList = self.getIntermediate("BidVolumeRatioList")
        transaction = self._getLastTickData("Transactions")
        if transaction is not None:
            bsFlag = self._getTransactionData("BSFlag", transaction)
            volume = self._getTransactionData("Volume", transaction)
            bidVolume = np.nansum(volume[bsFlag == 1])
            totalVolume = np.nansum(volume[(bsFlag == 1) | (bsFlag == 2)])
            bidVolumeRatio = bidVolume / totalVolume if totalVolume != 0 else 0.
            bidVolumeRatioList.append(bidVolumeRatio)
        else:
            bidVolumeRatioList.append(None)
        filterBidVolumeRatioList = list(filter(lambda x: x is not None, bidVolumeRatioList))

        bidVolumeRatioSlice = np.array(filterBidVolumeRatioList[-self.__lag:])
        if len(bidVolumeRatioSlice) > 5:
            lookBack = self.__sLag if self.__sLag < len(bidVolumeRatioSlice) else int(min(16, len(bidVolumeRatioSlice) / 3))
            factorValue = np.nanmean(np.angle(fft(bidVolumeRatioSlice))[-lookBack:])
        else:
            factorValue = 0.

        self._addFactorValue(factorValue)




