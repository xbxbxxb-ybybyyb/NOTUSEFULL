from System.Factor import Factor
import numpy as np


class FactorMdfPVPer(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__dLag = self._getParameter("DayLag")

    def calculate(self):

        min_price_list = self._getLastNMinuteData("ClosePrice", self.__dLag * 240)   # 需要考虑前一日停牌全为NaN情况
        min_amt_list = self._getLastNMinuteData("Amount", self.__dLag * 240)
        last_price = np.nanmean(self._getLastNTickData("LastPrice", 100))
        last_amt = np.nanmean(self._getLastNTickData("Amount", 100)) * 20
        p_price = sum(min_price_list > last_price + 1e-6) / (self.__dLag * 240)
        p_amt = sum(min_amt_list > last_amt + 1e-6) / (self.__dLag * 240)
        factor_value = p_price + p_amt
        self._addFactorValue(factor_value)
