import numpy as np
from System.Factor import Factor


class AggressiveOrderQty(Factor):
    def calculate(self):
        buyAggressiveQty = 0
        sellAggressiveQty = 0
        buyPassiveQty = 0
        sellPassiveQty = 0
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

            buyQty = np.sum(self._getTransactionData("Volume", transactions)[bsFlag == 1])
            sellQty = np.sum(self._getTransactionData("Volume", transactions)[bsFlag == 2])

            buyAggressiveQty = buyQty / buyAggressiveNum if buyAggressiveNum > 0 else 0
            sellAggressiveQty = sellQty / sellAggressiveNum if sellAggressiveNum > 0 else 0
            buyPassiveQty = buyQty / buyPassiveNum if buyPassiveNum > 0 else 0
            sellPassiveQty = sellQty / sellPassiveNum if sellPassiveNum > 0 else 0

        self._addFactorValue([buyAggressiveQty, sellAggressiveQty, buyPassiveQty, sellPassiveQty, buyAggressiveNum, sellAggressiveNum, buyPassiveNum, sellPassiveNum])
