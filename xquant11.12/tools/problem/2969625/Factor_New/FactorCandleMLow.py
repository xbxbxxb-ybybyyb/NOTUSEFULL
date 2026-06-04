# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/05/05
from System.Factor import Factor
import numpy as np


class FactorCandleMLow(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lags = self._getParameter("Lags")

    def calculate(self):
        lastp = self._getLastNTickData("LastPrice", int(max(self.__lags)))
        pm = [np.nanmin(lastp[-lag:]) for lag in self.__lags]
        factorValue = - (pm[0] / np.nanmean(pm[1:]) - 1) * 100

        self._addFactorValue(factorValue)
