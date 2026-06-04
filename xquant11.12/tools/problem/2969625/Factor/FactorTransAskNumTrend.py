import numpy as np
from System.Factor import Factor


class FactorTransAskNumTrend(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("NumTradesList", [])

    def calculate(self):
        transaction = self._getLastTickData("Transactions")
        askNumList = self.getIntermediate("NumTradesList")
        if transaction is not None:
            bsFlag = self._getTransactionData("BSFlag", transaction)
            askNum = (bsFlag == 2).sum()
            askNumList.append(askNum)
        else:
            askNumList.append(0)

        askNumArray = np.array(askNumList[-self.__lag:])
        if len(askNumArray) > 1:
            factorValue = np.corrcoef(askNumArray, np.arange(len(askNumArray)))[0, 1]
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)

