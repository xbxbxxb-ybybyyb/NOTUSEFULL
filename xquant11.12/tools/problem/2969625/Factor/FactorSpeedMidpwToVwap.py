from System.Factor import Factor
import numpy as np


class FactorSpeedMidpwToVwap(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__mvlag = self._getParameter("MinVwapLag")
        self.__mlag = self._getParameter("MinLag")

        self.__midPriceW = self._getFactor(
            {
                "ClassName": "MidPriceWeighted",
                "Parameters": {
                    "Grade": 1,
                },
            }
        )
        self.__vwapPrice = self._getFactor(
            {
                "ClassName": "VWAPPrice",
                "Parameters": {
                    "Lag": self.__mvlag
                }
            }
        )

    def calculate(self):

        midPriceW = self.__midPriceW.getFactorValueList()[-self.__mlag * 20:]
        vwapPrice = self.__vwapPrice.getFactorValueList()[-self.__mlag * 20:]

        diff_price = np.subtract(midPriceW, vwapPrice)
        if np.nansum(diff_price[diff_price > 0]) > 1e-6:
            factorValue = np.nansum(diff_price[diff_price > 0]) / np.nansum(~np.isnan(diff_price)) * 1e2
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)
