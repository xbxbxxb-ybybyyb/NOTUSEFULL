from System.Factor import Factor
import numpy as np


class FactorLowRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__dLag = self._getParameter("DayLag")

    def calculate(self):
        daily_price_list = self._getLastNHistoricalDailyData("ClosePrice", self.__dLag)
        last_price_list = self._getLastNTickData("LastPrice", self.__lag)
        last_price = last_price_list[-1]
        low_price = np.nanmin(last_price_list)
        if last_price is None or low_price is None or np.abs(last_price - low_price) < 1e-6:
            factor_value = 0
        else:
            low20 = np.nanmin(daily_price_list)
            factor_value = (last_price - low20) / (last_price - low_price)

        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)
