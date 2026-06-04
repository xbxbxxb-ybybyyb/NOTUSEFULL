from System.Factor import Factor
import numpy as np


class FactorAskDisMax(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__lag2 = self._getParameter("Lag2")
        self.__ask_vwap = self._getFactor(
            {
                "ClassName": "AskVwap"
            }
        )
        self._addIntermediate("ask_max", [])

    def calculate(self):
        ask_price_list = self.__ask_vwap.getFactorValueList()[-self.__lag:]
        ask_price_max = np.nanmax(ask_price_list)

        if ask_price_max > 1e-6:
            ask_max_value = (ask_price_list[-1] / ask_price_max - 1) * 1000
        else:
            ask_max_value = 0

        ask_max_list = self.getIntermediate("ask_max")
        ask_max_list.append(ask_max_value)

        factor_value = np.nanmean(ask_max_list[-self.__lag2:])

        if np.isnan(factor_value):
            factor_value = 0
        self._addFactorValue(factor_value)
