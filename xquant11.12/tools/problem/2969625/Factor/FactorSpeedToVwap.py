from System.Factor import Factor
import numpy as np


class FactorSpeedToVwap(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__mvlag = self._getParameter("MinVwapLag")
        self.__mlag = self._getParameter("MinLag")

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
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

        midPrice = self.__midPrice.getFactorValueList()[-self.__mlag * 20:]
        vwapPrice = self.__vwapPrice.getFactorValueList()[-self.__mlag * 20:]

        diff_price = np.subtract(midPrice, vwapPrice)
        factorValue = np.nansum(diff_price > 0) / np.nansum(~np.isnan(diff_price))

        if np.isnan(factorValue):
            factorValue = 0.5

        self._addFactorValue(factorValue)
