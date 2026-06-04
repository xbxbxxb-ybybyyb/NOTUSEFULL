import numpy as np
from System.Factor import Factor


class FactorTransBidChipX(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):
        transactionData = [x for x in self._getLastNTickData("Transactions", self.__lag) if x is not None]
        transaction = np.concatenate(transactionData, axis=0) if len(transactionData) > 0 else None

        chipDict = dict()

        if transaction is not None:
            bsFlag = self._getTransactionData("BSFlag", transaction)
            BidOrder = self._getTransactionData("BidOrder", transaction)
            VolumeData = self._getTransactionData("Volume", transaction)
            BidOrder = BidOrder[bsFlag == 1]
            VolumeData = VolumeData[bsFlag == 1]

            for i in range(BidOrder.shape[0]):
                bidOrder = BidOrder[i]
                volume = VolumeData[i]
                if bidOrder in chipDict:
                    chipDict[bidOrder] += volume
                else:
                    chipDict[bidOrder] = volume

        chipVolume = np.array(list(chipDict.values()))

        if len(chipVolume) > 2:
            factorValue = self.__compute_skew(chipVolume)
        else:
            lastFactorValue = self.getLastFactorValue()
            if lastFactorValue is not None:
                factorValue = lastFactorValue
            else:
                factorValue = 3.

        self._addFactorValue(factorValue)

    @staticmethod
    def __compute_skew(arr):
        if len(arr) < 2:
            return 0
        else:
            arr_mean = np.nanmean(arr)
            arr_std = np.nanstd(arr)
            three = np.nanmean((arr - arr_mean)**3)
            skew = three / arr_std**3 if arr_std >1e-6 else 0
            return skew







