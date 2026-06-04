from System.Factor import Factor
import numpy as np


class FactorPriceVolumeRatioScale(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")

        self.__dLag = self._getParameter("DayLag")

    def calculate(self):
        price = self._getLastNTickData('LastPrice', self.__window)
        high_price = np.nanmax(price)
        low_price = np.nanmin(price)
        ceiling_price = self._getLastTickData('HighPrice')
        floor_price = self._getLastTickData('LowPrice')
        last_price = self._getLastTickData('LastPrice')
        price_ratio = (last_price - floor_price) / (ceiling_price - floor_price)

        # avg_price = np.nanmean(price)
        # ceiling_price = np.nanmax(self._getLastNHistoricalDailyData("HighPrice", self.__dLag))
        # floor_price = np.nanmin(self._getLastNHistoricalDailyData("LowPrice", self.__dLag))
        # price_ratio = (avg_price - floor_price) / (ceiling_price - floor_price) if (ceiling_price - floor_price) > 0.01 else 0
        # high_price = self._getLastTickData('HighPrice')
        # low_price = self._getLastTickData('LowPrice')
        price_scale = (high_price - low_price) / (ceiling_price - floor_price)

        daily_volume_list = self._getLastNHistoricalDailyData("Volume", self.__dLag)
        volume = self._getLastNTickData('Volume', self.__window)
        avg_volume = np.nanmean(volume)
        ceiling_volume = np.nanmax(daily_volume_list)
        floor_volume = np.nanmin(daily_volume_list)
        volume_ratio = (avg_volume * 4730 - floor_volume) / (ceiling_volume - floor_volume)

        factorValue = - price_ratio * price_scale * volume_ratio

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)