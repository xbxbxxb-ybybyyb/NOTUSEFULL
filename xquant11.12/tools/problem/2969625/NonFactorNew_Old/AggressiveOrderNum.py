import numpy as np
from System.Factor import Factor


class AggressiveOrderNum(Factor):
    def calculate(self):
        buyAggressiveNum = 0
        sellAggressiveNum = 0
        buyPassiveNum = 0
        sellPassiveNum = 0

        transactions = self._getLastTickData("Transactions")
        if transactions is not None:
            bsFlag = self._getTransactionData("BSFlag", transactions)
            buyAggressiveNum = np.unique(self._getTransactionData("BidOrder", transactions)[bsFlag == 1]).shape[0]
            sellAggressiveNum = np.unique(self._getTransactionData("AskOrder", transactions)[bsFlag == 2]).shape[0]
            buyPassiveNum = np.unique(self._getTransactionData("AskOrder", transactions)[bsFlag == 1]).shape[0]
            sellPassiveNum = np.unique(self._getTransactionData("BidOrder", transactions)[bsFlag == 2]).shape[0]

        self._addFactorValue([buyAggressiveNum, sellAggressiveNum, buyPassiveNum, sellPassiveNum])
