import numpy as np
from System.Factor import Factor


class FactorPriceVolumeRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("WindowShort")
        self.__longWindow = self._getParameter("WindowLong")

    def calculate(self):
        today_price = self._getAllTodayTickData('LastPrice')[-self.__window:]
        yestoday_price = self._getAllHistoricalTickData('LastPrice')
        today_volume = self._getAllTodayTickData('Volume')
        yestoday_volume = self._getAllHistoricalTickData('Volume')
        split_volume = yestoday_volume[:len(today_volume)]
        resid_price = yestoday_price[len(today_volume):(len(today_volume) + self.__window)]
        if len(resid_price) > 1:
            a = np.nansum(today_volume[-self.__longWindow:])/np.nansum(split_volume[-self.__longWindow:])
            b = (np.nanmean(resid_price[-5:]) / np.nanmean(resid_price[:5]) - 1) * 100
            c = (np.nanmean(today_price[-5:]) / np.nanmean(today_price[:5]) - 1) * 100
            res = a * b - c
        else:
            res = 0
        if np.isnan(res) or np.isinf(res):
            res = 0

        self._addFactorValue(res)
