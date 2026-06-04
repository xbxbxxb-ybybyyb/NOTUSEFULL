from System.Factor import Factor
import numpy as np


class FactorMdfPricePer2(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__dLag = self._getParameter("DayLag")

    def calculate(self):

        min_price_list = self._getLastNMinuteData("ClosePrice", self.__dLag * 240)   # 需要考虑前一日停牌全为NaN情况
        min_price_list = np.array([x for x in min_price_list if x is not None and not np.isnan(x)])
        last_price_list = self._getLastNTickData("LastPrice", 200)
        last_price_list = np.array([x for x in last_price_list if x is not None and not np.isnan(x)])
        last_price = np.nanmean(last_price_list)
        p1 = sum(min_price_list > last_price + 1e-6) / len(min_price_list) if len(min_price_list) != 0 else 0.5
        p2 = sum(last_price_list > last_price + 1e-6) / len(last_price_list) if len(last_price_list) != 0 else 0.5
        factor_value = p1 + p2
        self._addFactorValue(factor_value)
