from System.Factor import Factor
import numpy as np


class FactorAskDisToAdjVwapM(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__ask_vwap = self._getFactor(
            {
                "ClassName": "AskVwap"
            }
        )
        self.__vwap_price = self._getFactor(
            {
                "ClassName": "VWAPPriceAdjAllDay",
            }
        )
        self._addIntermediate("ask_to_vwap", [])

    def calculate(self):
        vwap_price = self.__vwap_price.getLastFactorValue()
        ask_price_vwap = self.__ask_vwap.getLastFactorValue()
        dis_to_vwap = ask_price_vwap / vwap_price - 1 if vwap_price != 0 else 0
        dis_to_vwap_list = self.getIntermediate("ask_to_vwap")
        dis_to_vwap_list.append(dis_to_vwap)

        sub_dis_to_vwap_list = dis_to_vwap_list[-self.__lag:]
        length = len(sub_dis_to_vwap_list)
        adj_ratio = np.arange(length, 0, -1) / length

        factor_value = -np.nansum(sub_dis_to_vwap_list * adj_ratio[:length])

        self._addFactorValue(factor_value)
