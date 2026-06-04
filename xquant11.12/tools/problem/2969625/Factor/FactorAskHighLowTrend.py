from System.Factor import Factor
import numpy as np


class FactorAskHighLowTrend(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__ask_vwap = self._getFactor(
            {
                "ClassName": "AskVwap"
            }
        )
        self._addIntermediate("high_to_low", [])

    def calculate(self):
        ask_price_list = self.__ask_vwap.getFactorValueList()[-self.__lag:]

        ask_high = np.nanmax(ask_price_list)
        ask_low = np.nanmin(ask_price_list)
        high_to_low = ask_high / ask_low - 1 if ask_low > 1e-6 else 0

        high_to_low_list = self.getIntermediate("high_to_low")
        high_to_low_list.append(high_to_low)
        factor_value = np.nanmean(high_to_low_list[-self.__lag:]) * 1000

        if np.isnan(factor_value):
            factor_value = 0
        self._addFactorValue(factor_value)
