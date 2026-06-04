from System.Factor import Factor
import numpy as np


class FactorAskDistanceMulRet(Factor):
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
        ask_price_adjust = self.__ask_vwap.getFactorValueList()[-self.__lag:]
        ask_distance = self.getIntermediate("ask_distance")

        askd = ask_price_adjust[-1] / ask_price[0] - 1 if ask_price[0] != 0 else np.nan
        ask_distance.append(askd)
        ask_distance_sub = ask_distance[-self.__lag:]
        if ask_price_adjust[0] != 0:
            factor_value = np.nanmean(ask_distance_sub) * (ask_price[0] / ask_price_adjust[0] - 1) * 1000000
        else:
            lastv = self.getLastFactorValue()
            if lastv is not None:
                factor_value = lastv
            else:
                factor_value = 0

        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)

