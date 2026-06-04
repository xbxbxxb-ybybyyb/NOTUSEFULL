from System.Factor import Factor
import numpy as np
from scipy.signal import detrend


class FactorAskDetrend(Factor):
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
        ask_distance_list.append(ask_price_adjust / ask_price[0] - 1 if ask_price[0] > 1e-7 else 0.)

        sub_ask_distance_array = np.array(ask_distance_list[-self.__lag:])
        np.place(sub_ask_distance_array, np.isnan(sub_ask_distance_array), 0.)

        ask_distance_detrend = detrend(sub_ask_distance_array)
        ask_distance_detrend_sorted = ask_distance_detrend.copy()
        ask_distance_detrend_sorted.sort()
        factor_value = np.corrcoef(ask_distance_detrend * 1e3, ask_distance_detrend_sorted * 1e3)[0][1]

        if np.isnan(factor_value):
            factor_value = 0.
        self._addFactorValue(factor_value)
