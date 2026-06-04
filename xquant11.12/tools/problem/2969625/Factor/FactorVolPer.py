from System.Factor import Factor
import numpy as np


class FactorVolPer(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__dLag = self._getParameter("DayLag")

    def calculate(self):

        min_vol_list = self._getLastNMinuteData("Volume", self.__dLag * 240)  # 需要考虑上一交易日停牌，全为NaN情况
        timeList = self._getLastNMinuteData("Time", self.__dLag * 240)

        last_vol = np.nansum(self._getLastNTickData("Volume", 60)) / 3
        factor_value = sum(min_vol_list > last_vol) / (self.__dLag * 240)
        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)
