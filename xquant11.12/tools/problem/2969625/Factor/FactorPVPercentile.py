from System.Factor import Factor
import numpy as np


class FactorPVPercentile(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag1 = self._getParameter("Lag1")
        self.__lag2 = self._getParameter("Lag2")

    def calculate(self):
        # lag1 > lag2
        last_price_list = self._getLastNTickData("LastPrice", self.__lag1)
        last_price_list = list(filter(lambda x: x is not None, last_price_list))
        lag = self.__lag2 if len(last_price_list) > self.__lag2 + 4 else len(last_price_list) - 4 if len(last_price_list) > 5 else 1
        ret = np.array(last_price_list[lag:]) / np.array(last_price_list[:-lag]) - 1
        if len(ret) == 0:
            ret_percentile = 0
        else:
            ret_percentile = sum(ret[-1] > np.array(ret)) / len(ret)

        vol_list = self._getLastNTickData("Volume", self.__lag1)
        vol_list = list(filter(lambda x: x is not None, vol_list))
        vol_sum = [sum(vol_list[i:(i + lag)]) for i in range(0, len(vol_list) - lag)]
        if len(vol_sum) == 0:
            vol_percentile = 0
        else:
            vol_percentile = sum(vol_sum[-1] > np.array(vol_sum)) / len(vol_sum)

        factor_value = ret_percentile * vol_percentile
        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)
