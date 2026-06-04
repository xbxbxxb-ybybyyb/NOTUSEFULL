import numpy as np
from System.Factor import Factor


class BidVwapAdj(Factor):

    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__percentile = self._getParameter("percentile")

    def calculate(self):
        bid_vol = self._getLastTickData("BidVolume")
        bid_price = self._getLastTickData("BidPrice")
        bid_amt = bid_vol * bid_price
        bid_amt = bid_amt[bid_price > bid_price[0] * (1 - self.__percentile)]
        bid_vol = bid_vol[bid_price > bid_price[0] * (1 - self.__percentile)]
        adjust_ratio = np.arange(len(bid_amt) + 1, 1, -1) / np.sum(np.arange(len(bid_amt) + 1, 1, -1))
        bid_amt_sum = np.nansum(bid_amt * adjust_ratio)
        bid_vol_sum = np.nansum(bid_vol * adjust_ratio)
        if bid_vol_sum > 1e-6:
            bid_price_adjust = bid_amt_sum / bid_vol_sum
        else:
            bid_price_adjust = self._getLastTickData("MinPrice")

        self._addFactorValue(bid_price_adjust)
