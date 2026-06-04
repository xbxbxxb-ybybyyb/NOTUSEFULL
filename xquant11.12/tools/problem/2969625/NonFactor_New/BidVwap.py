import numpy as np
from System.Factor import Factor


class BidVwap(Factor):

    def calculate(self):
        bid_vol = self._getLastTickData("BidVolume")
        bid_price = self._getLastTickData("BidPrice")
        bid_amt = bid_vol * bid_price
        adjust_ratio = np.arange(len(bid_vol), 0, -1.) / sum(np.arange(len(bid_vol), 0, -1.))
        bid_amt_sum = np.nansum(bid_amt * adjust_ratio)
        bid_vol_sum = np.nansum(bid_vol * adjust_ratio)
        if bid_vol_sum > 1e-6:
            bid_price_adjust = bid_amt_sum / bid_vol_sum
        else:
            bid_price_adjust = self._getLastTickData("MinPrice")

        self._addFactorValue(bid_price_adjust)
