from System.Factor import Factor
import numpy as np
from scipy import stats


class FactorMidPriceSkew(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )

    def calculate(self):
        mid_price_list = self.__midPrice.getFactorValueList()[-self.__lag:]
        mid_price_list = list(filter(lambda x: x is not None, mid_price_list))
        if np.nanmax(mid_price_list) - np.nanmin(mid_price_list) < 1e-6:
            factor_value = 0
        else:
            factor_value = stats.skew(np.array(mid_price_list))
        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)
