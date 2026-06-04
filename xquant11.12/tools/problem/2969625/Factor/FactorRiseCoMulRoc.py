from System.Factor import Factor
import numpy as np


class FactorRiseCoMulRoc(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__lag_roc = self._getParameter("LagRoc")

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )

    def calculate(self):
        mid_price_list = self.__midPrice.getFactorValueList()[-self.__lag: ]
        mid_price_list = list(filter(lambda x: x is not None, mid_price_list))
        if len(mid_price_list) <= 1:
            factor_value = 0
        else:
            origin_list = mid_price_list.copy()
            mid_price_list.sort()
            if np.nanmax(origin_list) - np.nanmin(origin_list) < 1e-6:
                rise_coordination = 0
            else:
                rise_coordination = np.corrcoef(origin_list, mid_price_list)[0, 1]
            roc = mid_price_list[-1] / mid_price_list[-min(self.__lag_roc, len(mid_price_list))] - 1
            factor_value = rise_coordination * roc
        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)
