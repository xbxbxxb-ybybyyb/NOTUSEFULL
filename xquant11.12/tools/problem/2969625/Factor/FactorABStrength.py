from System.Factor import Factor
import numpy as np


class FactorABStrength(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag1 = self._getParameter("Lag1")
        self.__lag2 = self._getParameter("Lag2")

        self._addIntermediate("ab_strength", [])

    def calculate(self):
        # lag1 > lag2
        ab_strength = self.getIntermediate("ab_strength")
        bid_vol = self._getLastTickData("BidVolume")
        ask_vol = self._getLastTickData("AskVolume")
        bid_price = self._getLastTickData("BidPrice")
        ask_price = self._getLastTickData("AskPrice")

        bid_amt = bid_vol * bid_price
        ask_amt = ask_vol * ask_price
        adjust_ratio = np.arange(0.1 * len(bid_vol), 0, -0.1)
        bid_amt_sum = np.nansum(bid_amt * adjust_ratio)
        ask_amt_sum = np.nansum(ask_amt * adjust_ratio)
        bid_vol_sum = np.nansum(bid_vol * adjust_ratio)
        ask_vol_sum = np.nansum(ask_vol * adjust_ratio)
        bid_price = bid_amt_sum / bid_vol_sum if bid_vol_sum != 0 else 0.  # 涨跌停处理
        ask_price = ask_amt_sum / ask_vol_sum if ask_vol_sum != 0 else 0.
        ab_strength.append(bid_price / ask_price if ask_price != 0 else 0.)
        ab_strength_slice = ab_strength[-self.__lag1:]
        if np.nanmean(ab_strength_slice) > 1e-6:
            amt_pressure = np.nanmean(ab_strength_slice[-self.__lag2:]) / np.nanmean(ab_strength_slice)
            factor_value = (amt_pressure - 1) * 1000
        else:
            factor_value = 0.

        if np.isnan(factor_value):
            factor_value = 0.

        self._addFactorValue(factor_value)
