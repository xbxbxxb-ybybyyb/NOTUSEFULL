from System.Factor import Factor
import numpy as np


class FactorAskDisToVwapCorr(Factor):
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
                "ClassName": "AvePrice",
            }
        )
        self._addIntermediate("ask_to_vwap", [])

    def calculate(self):
        vwap_price = self.__vwap_price.getLastFactorValue()
        ask_price_vwap = self.__ask_vwap.getLastFactorValue()
        dis_to_vwap = (ask_price_vwap / vwap_price - 1) * 1e3 if vwap_price > 1e-6 else 0
        dis_to_vwap_list = self.getIntermediate("ask_to_vwap")
        dis_to_vwap_list.append(dis_to_vwap)

        sub_dis_to_vwap_list = dis_to_vwap_list[-self.__lag:]
        if max(sub_dis_to_vwap_list) - min(sub_dis_to_vwap_list) > 1e-6:
            factor_value = np.corrcoef(np.array(sub_dis_to_vwap_list), np.arange(len(sub_dis_to_vwap_list)))[0][1]
        else:
            factor_value = 0.

        if np.isnan(factor_value):
            factor_value = 0
        self._addFactorValue(factor_value)
