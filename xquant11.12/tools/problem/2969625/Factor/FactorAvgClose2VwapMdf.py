from System.Factor import Factor
import numpy as np


class FactorAvgClose2VwapMdf(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.lag = self._getParameter("Lag")

    def calculate(self):
        price_list = self._getLastNTickData("LastPrice", self.lag)
        vol_list = self._getLastNTickData("Volume", self.lag)
        amt_list = self._getLastNTickData("Amount", self.lag)
        price_ave = np.nanmean(price_list)
        if np.nansum(amt_list) < 0.001 or np.nansum(vol_list) < 0.001:
            last_value = self.getLastFactorValue()
            if last_value is not None:
                factor_value = last_value
            else:
                factor_value = 0
        else:
            vwap = np.nansum(amt_list) / np.nansum(vol_list)
            factor_value = price_ave / vwap - 1 if vwap < 0.001 else 0

        self._addFactorValue(factor_value * 1000)
