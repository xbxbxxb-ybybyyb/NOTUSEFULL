from System.Factor import Factor
import numpy as np


class FactorMidpwLLTsGapMax(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__lltlag = self._getParameter("LLTLag")
        self.__LLTFilter = self._getFactor(
            {
                "ClassName": "LLTFilter",
                "Parameters": {
                    "Lag": self.__lltlag,
                    "FilterObj": "MidPrice"
                }
            }
        )
        self.__MidPriceW = self._getFactor(
            {
                "ClassName": "MidPriceWeighted",
                "Parameters": {
                    "Grade": 1,
                }
            }
        )

    def calculate(self):

        llt = self.__LLTFilter.getFactorValueList()[-self.__lag:]
        midpw = self.__MidPriceW.getFactorValueList()[-self.__lag:]
        factorValue = np.nanmax(np.subtract(midpw, llt)) / llt[-1] * 1e3

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
