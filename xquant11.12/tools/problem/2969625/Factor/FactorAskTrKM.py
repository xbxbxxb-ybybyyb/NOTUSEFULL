from System.Factor import Factor
import numpy as np


class FactorAskTrKM(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("TransactionsAskVolumeArray", [])

    def calculate(self):
        transactionsAskVolumeArray = self.getIntermediate("TransactionsAskVolumeArray")
        transactions = self._getLastTickData("Transactions")

        if transactions is not None:
            bsFlag = self._getTransactionData("BSFlag", transactions)
            volume = self._getTransactionData("Volume", transactions)
            transactionsAskVolumeArray.append(np.nansum(volume[bsFlag == 2]))
        else:
            transactionsAskVolumeArray.append(0)

        L = min(len(transactionsAskVolumeArray), self.__lag)
        localTrAskVolumeArray = transactionsAskVolumeArray[-L:]

        if L < 5:
            if len(self.getFactorValueList()) == 0:
                factorValue = 0
            else:
                factorValue = self.getLastFactorValue()
        else:
            factorValue = -np.corrcoef(np.arange(len(localTrAskVolumeArray)), localTrAskVolumeArray)[0][1]
            if np.isnan(factorValue):
                factorValue = 0

        self._addFactorValue(factorValue)
