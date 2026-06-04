import numpy as np
from System.Factor import Factor


class AskVwapNum(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.n = self._getParameter("n")

    def calculate(self):
        ask_vol = self._getLastTickData("AskVolume")[:self.n]
        ask_price = self._getLastTickData("AskPrice")[:self.n]
        ask_amt = ask_vol * ask_price
        adjust_ratio = np.arange(self.n, 0, -1) / sum(np.arange(self.n, 0, -1))
        ask_amt_sum = np.nansum(ask_amt * adjust_ratio)
        ask_vol_sum = np.nansum(ask_vol * adjust_ratio)
        ask_price_adjust = ask_amt_sum / ask_vol_sum if ask_vol_sum != 0 else 0
        if np.isnan(ask_price_adjust):
            ask_price_adjust = 0

        self._addFactorValue(ask_price_adjust)
