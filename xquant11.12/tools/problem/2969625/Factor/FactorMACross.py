from System.Factor import Factor
import numpy as np


class FactorMACross(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__slag = self._getParameter("LagShort")
        self.__llag = self._getParameter("LagLong")

        self.__MA1 = self._getFactor(
            {
                "ClassName": "MAPrice",
                "Parameters": {
                    "Lag": self.__slag
                }
            }
        )

        self.__MA2 = self._getFactor(
            {
                "ClassName": "MAPrice",
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

    def calculate(self):
        mid_price = self.__midPrice.getLastFactorValue()
        ma1 = self.__MA1.getLastFactorValue()
        ma2 = self.__MA2.getLastFactorValue()
        factor_value = (ma1 / ma2 + mid_price / ma1 + ma2 / mid_price - 3) * 1e6
        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)
