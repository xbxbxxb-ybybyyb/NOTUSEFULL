import numpy as np
from System.Factor import Factor


class FactorTransBidNumRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__sLag = self._getParameter("LagShort")
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("NumTradesList", [])

    def calculate(self):
        transaction = self._getLastTickData("Transactions")
        bidNumList = self.getIntermediate("NumTradesList")
        if transaction is not None:
            bsFlag = self._getTransactionData("BSFlag", transaction)
            bidNum = (bsFlag == 1).sum()
            bidNumList.append(bidNum)
        else:
            bidNumList.append(0)

        numTrades = np.nansum(bidNumList[-self.__sLag:])
        tickTradeNum = np.nansum(bidNumList[-self.__lag:])
        if tickTradeNum > 1e-4:
            factorValue = numTrades / tickTradeNum
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)

