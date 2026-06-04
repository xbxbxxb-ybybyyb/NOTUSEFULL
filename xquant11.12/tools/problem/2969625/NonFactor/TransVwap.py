from System.Factor import Factor
import numpy as np


class TransVwap(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__dir = self._getParameter("Direction")

    def calculate(self):
        transaction = self._getLastTickData("Transactions")
        if transaction is not None:
            flag = self._getTransactionData("BSFlag", transaction)
            vol = self._getTransactionData("Volume", transaction)
            dealp = self._getTransactionData("Price", transaction)
            if self.__dir == "Bid":
                vol_sub = vol[flag == 1]
                dealp_sub = dealp[flag == 1]
            elif self.__dir == "Ask":
                vol_sub = vol[flag == 2]
                dealp_sub = dealp[flag == 2]
            else:
                vol_sub = vol
                dealp_sub = dealp
            if len(dealp_sub) > 0:
                factorValue = np.dot(dealp_sub, vol_sub) / np.nansum(vol_sub)
            else:
                factorValue = np.nan
        else:
            factorValue = np.nan

        self._addFactorValue(factorValue)
