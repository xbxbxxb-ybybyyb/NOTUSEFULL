import numpy as np
from System.Factor import Factor


class FactorTransAskNumRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__sLag = self._getParameter("LagShort")
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
            
        numTrades = np.nansum(askNumList[-self.__sLag:])
        tickTradeNum = np.nansum(askNumList[-self.__lag:])
        if tickTradeNum > 1e-4:
            factorValue = numTrades / tickTradeNum
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)

