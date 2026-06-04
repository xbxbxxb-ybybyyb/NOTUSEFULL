from System.Factor import Factor
import numpy as np


class FactorAskDisAll(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__ask_vwap = self._getFactor(
            {
                "ClassName": "AskVwap"
            }
        )

    def calculate(self):
        ask_price_list = self.__ask_vwap.getFactorValueList()[-self.__lag:]

        length = len(ask_price_list)
        adj_ratio = np.arange(length, 0, -1) / np.nansum(np.arange(length, 0, -1))
        ask_price_mean = np.nansum(ask_price_list * adj_ratio[:length])

        if ask_price_mean > 1e-6:
            ask_dis_all = (np.array(ask_price_list) / ask_price_mean - 1) * 1000
            factor_value = np.nanmean(ask_dis_all)
        else:
            factor_value = 0
        if np.isnan(factor_value):
            factor_value = 0
        self._addFactorValue(factor_value)
