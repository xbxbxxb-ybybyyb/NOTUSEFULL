from System.Factor import Factor
import numpy as np


class FactorAskDistanceGap(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__slevel = self._getParameter("ShortLevel")
        self.__llevel = self._getParameter("LongLevel")
        self.__ask_vwap_5 = self._getFactor(
            {
                "ClassName": "AskVwapNum",
                "Parameters": {
                    "n": self.__slevel,
                }
            }
        )
        self.__ask_vwap_10 = self._getFactor(
            {
                "ClassName": "AskVwapNum",
                "Parameters": {
                    "n": self.__llevel,
                }
            }
        )
        self._addIntermediate("askDistanceList", [])

    def calculate(self):
        ask_price_adjust_5 = self.__ask_vwap_5.getLastFactorValue()
        ask_price_adjust_10 = self.__ask_vwap_10.getLastFactorValue()
        askDistanceList = self.getIntermediate("askDistanceList")
        askDistanceList.append(ask_price_adjust_10 / ask_price_adjust_5 - 1 if ask_price_adjust_5 != 0 else 0)
        factor_value = np.nanmean(askDistanceList) * 1000
        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)
