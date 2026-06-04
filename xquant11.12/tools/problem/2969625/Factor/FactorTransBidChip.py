#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorTransBidChip(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):
        transactionData = self._getLastNTickData("Transactions", self.__lag)
        chipDict = {}
        for transaction in transactionData:
            if transaction is not None:
                bsFlag = self._getTransactionData("BSFlag", transaction)
                BidOrder = self._getTransactionData("BidOrder", transaction)
                VolumeData = self._getTransactionData("Volume", transaction)
                BidOrder = BidOrder[bsFlag == 1]
                VolumeData = VolumeData[bsFlag == 1]
                if len(BidOrder) > 0:
                    for i in range(BidOrder.shape[0]):
                        bidOrder = BidOrder[i]
                        volume = VolumeData[i]
                        if bidOrder in chipDict:
                            chipDict[bidOrder] += volume
                        else:
                            chipDict[bidOrder] = volume

        chipVolume = np.array(list(chipDict.values()))

        if len(chipVolume) > 0:
            factorValue = self.__compute_skew(chipVolume)
        else:
            factorValue = 0.

        self._addFactorValue(factorValue)

    @staticmethod
    def __compute_skew(arr):
        if len(arr) <= 1:
            return 0
        else:
            arr_mean = np.nanmean(arr)
            arr_std = np.nanstd(arr)
            three = np.nanmean((arr - arr_mean)**3)
            skew = three / arr_std**3 if arr_std != 0 else 0
            return skew







