from System.Factor import Factor
import numpy as np


class FactorVolStrong(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag1 = self._getParameter("Lag1")
        self.__lag2 = self._getParameter("Lag2")

        self._addIntermediate("AmtPressureList", [])

    def calculate(self):
        # lag1 > lag2
        amtPressureList = self.getIntermediate("AmtPressureList")
        vol_list = self._getLastNTickData("Volume", self.__lag1)
        vol_ratio = np.nanmean(vol_list[-self.__lag2:]) / np.nanmean(vol_list) if np.nanmean(vol_list) != 0 else 1.

        bid_vol = self._getLastTickData("BidVolume")
        ask_vol = self._getLastTickData("AskVolume")
        bid_price = self._getLastTickData("BidPrice")
        ask_price = self._getLastTickData("AskPrice")

        bid_amt = bid_vol * bid_price
        ask_amt = ask_vol * ask_price
        adjust_ratio = np.arange(0.1 * len(bid_vol), 0, -0.1)
        bid_amt_sum = np.nansum(bid_amt * adjust_ratio)
        ask_amt_sum = np.nansum(ask_amt * adjust_ratio)
        amtPressureList.append(bid_amt_sum / ask_amt_sum if ask_amt_sum != 0 else 0.)

        amt_pressure_list = amtPressureList[-self.__lag1:]
        if np.nanmean(amt_pressure_list) != 0:
            amt_pressure = np.nanmean(amt_pressure_list[-self.__lag2:]) / np.nanmean(amt_pressure_list)
        else:
            amt_pressure = 1.
        factor_value = vol_ratio * amt_pressure
        if np.isnan(factor_value):
            factor_value = 0.

        self._addFactorValue(factor_value)
