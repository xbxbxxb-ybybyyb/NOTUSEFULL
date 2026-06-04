#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorAskNumSharpeX(Factor):
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
        else:
            askNumList.append(0)

        askNumSlice = np.array(askNumList[-self.__lag:])
        if len(askNumSlice) < 5:
            factorValue = - 1.
        else:
            askNumStd = np.nanstd(askNumSlice)
            if askNumStd > 1e-6:
                factorValue = - np.nanmean(askNumSlice) / askNumStd
            else:
                lastFactorValue = self.getLastFactorValue()
                if lastFactorValue is not None:
                    factorValue = lastFactorValue
                else:
                    factorValue = - 1.

        self._addFactorValue(factorValue)





