import numpy as np
from System.Factor import Factor


class FactorTransBidNumTrend(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
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

        bidNumArray = np.array(bidNumList[-self.__lag:])
        if len(np.unique(bidNumArray)) > 1:
            factorValue = np.corrcoef(bidNumArray, np.arange(len(bidNumArray)))[0, 1]
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)

