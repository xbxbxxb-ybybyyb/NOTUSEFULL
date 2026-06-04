from System.Factor import Factor
import numpy as np


class FactorMdfPricePer(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__dLag = self._getParameter("DayLag")

    def calculate(self):

        min_price_list = self._getLastNMinuteData("ClosePrice", self.__dLag * 240)   # 需要考虑前一日停牌全为NaN情况
        last_price = np.nanmean(self._getLastNTickData("LastPrice", 60))
        factor_value = sum(min_price_list > last_price + 1e-6) / (self.__dLag * 240)

        if np.isnan(factor_value):
            factor_value = 0.

        self._addFactorValue(factor_value)
