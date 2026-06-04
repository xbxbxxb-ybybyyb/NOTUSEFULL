from System.Factor import Factor
import numpy as np
from scipy.signal import detrend


class FactorAskDisDetrend(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__smlag = self._getParameter("SmoothLag")
        self.__ask_vwap = self._getFactor(
            {
                "ClassName": "AskVwap"
            }
        )
        self._addIntermediate("ask_distance", [])

    def calculate(self):
        ask_price = self._getLastTickData("AskPrice")[0]
        ask_price_adjust = self.__ask_vwap.getLastFactorValue()
        ask_distance_list = self.getIntermediate("ask_distance")
        ask_distance_list.append(ask_price_adjust - ask_price)        
        ask_price_adjust_fft = detrend(np.array(ask_distance_list[-self.__lag:]))
        factor_value = ask_price_adjust_fft[-self.__smlag:].mean() * 1000
        
        if np.isnan(factor_value):
            factor_value = 0
        self._addFactorValue(factor_value)
