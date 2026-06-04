from System.Factor import Factor
import numpy as np


class FactorPricePer(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__dLag = self._getParameter("DayLag")

    def calculate(self):
        min_price_list = self._getLastNMinuteData("ClosePrice", self.__dLag * 240)   # 需要考虑前一日停牌全为NaN情况
        last_price = self._getLastTickData("LastPrice")
        factor_value = sum(min_price_list > last_price) / (self.__dLag * 240)

        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)
