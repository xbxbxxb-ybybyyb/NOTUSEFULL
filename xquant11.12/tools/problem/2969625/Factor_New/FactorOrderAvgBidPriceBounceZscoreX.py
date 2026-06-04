import numpy as np
from System.Factor import Factor


class FactorOrderAvgBidPriceBounceZscoreX(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__sLag = self._getParameter("sLag")

    def calculate(self):
        avgPriceArray = self._getLastNTickData("AvgBidPrice", self.__lag)
        minPrice = self._getLastTickData("MinPrice")
        if len(avgPriceArray) < min(5, self.__sLag):
            factorValue = 0.
        else:
            priceBase = np.minimum.accumulate(avgPriceArray)
            priceBase[priceBase < 1e-4] = minPrice
            bounce = (avgPriceArray / priceBase - 1.) * 1000
            bounceStd = np.nanstd(bounce)
            if bounceStd > 1e-6:
                factorValue = (bounce[-1] - np.nanmean(bounce[-self.__sLag:])) / bounceStd
            else:
                lastFactorValue = self.getLastFactorValue()
                if lastFactorValue is not None:
                    factorValue = lastFactorValue
                else:
                    factorValue = 0.

        self._addFactorValue(factorValue)



