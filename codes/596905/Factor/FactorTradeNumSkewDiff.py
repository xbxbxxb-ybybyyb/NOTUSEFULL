#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorTradeNumSkewDiff(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("BidNumList", [])
        self._addIntermediate("AskNumList", [])

    def calculate(self):
        bidNumList = self.getIntermediate("BidNumList")
        askNumList = self.getIntermediate("AskNumList")
        transaction = self._getLastTickData("Transactions")
        if transaction is not None:
            bsFlag = self._getTransactionData("BSFlag", transaction)
            bidNumList.append((bsFlag == 1).sum())
            askNumList.append((bsFlag == 2).sum())

        bidNumSlice = np.array(bidNumList[-self.__lag:])
        askNumSlice = np.array(askNumList[-self.__lag:])
        if len(bidNumSlice) <= 1:
            factorValue = 0.
        else:
            factorValue = self.__compute_skew(bidNumSlice) - self.__compute_skew(askNumSlice)

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)

    @staticmethod
    def __compute_skew(arr):
        if len(arr) <= 1:
            return np.nan
        else:
            arr_mean = np.nanmean(arr)
            arr_std = np.nanstd(arr)
            three = np.nanmean((arr - arr_mean)**3)
            skew = three / arr_std**3 if arr_std != 0 else 0
            return skew





