from System.Factor import Factor
import numpy as np


class FactorEntrustRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag1 = self._getParameter("Lag1")
        self.__lag2 = self._getParameter("Lag2")

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )

    def calculate(self):
        mid_price_list = self.__midPrice.getFactorValueList()[-self.__lag1:]
        mid_price_list = list(filter(lambda x: x is not None, mid_price_list))
        lag = self.__lag2 if len(mid_price_list) > self.__lag2 + 4 else len(mid_price_list) - 4 if len(
            mid_price_list) > 5 else 1
        value1 = mid_price_list[-1] - mid_price_list[0]
        value2 = np.nansum(
            np.abs((np.array(mid_price_list)[lag:] - np.array(mid_price_list)[:-lag]) / len(mid_price_list)))
        factor_value = value1 / value2 if value2 != 0 else 0

        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)
