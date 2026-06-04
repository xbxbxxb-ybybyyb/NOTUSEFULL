import numpy as np
from System.Factor import Factor


class FactorDoubleMAPrice(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__slowLag = self._getParameter("SlowLag")
        self.__fastLag = self._getParameter("FastLag")

        self.__slowMidPrice = self._getFactor(
            {
                "ClassName": "MA",
                "Parameters": {
                    "Lag": self.__slowLag,
                    "OriginalData": {
                        "ClassName": "MidPrice"
                    }
                }
            }
        )

        self.__fastMidPrice = self._getFactor(
            {
                "ClassName": "MA",
                "Parameters": {
                    "Lag": self.__fastLag,
                    "OriginalData": {
                        "ClassName": "MidPrice"
                    }
                }
            }
        )

    def calculate(self):
        slowMidPriceList = self.__slowMidPrice.getFactorValueList()
        slowMidPrice = self.__slowMidPrice.getLastFactorValue()
        fastMidPrice = self.__fastMidPrice.getLastFactorValue()

        slowMidPriceStd = np.nanstd(slowMidPriceList[-self.__slowLag:], ddof=1)

        if slowMidPrice > 0 and fastMidPrice > 0 and slowMidPriceStd > 0:
            value = np.log(fastMidPrice / slowMidPrice) / (slowMidPriceStd / slowMidPrice)
        else:
            value = 0.

        self._addFactorValue(value)

