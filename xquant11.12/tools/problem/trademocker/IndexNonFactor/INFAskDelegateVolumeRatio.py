from System.Factor import Factor
import numpy as np


class INFAskDelegateVolumeRatio(Factor):

    def calculate(self):
        vol_d_g = self._getLastNHistoricalDailyDataForStockGroup("Volume", 1, isStacked=True)[0, :]
        vol_d_g[vol_d_g == 0] = np.nan
        ask_vol_g = np.array([np.nansum(each[0]) if each[0] is not None else 0.
                              for each in self._getLastTickDataForStockGroup("AskVolume")])
        avr_g = ask_vol_g / vol_d_g
        if np.nanmean(avr_g) > 0:
            factorValue = avr_g / np.nanmean(avr_g)
        else:
            factorValue = avr_g  # 此时avr_g为NaN或0

        self._addFactorValue(factorValue)
