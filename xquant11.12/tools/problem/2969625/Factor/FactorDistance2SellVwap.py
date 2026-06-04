from System.Factor import Factor
import numpy as np


class FactorDistance2SellVwap(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__ask_vwap = self._getFactor(
            {
                "ClassName": "AskVwap"
            }
        )
        self._addIntermediate("res_value", [])

    def calculate(self):
        ask_price_adjust = self.__ask_vwap.getLastFactorValue()
        ask_price_mean = np.nanmean(self._getLastTickData("AskPrice"))
        res_value = self.getIntermediate("res_value")
        if ask_price_adjust != 0:
            res_value.append((ask_price_mean / ask_price_adjust - 1) * 1000)
        else:
            res_value.append(0.)

        factor_value = np.nanmean(res_value[-self.__lag:])

        if np.isnan(factor_value):
            factor_value = 0.

        self._addFactorValue(factor_value)
