import numpy as np
from System.Factor import Factor

class FactorMidAvgToLastPrice(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.__lag = self._getParameter("Lag")

        self.__midPrice = self._getFactor(

            {
                "ClassName": "MidPrice"
            }
        )

    def calculate(self):
        lastPrice = self._getLastTickData("LastPrice")
        midPriceList = self.__midPrice.getFactorValueList()[-self.__lag:]
        midAvgPrice = np.nanmean(midPriceList)
        factorValue = - (lastPrice / midAvgPrice - 1) * 1000 if midAvgPrice > 1e-4 else 0

        self._addFactorValue(factorValue)