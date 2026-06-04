from System.Factor import Factor
import numpy as np


class BidAmtPerTrade(Factor):
    def calculate(self):
        transaction = self._getLastTickData('Transactions')
        if transaction is None:
            value = 0
        else:
            value = self.__getBidAmt(transaction)
        self._addFactorValue(value)

    def __getBidAmt(self, transaction):
        flag = self._getTransactionData("BSFlag", transaction)
        Time = self._getTransactionData("Timestamp", transaction)
        amt = self._getTransactionData("Amount", transaction)
        if (flag == 1).sum() == 0:
            return 0
        else:
            weight_amt = np.power(np.e, (Time * 1000 - Time[-1] * 1000) / 1000) * amt
            ask_amt_per_trans = (weight_amt[flag == 1]).sum() / (flag == 1).sum()
            return ask_amt_per_trans
