import numpy as np
from System.Factor import Factor


class FactorMinuteTransBidNumRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):
        transactionData = self._getLastNTickData("Transactions", self.__lag)
        bidNumList = []
        for transaction in transactionData:
            if transaction is not None:
                bsFlag = self._getTransactionData("BSFlag", transaction)
                bidNum = (bsFlag == 1).sum()
                bidNumList.append(bidNum)

        numTrades = self._getLastMinuteData("NumTrades")

        tickTradeNum = np.nansum(bidNumList)
        if tickTradeNum > 1e-4:
            factorValue = numTrades / tickTradeNum
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)

