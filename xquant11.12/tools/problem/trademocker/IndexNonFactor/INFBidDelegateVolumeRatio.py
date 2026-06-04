from System.Factor import Factor
import numpy as np


class INFBidDelegateVolumeRatio(Factor):

    def calculate(self):
        vol_d_g = self._getLastNHistoricalDailyDataForStockGroup("Volume", 1, isStacked=True)[0, :]
        vol_d_g[vol_d_g == 0] = np.nan
        bid_vol_g = np.array([np.nansum(each[0]) if each[0] is not None else 0.
                              for each in self._getLastTickDataForStockGroup("BidVolume")])
        bvr_g = bid_vol_g / vol_d_g
        if np.nanmean(bvr_g) > 0:
            factorValue = bvr_g / np.nanmean(bvr_g)
        else:
            factorValue = bvr_g  # 此时bvr_g为NaN或0

        self._addFactorValue(factorValue)
