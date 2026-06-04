from System.Factor import Factor
import numpy as np


class FactorAskDisMaxM(Factor):
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
        ask_price_list = [x for x in ask_price_list if not np.isnan(x) and x != 0]
        factor_value = 0.5

        length = len(ask_price_list)
        if length > 0:

            ask_price_max = np.nanmax(ask_price_list)
            ask_price_min = np.nanmin(ask_price_list)

            if ask_price_max - ask_price_min > 1e-3:
                ask_amx_value = (ask_price_max - ask_price_list[-1]) / (ask_price_max - ask_price_min)
            else:
                ask_amx_value = 1

            ask_max_list = self.getIntermediate("ask_max")
            ask_max_list.append(ask_amx_value)

            if len(ask_max_list) > 5:
                factor_value = np.nanmean(ask_max_list[-self.__lag2:])

        self._addFactorValue(factor_value)
