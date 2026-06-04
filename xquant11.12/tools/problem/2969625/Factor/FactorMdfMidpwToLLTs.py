from System.Factor import Factor
import numpy as np


class FactorMdfMidpwToLLTs(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
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
                    "Grade": 5,
                }
            }
        )

    def calculate(self):

        llt = self.__LLTFilter.getLastFactorValue()
        midpw = self.__MidPriceW.getLastFactorValue()
        factorValue = np.subtract(midpw, llt) / llt * 1e3

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
