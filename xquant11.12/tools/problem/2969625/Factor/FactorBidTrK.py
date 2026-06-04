from System.Factor import Factor
import numpy as np


class FactorBidTrK(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("TransactionsBidVolumeArray", [])

    def calculate(self):
        transactionsBidVolumeArray = self.getIntermediate("TransactionsBidVolumeArray")
        transactions = self._getLastTickData("Transactions")

        if transactions is not None:
            bsFlag = self._getTransactionData("BSFlag", transactions)
            volume = self._getTransactionData("Volume", transactions)
            transactionsBidVolumeArray.append(np.nansum(volume[bsFlag == 1]))
        else:
            transactionsBidVolumeArray.append(0)

        L = min(len(transactionsBidVolumeArray), self.__lag)
        if L < 5:
            if len(self.getFactorValueList()) == 0:
                factorValue = 0
            else:
                factorValue = self.getLastFactorValue()
        else:
            factorValue = self.__get_regression_params(np.arange(L), transactionsBidVolumeArray[-L:])[1] / 100

        self._addFactorValue(factorValue)

    @staticmethod
    def __get_regression_params(x, y):
        x, y = np.array(x), np.array(y)
        x_ = x[~(np.isnan(x) | np.isnan(y))]
        y_ = y[~(np.isnan(x) | np.isnan(y))]
        if len(x_) < 3 or len(x_) / len(x) < 0.5:
            alpha, beta = 0, 0
        else:
            beta = (np.sum(x_ * y_) - np.sum(x_) * np.mean(y_)) / np.var(x_) / len(x_)
            alpha = np.mean(y_) - beta * np.mean(x_)
        return alpha, beta
