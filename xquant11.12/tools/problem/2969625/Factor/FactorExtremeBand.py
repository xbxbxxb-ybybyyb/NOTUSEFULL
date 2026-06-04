# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/03/15
from System.Factor import Factor
import numpy as np


class FactorExtremeBand(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__scale = self._getParameter("Scale")

        self.__band_up = None
        self.__band_down = None

    def calculate(self):
        pclosep = self._getLastNHistoricalDailyData("PreviousClose", 1)[0]
        if np.isnan(pclosep):  # 上市第一天不计算
            factorValue = 0.
        else:
            lastp = self._getLastTickData("LastPrice")

            high_band = pclosep * (1 + self.__band_up * self.__scale)
            low_band = pclosep * (1 + self.__band_down * self.__scale)

            if lastp > high_band:
                factorValue = -(lastp / high_band - 1) * 1e2
            elif lastp < low_band:
                factorValue = -(lastp / low_band - 1) * 1e2
            else:
                factorValue = (lastp / pclosep - 1) / 1e2

        self._addFactorValue(factorValue)

    def _onNewDay(self):
        pclosep = self._getLastNHistoricalDailyData("PreviousClose", self.__lag)
        highp = self._getLastNHistoricalDailyData("HighPrice", self.__lag)
        lowp = self._getLastNHistoricalDailyData("LowPrice", self.__lag)
        band_up = np.nanmean(np.clip(highp / pclosep - 1, a_min=0, a_max=np.inf))
        band_down = np.nanmean(np.clip(lowp / pclosep - 1, a_min=-np.inf, a_max=0))
        if band_up > 0:
            self.__band_up = band_up
        else:
            self.__band_up = 0.07
        if band_down < 0:
            self.__band_down = band_down
        else:
            self.__band_down = -0.07
