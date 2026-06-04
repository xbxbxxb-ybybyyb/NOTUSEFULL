import numpy as np
from System.Factor import Factor


class FactorPriceRatioM(Factor):
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
            if len(today_price) >= self.__avgWindow:
                a = (np.nanmean(today_price[-self.__avgWindow:]) / np.nanmean(today_price[:self.__avgWindow]))
                b = np.nanmean(split_price[-self.__avgWindow:]) / np.nanmean(split_price[:self.__avgWindow])
                c = np.nanmean(resid_price[-self.__avgWindow:]) / np.nanmean(resid_price[:self.__avgWindow])
                res = a * b * c
                res = (res - 1) * 100
            else:
                window = max(1, int(len(today_price) / 4))
                a = (np.nanmean(today_price[-window:]) / np.nanmean(today_price[:window]))
                b = np.nanmean(split_price[-window:]) / np.nanmean(split_price[:window])
                c = np.nanmean(resid_price[-window:]) / np.nanmean(resid_price[:window])
                res = a * b * c
                res = (res - 1) * 100
        else:
            res = 0
        res = res * (-1)
        self._addFactorValue(res)
