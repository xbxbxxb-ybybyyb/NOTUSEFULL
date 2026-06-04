from System.Factor import Factor
import numpy as np


class TransBidVolumeForStockGroup(Factor):

    def calculate(self):
        transactions = self._getLastTickDataForStockGroup("Transactions")
        if transactions is not None:
            factorValue = [self.__get_bid_volume(trans) for trans in transactions[0]]
        else:
            factorValue = None

        self._addFactorValue(factorValue)

    def __get_bid_volume(self, Transaction):
        if Transaction is not None:
            bsflag = self._getTransactionData("BSFlag", Transaction)
            volume = self._getTransactionData("Volume", Transaction)
            bv = np.nansum(volume[bsflag == 1])
        else:
            bv = 0
        return bv
