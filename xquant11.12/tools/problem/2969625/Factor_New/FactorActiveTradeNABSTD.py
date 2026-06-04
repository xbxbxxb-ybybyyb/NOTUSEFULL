# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/05/05
from System.Factor import Factor
import numpy as np


class FactorActiveTradeNABSTD(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("BidNum", [])
        self._addIntermediate("AskNum", [])

    def calculate(self):
        askNumList = self.getIntermediate("AskNum")
        bidNumList = self.getIntermediate("BidNum")

        trade = self._getLastTickData("Transactions")
        if trade is not None:
            bsflag = self._getTransactionData("BSFlag", trade)
            askNumList.append(np.nansum(bsflag == 2))
            bidNumList.append(np.nansum(bsflag == 1))
        else:
            askNumList.append(0)
            bidNumList.append(0)

        if len(bidNumList) >= 5:
            factorValue = np.nanstd(askNumList[-self.__lag:]) - np.nanstd(bidNumList[-self.__lag:])
        else:
            factorValue = 0.

        self._addFactorValue(factorValue)
