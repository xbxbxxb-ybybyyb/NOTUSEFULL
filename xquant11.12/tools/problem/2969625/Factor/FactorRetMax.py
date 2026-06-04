from System.Factor import Factor
import numpy as np
import pandas as pd


class FactorRetMax(Factor):
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
        # lag1 > lag2
        mid_price_list = self.__midPrice.getFactorValueList()[-self.__lag1:]
        mid_price_list = list(filter(lambda x: x is not None, mid_price_list))
        lag = min(self.__lag2, len(mid_price_list) - 1)
        ret = np.array(mid_price_list[lag:]) / np.array(mid_price_list[:-lag]) - 1
        if len(ret) == 0:
            factor_value = 0
        else:
            factor_value = np.nanmax(ret)
            if np.isnan(factor_value):
                factor_value = 0

        self._addFactorValue(factor_value)
