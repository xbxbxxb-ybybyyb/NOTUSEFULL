import numpy as np
from System.Factor import Factor


class AskVwap(Factor):

    def calculate(self):
        ask_vol = self._getLastTickData("AskVolume")
        ask_price = self._getLastTickData("AskPrice")
        ask_amt = ask_vol * ask_price
        adjust_ratio = np.arange(len(ask_vol), 0, -1) / sum(np.arange(len(ask_vol), 0, -1))
        ask_amt_sum = np.nansum(ask_amt * adjust_ratio)
        ask_vol_sum = np.nansum(ask_vol * adjust_ratio)
        ask_price_adjust = ask_amt_sum / ask_vol_sum if ask_vol_sum > 1e-6 else 0
        if np.isnan(ask_price_adjust):
            ask_price_adjust = 0

        self._addFactorValue(ask_price_adjust)
