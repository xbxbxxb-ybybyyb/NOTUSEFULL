from System.Factor import Factor
import numpy as np


class TransLowPrice(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__dir = self._getParameter("Direction")

    def calculate(self):
        transaction = self._getLastTickData("Transactions")
        if transaction is not None:
            flag = self._getTransactionData("BSFlag", transaction)
            dealp = self._getTransactionData("Price", transaction)
            if self.__dir == "Bid":
                dealp_sub = dealp[flag == 1]
            elif self.__dir == "Ask":
                dealp_sub = dealp[flag == 2]
            else:
                dealp_sub = dealp
            if len(dealp_sub) > 0:
                factorValue = np.nanmin(dealp_sub)
            else:
                factorValue = np.nan
        else:
            factorValue = np.nan

        self._addFactorValue(factorValue)
