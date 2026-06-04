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
        else:
            bidNumList.append(None)
        filterBidNumList = list(filter(lambda x: x is not None, bidNumList))

        bidNumSlice = np.array(filterBidNumList[-self.__lag:])
        if len(bidNumSlice) <= 1:
            factorValue = 0.
        else:
            factorValue = np.nanmean(bidNumSlice) / np.nanstd(bidNumSlice) if np.nanstd(bidNumSlice) != 0 else 0

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)





