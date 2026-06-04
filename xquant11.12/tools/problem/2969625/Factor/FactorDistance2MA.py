from System.Factor import Factor
import numpy as np


class FactorDistance2MA(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__dLag = self._getParameter("DayLag")

    def calculate(self):
        daily_price_list = self._getLastNHistoricalDailyData("ClosePrice", self.__dLag - 1)
        last_price = self._getLastTickData("LastPrice")
        if last_price is None:
            factor_value = 0.
        else:
            ma20 = (np.nansum(daily_price_list) + last_price) / self.__dLag
            factor_value = last_price / ma20 - 1

        if np.isnan(factor_value):
            factor_value = 0.

        self._addFactorValue(factor_value)
