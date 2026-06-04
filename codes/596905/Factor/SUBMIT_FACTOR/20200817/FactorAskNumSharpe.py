#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorAskNumSharpe(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("AskNumList", [])

    def calculate(self):
        askNumList = self.getIntermediate("AskNumList")
        transaction = self._getLastTickData("Transactions")
        if transaction is not None:
            bsFlag = self._getTransactionData("BSFlag", transaction)
            askNumList.append((bsFlag == 2).sum())

        askNumSlice = np.array(askNumList[-self.__lag:])
        if len(askNumSlice) <= 1:
            factorValue = 0.
        else:
            factorValue = np.nanmean(askNumSlice) / np.nanstd(askNumSlice) if np.nanstd(askNumSlice) != 0 else 0
        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)





