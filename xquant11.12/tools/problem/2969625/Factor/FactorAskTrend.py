from System.Factor import Factor
import numpy as np


class FactorAskTrend(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__ask_vwap = self._getFactor(
            {
                "ClassName": "AskVwap"
            }
        )
        self._addIntermediate("ask_distance", [])

    def calculate(self):
        ask_price = self._getLastTickData("AskPrice")
        ask_price_adjust = self.__ask_vwap.getLastFactorValue()
        ask_distance_list = self.getIntermediate("ask_distance")
        askd = ask_price_adjust / ask_price[0] - 1 if ask_price[0] != 0 else np.nan
        ask_distance_list.append(askd)
        ask_distance_slice = ask_distance_list[-self.__lag:]
        ask_distance_list_sorted = ask_distance_slice.copy()
        ask_distance_list_sorted.sort()
        if np.nanmax(ask_distance_slice) == np.nanmin(ask_distance_slice):
            factor_value = 0
        else:
            factor_value = np.corrcoef(ask_distance_slice, ask_distance_list_sorted)[0, 1]
        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)
