
import numpy as np
from System.Factor import Factor


class FactorAskDepthTrend(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__dLag = self._getParameter("DayLag")

    def calculate(self):
        price = self._getLastTickData("AskPrice")
        if price[0] < 1e-4 or price[-1] < 1e-4:
            p0 = self._getLastTickData('MaxPrice')
            p1 = self._getLastTickData('LastPrice')
        else:
            p0, p1 = price[0], price[-1]
        askDepth = 100 * abs(p0 - p1) / p0 if p0 > 1e-4 else 0
        high_price_list, low_price_list = self._getLastNHistoricalDailyData("HighPrice", self.__dLag), self._getLastNHistoricalDailyData("LowPrice", self.__dLag)

        ceiling_price = np.nanmean(high_price_list)
        floor_price = np.nanmean(low_price_list)
        priceRatio = (p0 - floor_price) / (ceiling_price - floor_price) if (ceiling_price - floor_price) > 0.01 else 0
        high_price = self._getLastTickData('HighPrice')
        low_price = self._getLastTickData('LowPrice')
        price_scale = (high_price - low_price) / (ceiling_price - floor_price)

        factorValue = askDepth * (1 - priceRatio) * price_scale
        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)