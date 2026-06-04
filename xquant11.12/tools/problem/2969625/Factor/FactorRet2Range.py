from System.Factor import Factor
import numpy as np


class FactorRet2Range(Factor):
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
        mid_price_list = list(filter(lambda x: x is not None and x != 0, mid_price_list))
        lag = min(self.__lag2, len(mid_price_list) - 1)
        ret = np.array(mid_price_list[lag:]) / np.array(mid_price_list[:-lag]) - 1

        factor_value = 0
        if len(mid_price_list) > 0:
            ret_range = np.nanmax(mid_price_list) / np.nanmin(mid_price_list) - 1
            if ret_range != 0:
                factor_value = np.nanmean(ret) / ret_range
        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)
