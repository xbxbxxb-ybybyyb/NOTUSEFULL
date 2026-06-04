from System.Factor import Factor
import numpy as np


class FactorBidTrKM(Factor):
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
        localTrBidVolumeArray = transactionsBidVolumeArray[-L:]

        if L < 5:
            if len(self.getFactorValueList()) == 0:
                factorValue = 0
            else:
                factorValue = self.getLastFactorValue()
        else:
            factorValue = np.corrcoef(np.arange(len(localTrBidVolumeArray)), localTrBidVolumeArray)[0][1]
            if np.isnan(factorValue):
                factorValue = 0

        self._addFactorValue(factorValue)
