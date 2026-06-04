#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorBidNumSharpe(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("BidNumList", [])

    def calculate(self):
        bidNumList = self.getIntermediate("BidNumList")
        transaction = self._getLastTickData("Transactions")
        if transaction is not None:
            bsFlag = self._getTransactionData("BSFlag", transaction)
            bidNumList.append((bsFlag == 1).sum())

        bidNumSlice = np.array(bidNumList[-self.__lag:])
        if len(bidNumSlice) <= 1:
            factorValue = 0.
        else:
            factorValue = np.nanmean(bidNumSlice) / np.nanstd(bidNumSlice) if np.nanstd(bidNumSlice) != 0 else 0

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)





