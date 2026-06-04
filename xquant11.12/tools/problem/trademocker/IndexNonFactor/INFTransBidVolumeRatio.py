from System.Factor import Factor
import numpy as np


class INFTransBidVolumeRatio(Factor):

    def calculate(self):
        trans_g = self._getLastTickDataForStockGroup("Transactions")

        bv_g = [self.__get_trans_volume(each[0], "Bid") for each in trans_g]
        av_g = [self.__get_trans_volume(each[0], "Ask") for each in trans_g]
        v_g = np.nansum(bv_g) + np.nansum(av_g)
        if v_g > 0.01:
            factorValue = np.nansum(bv_g) / v_g
        else:
            factorValue = 0.

        self._addFactorValue(factorValue)

    def __get_trans_volume(self, Transaction, direction):
        if Transaction is not None:
            bsflag = self._getTransactionData("BSFlag", Transaction)
            volume = self._getTransactionData("Volume", Transaction)
            if direction == "Bid":
                tv = np.nansum(volume[bsflag == 1])
            else:
                tv = np.nansum(volume[bsflag == 2])
        else:
            tv = 0.
        return tv
