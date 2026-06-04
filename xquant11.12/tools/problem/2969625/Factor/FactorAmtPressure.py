from System.Factor import Factor
import numpy as np


class FactorAmtPressure(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("amt_pressure", [])

    def calculate(self):
        amt_pressure = self.getIntermediate("amt_pressure")
        bid_vol = self._getLastTickData("BidVolume")
        ask_vol = self._getLastTickData("AskVolume")
        bid_price = self._getLastTickData("BidPrice")
        ask_price = self._getLastTickData("AskPrice")

        bid_amt = bid_vol * bid_price
        ask_amt = ask_vol * ask_price
        adjust_ratio = np.arange(0.1 * len(bid_vol), 0, -0.1)
        bid_amt_sum = np.nansum(bid_amt * adjust_ratio)
        ask_amt_sum = np.nansum(ask_amt * adjust_ratio)
        amt_pressure.append(bid_amt_sum / ask_amt_sum if ask_amt_sum != 0 else 0)
        amt_pressure_slice = amt_pressure[-self.__lag:]
        factor_value = np.nanmean(amt_pressure_slice)
        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)
