from System.Factor import Factor
import numpy as np


class INFTransAskVolumeRank(Factor):

    def calculate(self):
        trans_g = self._getLastTickDataForStockGroup("Transactions")

        bv_g = [self.__get_trans_volume(each[0], "Bid") for each in trans_g]
        av_g = [self.__get_trans_volume(each[0], "Ask") for each in trans_g]
        avr_g = np.divide(av_g, np.add(bv_g, av_g))  # 如果除0是NaN
        np.place(avr_g, np.isnan(avr_g), 0.)

        factorValue = [np.nansum(avr_g < each) / len(avr_g) for each in avr_g]

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
            tv = 0
        return tv
