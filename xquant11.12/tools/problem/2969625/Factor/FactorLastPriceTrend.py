from System.Factor import Factor
import numpy as np


class FactorLastPriceTrend(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")

        self.__dLag = self._getParameter("DayLag")

    def calculate(self):
        daily_price_list = self._getLastNHistoricalDailyData("ClosePrice", self.__dLag)
        price = self._getLastNTickData('LastPrice', self.__window)
        avg_price = np.nanmean(price)
        ceiling_price = np.nanmax(daily_price_list)
        floor_price = np.nanmin(daily_price_list)
        price_ratio = (avg_price - floor_price) / (ceiling_price - floor_price) if (ceiling_price - floor_price) > 0.01 else 0
        high_price = self._getLastTickData('HighPrice')
        low_price = self._getLastTickData('LowPrice')
        price_scale = (high_price - low_price) / (ceiling_price - floor_price)

        factorValue = (1-price_ratio) * price_scale * 10

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)