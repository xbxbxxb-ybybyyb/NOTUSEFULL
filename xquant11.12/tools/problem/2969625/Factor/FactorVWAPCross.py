from System.Factor import Factor
import numpy as np


class FactorVWAPCross(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__slag = self._getParameter("LagShort")
        self.__llag = self._getParameter("LagLong")

        self.__VWAP1 = self._getFactor(
            {
                "ClassName": "VWAPPrice",
                "Parameters": {
                    "Lag": self.__slag
                }
            }
        )

        self.__VWAP2 = self._getFactor(
            {
                "ClassName": "VWAPPrice",
                "Parameters": {
                    "Lag": self.__llag
                }
            }
        )

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )
        self._addIntermediate("vwap_cross", [])

    def calculate(self):
        mid_price = self.__midPrice.getLastFactorValue()
        vwap1 = self.__VWAP1.getLastFactorValue()
        vwap2 = self.__VWAP2.getLastFactorValue()
        vwap_cross = self.getIntermediate("vwap_cross")
        vwap_cross.append((vwap1 / vwap2 + mid_price / vwap1 + vwap2 / mid_price - 3) * 1e6)
        vwap_cross_sub = vwap_cross[-self.__lag:]
        factor_value = np.nanmean(vwap_cross_sub)
        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)
