import numpy as np
from System.Factor import Factor


class BidVwapNum(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.n = self._getParameter("n")

    def calculate(self):
        bid_vol = self._getLastTickData("BidVolume")[:self.n]
        bid_price = self._getLastTickData("BidPrice")[:self.n]
        bid_amt = bid_vol * bid_price
        adjust_ratio = np.arange(self.n, 0, -1) / sum(np.arange(self.n, 0, -1))
        bid_amt_sum = np.nansum(bid_amt * adjust_ratio)
        bid_vol_sum = np.nansum(bid_vol * adjust_ratio)
        bid_price_adjust = bid_amt_sum / bid_vol_sum if bid_vol_sum != 0 else 0
        if np.isnan(bid_price_adjust):
            bid_price_adjust = 0

        self._addFactorValue(bid_price_adjust)
