import numpy as np
from System.Factor import Factor


class FactorPredPrice(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")
        self.__avgWindow = self._getParameter("AvgWindow")

    def calculate(self):
        today_price = self._getAllTodayTickData('LastPrice')
        yestoday_price = self._getAllHistoricalTickData('LastPrice')
        split_price = yestoday_price[:len(today_price)]
        resid_price = yestoday_price[len(today_price):(len(today_price) + self.__window)]
        resid_price = resid_price[~np.isnan(resid_price)]
        if len(resid_price) > 1:
            a = (np.nanmean(today_price[-self.__avgWindow:]) / np.nanmean(today_price[:self.__avgWindow]))
            b = np.nanmean(split_price[-self.__avgWindow:]) / np.nanmean(split_price[:self.__avgWindow])
            c = np.nanmean(resid_price[-self.__avgWindow:]) / np.nanmean(resid_price[:self.__avgWindow])
            res = (a / b) * c
            res = (res - 1) * 100
        else:
            res = 0
        if np.isnan(res) or np.isinf(res):
            res = 0

        self._addFactorValue(res)
