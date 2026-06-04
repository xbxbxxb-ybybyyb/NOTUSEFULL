from System.Factor import Factor
import numpy as np


class FactorSellDistanceStd(Factor):
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
        ask_distance = self.getIntermediate("ask_distance")
        askd = ask_price_adjust / ask_price[0] - 1 if ask_price[0] != 0 else np.nan
        ask_distance.append(askd)
        ask_distance_sub = ask_distance[-self.__lag:]
        factor_value = np.nanstd(ask_distance_sub) * 1000
        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)
