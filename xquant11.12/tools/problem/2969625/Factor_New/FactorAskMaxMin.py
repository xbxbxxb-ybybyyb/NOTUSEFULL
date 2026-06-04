from System.Factor import Factor
import numpy as np


class FactorAskMaxMin(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__ask_vwap = self._getFactor(
            {
                "ClassName": "AskVwap"
            }
        )

    def calculate(self):
        ask_price_list = self.__ask_vwap.getFactorValueList()[-self.__lag:][::-1]
        ask_price_max = np.nanmax(ask_price_list)
        ask_price_min = np.nanmin(ask_price_list)
        max_pos = np.argmax(ask_price_list)
        min_pos = np.argmin(ask_price_list)

        if max_pos > min_pos and ask_price_min > 1e-6:
            factor_value = (ask_price_max / ask_price_min - 1) * 1000
        elif max_pos < min_pos and ask_price_max > 1e-6:
            factor_value = (ask_price_min / ask_price_max - 1) * 1000
        else:
            factor_value = 0

        self._addFactorValue(factor_value)
