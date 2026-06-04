from System.Factor import Factor
import numpy as np


class FactorHighRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__dLag = self._getParameter("DayLag")

    def calculate(self):
        daily_price_list = self._getLastNHistoricalDailyData("ClosePrice", self.__dLag)
        last_price_list = self._getLastNTickData("LastPrice", self.__lag)
        last_price = last_price_list[-1]
        high_price = np.nanmax(last_price_list)
        if np.abs(high_price - last_price) < 1e-6:
            factor_value = 0.
        else:
            high20 = np.nanmax(daily_price_list)
            factor_value = (high20 - last_price) / (high_price - last_price)

        if np.isnan(factor_value):
            factor_value = 0.

        self._addFactorValue(factor_value)
