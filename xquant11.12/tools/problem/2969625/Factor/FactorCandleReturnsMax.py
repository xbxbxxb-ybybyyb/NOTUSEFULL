from System.Factor import Factor
import numpy as np


class FactorCandleReturnsMax(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__wd = self._getParameter("Window")

        self.__midPriceWeighted = self._getFactor(
            {
                "ClassName": "MidPriceWeighted",
                "Parameters": {
                    "Grade": 1
                }
            }
        )

    def calculate(self):

        midpw = self.__midPriceWeighted.getFactorValueList()[-self.__lag:][::-1]
        n = len(midpw) // self.__wd if len(midpw) % self.__wd == 0 else len(midpw) // self.__wd + 1
        midpw_itv = [midpw[i * self.__wd: (i + 1) * self.__wd] for i in range(n)]
        crtns = [(each[0] / each[-1] - 1) for each in midpw_itv]
        factorValue = np.nanmax(crtns) * 100

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
