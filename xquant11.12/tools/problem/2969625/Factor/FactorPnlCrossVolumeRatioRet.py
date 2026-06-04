import numpy as np
from System.Factor import Factor


class FactorPnlCrossVolumeRatioRet(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__dlag = self._getParameter("DayLag")
        self.__window = self._getParameter("Window")
        self.__iwindow = self._getParameter("IndexWindow")
        self.__indexName = self._getParameter("IndexName")

    def calculate(self):
        volume = np.nanmean(self._getLastNHistoricalDailyData('Volume', self.__dlag))
        today_volume = self._getAllTodayTickData('Volume')
        volume_ratio = np.nansum(today_volume) / volume / len(today_volume) * 4730 if volume != 0 else 1

        price_ind = self._getAllTodayINFTickData(self.__indexName, 'LastPrice')
        price = self._getAllTodayTickData('LastPrice')

        if len(price_ind) > 1:
            ind_pct = (price_ind[1:] / price_ind[:-1] - 1) * 10000
            pct = (price[1:] / price[:-1] - 1) * 10000
            factorValue = (np.nanmean(pct[-self.__window:]) - np.nanmean(ind_pct[-self.__iwindow:])) * volume_ratio
        else:
            factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
