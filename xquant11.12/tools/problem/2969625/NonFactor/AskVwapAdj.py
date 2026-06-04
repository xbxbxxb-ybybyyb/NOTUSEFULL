import numpy as np
from System.Factor import Factor


class AskVwapAdj(Factor):

    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__percentile = self._getParameter("percentile")

    def calculate(self):
        ask_vol = self._getLastTickData("AskVolume")
        ask_price = self._getLastTickData("AskPrice")
        ask_amt = ask_vol * ask_price
        ask_amt = ask_amt[ask_price < ask_price[0] * (1 + self.__percentile)]
        ask_vol = ask_vol[ask_price < ask_price[0] * (1 + self.__percentile)]
        adjust_ratio = np.arange(len(ask_amt) + 1, 1, -1) / np.sum(np.arange(len(ask_amt) + 1, 1, -1))
        ask_amt_sum = np.nansum(ask_amt * adjust_ratio)
        ask_vol_sum = np.nansum(ask_vol * adjust_ratio)
        ask_price_adjust = ask_amt_sum / ask_vol_sum if ask_vol_sum > 1e-6 else 0
        if np.isnan(ask_price_adjust):
            ask_price_adjust = 0

        self._addFactorValue(ask_price_adjust)
