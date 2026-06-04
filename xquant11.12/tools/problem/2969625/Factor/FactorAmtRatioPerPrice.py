from System.Factor import Factor
import numpy as np


class FactorAmtRatioPerPrice(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )
        self.__lag1 = self._getParameter("Lag1")
        self.__lag2 = self._getParameter("Lag2")

    def calculate(self):
        # lag1 < lag2
        mid_price_list = self.__midPrice.getFactorValueList()[-self.__lag2: ]
        mid_price_list = list(filter(lambda x: x is not None, mid_price_list))
        amt_array1 = self._getLastNTodayTickData("Amount", self.__lag1)
        amt_array2 = self._getLastNTodayTickData("Amount", self.__lag2)
        if len(mid_price_list) <= 1 or (np.nanmean(amt_array1) < 1e-6) or (np.nanmean(amt_array2) < 1e-6) or (mid_price_list[0] < 0.01):
            factor_value = 0
        else:
            if (np.nanmean(amt_array1) < 1e-6) or (np.nanmean(amt_array2) < 1e-6):
                factor_value = 0
            else:
                amt_ratio = np.nanmean(amt_array1) / np.nanmean(amt_array2)
                factor_value = (mid_price_list[-1] / mid_price_list[0] - 1) / amt_ratio
        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)
